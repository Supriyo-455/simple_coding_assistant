import os
import subprocess
import requests
import json
import ast
import sys # Import sys module
from googlesearch import search

# The URL for the LM Studio API endpoint.
# Make sure your LM Studio server is running.
LM_STUDIO_URL = os.getenv('LM_STUDIO_URL', 'http://localhost:1234/v1/chat/completions')

class Assistant:
    """
    An autonomous AI assistant that can perform development tasks.
    """

    def __init__(self):
        """
        Initializes the assistant.
        """
        self.history = []
        self.output_callback = print # Default to printing to console
        self._is_running = False
        self.os_name = sys.platform # Store the OS name

    def set_output_callback(self, callback):
        """
        Sets a callback function to handle output messages.
        """
        self.output_callback = callback

    def stop(self):
        """
        Stops the assistant's execution loop.
        """
        self._is_running = False

    def get_llm_response(self, prompt):
        """
        Gets a response from the local LLM.
        The prompt should ask the LLM to choose the next action to take.
        """
        self.history.append({"role": "user", "content": prompt})
        
        headers = {'Content-Type': 'application/json'}
        data = {
            "messages": self.history,
            "temperature": 0.5,
        }
        
        try:
            response = requests.post(LM_STUDIO_URL, headers=headers, json=data)
            response.raise_for_status()  # Raise an exception for bad status codes
            response_json = response.json()
            llm_content = response_json['choices'][0]['message']['content']
            self.history.append({"role": "assistant", "content": llm_content})
            return llm_content
        except requests.exceptions.RequestException as e:
            self.output_callback(f"Error connecting to LM Studio: {e}")
            return None

    def execute_tool(self, tool_call_str):
        """
        Parses and executes a tool call string from the LLM.
        This implementation is designed to be more robust against syntax errors.
        """
        # Remove triple backticks if present
        if tool_call_str.startswith('```python\n') and tool_call_str.endswith('```'):
            tool_call_str = tool_call_str[3:-3].strip()

        # Remove leading "python " if present (LLM sometimes adds this unnecessarily)
        if tool_call_str.startswith('python\n'):
            tool_call_str = tool_call_str[len('python\n'):].strip()

        try:
            tool_name = ""
            args_str = ""
            if '(' in tool_call_str and tool_call_str.endswith(')'):
                tool_name = tool_call_str.split('(', 1)[0]
                args_str = tool_call_str.split('(', 1)[1][:-1] # Content between the first '(' and the last ')'
            else:
                tool_name = tool_call_str.strip()
                args_str = ""

            # This is a more robust way to handle arguments, especially with complex strings.
            # It splits the arguments by commas, but only if the comma is not inside a string.
            args = []
            if args_str:
                in_string = False
                current_arg = ""
                for char in args_str:
                    if char == '"' and not in_string:
                        in_string = True
                    elif char == '"' and in_string:
                        in_string = False
                    
                    if char == ',' and not in_string:
                        args.append(current_arg.strip())
                        current_arg = ""
                    else:
                        current_arg += char
                args.append(current_arg.strip())

            # Remove quotes from the arguments
            args = [arg.strip('"') for arg in args]

            self.output_callback(f"Executing tool: {tool_name} with args: {args}")

            self.output_callback(f"Executing tool: {tool_name} with args: {args}")

            # Call the corresponding tool method
            if hasattr(self, tool_name) and callable(getattr(self, tool_name)):
                if tool_name == 'write_file':
                    if len(args) != 2:
                        return f"Error: write_file requires 2 arguments (path, content), but received {len(args)}."
                elif tool_name == 'read_file':
                    if len(args) != 1:
                        return f"Error: read_file requires 1 argument (path), but received {len(args)}."
                return getattr(self, tool_name)(*args)
            elif tool_name == 'finish':
                self._is_running = False
                # Handle finish tool with or without arguments
                if not args or args[0] == '': # Check if args is empty or contains an empty string
                    return "Task finished with no specific message."
                else:
                    return f"Task finished with message: {args[0]}"
            else:
                return f"Unknown tool: {tool_name}"

        except Exception as e:
            return f"Error parsing or executing tool: {e}"

    # --- Tool Implementations ---

    def write_file(self, path, content):
        """Writes content to a file."""
        if not os.path.isabs(path):
            return f"Error: write_file requires an absolute path, but received '{path}'."
        try:
            with open(path, 'w') as f:
                f.write(content)
            return f"Successfully wrote to {path}."
        except Exception as e:
            return f"Error writing to file: {e}"

    def read_file(self, path):
        """Reads content from a file."""
        if not os.path.isabs(path):
            return f"Error: read_file requires an absolute path, but received '{path}'."
        try:
            with open(path, 'r') as f:
                return f.read()
        except Exception as e:
            return f"Error reading file: {e}"

    def run_shell_command(self, command):
        """
        Executes a shell command.
        """
        try:
            result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
            stdout_output = result.stdout if result.stdout else "(empty)"
            stderr_output = result.stderr if result.stderr else "(empty)"
            return f"STDOUT:\n{stdout_output}\nSTDERR:\n{stderr_output}"
        except subprocess.CalledProcessError as e:
            stdout_output = e.stdout if e.stdout else "(empty)"
            stderr_output = e.stderr if e.stderr else "(empty)"
            return f"Error executing command: {e}\nSTDOUT:\n{stdout_output}\nSTDERR:\n{stderr_output}"

    def google_search(self, query):
        """Performs a Google search using the googlesearch-python library."""
        try:
            # Perform the search and get the first 5 results
            search_results = list(search(query, num_results=5))
            if search_results:
                results_str = "\n".join(search_results)
                self.output_callback(f"Search results for '{query}':\n{results_str}")
                return results_str
            else:
                self.output_callback(f"No search results found for '{query}'.")
                return f"No search results found for '{query}'."
        except Exception as e:
            self.output_callback(f"Error during Google search: {e}")
            return f"Error during Google search: {e}"

    def run(self, goal):
        """
        Runs the assistant to achieve a given goal.
        """
        self._is_running = True
        system_prompt = f"""You are an autonomous AI assistant. Your goal is to achieve the following: '{goal}'.
You are currently running on a {self.os_name} operating system.
You will interact by receiving observations (results of tool executions) and responding with a single tool call.
Based on the goal and the observation, you must decide which single tool to execute next.
Do not ask for clarification. Make your best judgment and execute a command.

Your available tools are:
- `finish("a final message to the user")`: Use this tool when you believe the goal has been fully achieved, or to respond to simple greetings/questions. This tool is a direct function call and **MUST NOT** be prefixed with `python` or wrapped in `run_shell_command()`.
  Example: `finish("Hello! How can I help you today?")`
- `write_file("your absolute path to file", "content for the file")`: Creates or overwrites a file. **ALWAYS use absolute paths.** This tool requires exactly two arguments: the absolute path and the content.
- `read_file("your absolute path to file")`: Reads the full content of a file. **ALWAYS use absolute paths.** This tool requires exactly one argument: the absolute path.
- `run_shell_command("your shell command as a single string")`: Executes a command in the shell. **IMPORTANT: The entire command, including any `python` calls, must be a single string argument to `run_shell_command()`.
  Example: `run_shell_command("python -m pip install requests")`
  Example: `run_shell_command("ls -l")`
- `google_search("your search query")`: Searches the web for information.

Call tools with their correct names only otherwise the magic will not work.
Try not to use unknown tools. Soecially python infront of tools command!!

**IMPORTANT:**
- For simple greetings or questions (e.g., "hello", "hii", "what is your name?"), you MUST use the `finish` tool immediately to provide a direct response. Example: `finish("Hello! How can I help you today?")`
- For complex tasks, carefully analyze the `Observation` from previous tool executions. Do not repeat actions that have already been performed or have failed. Plan your next step logically based on the *current* state and the overall goal.
- When using `run_shell_command` for installations (e.g., `pip install`), always check the `Observation` for success or failure. If a module is already installed or the installation fails, do NOT attempt to install it again. Instead, proceed with the next logical step or use `finish` if the task cannot be completed.
"""
        
        self.history = [{"role": "system", "content": system_prompt}]
        
        last_result = "No commands have been executed yet. This is the beginning of the task."

        while self._is_running:
            prompt = f"""Observation:
```
{last_result}
```
Based on your goal, what is the next single tool call you should execute? Respond with only the tool call."""
            
            tool_call = self.get_llm_response(prompt)
            
            if tool_call is None:
                self.output_callback("Could not get a response from the LLM. Aborting.")
                break

            # Remove triple backticks if present (already handled in execute_tool, but for display consistency)
            if tool_call.startswith('```') and tool_call.endswith('```'):
                tool_call = tool_call[3:-3].strip()

            # Remove leading "python " if present (for display consistency)
            if tool_call.startswith('python '):
                tool_call = tool_call[len('python '):].strip()

            self.output_callback(f"\n--- LLM decided to run ---\n{tool_call}\n---------------------------\n")
            
            last_result = self.execute_tool(tool_call)

            self.output_callback(f"\n--- Tool execution result ---\n{last_result}\n-----------------------------")


if __name__ == '__main__':
    # This allows the assistant to be run from the command line
    # or imported and used by another script (like the GUI).
    print("Welcome to CodeGuru (CLI Mode)!")
    print("For the GUI, please run 'python gui.py'")
    user_goal = input("Please state your development goal: ")
    assistant = Assistant()
    assistant.run(user_goal)