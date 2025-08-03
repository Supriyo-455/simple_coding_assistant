import os
import subprocess
import requests
import json
import ast
import sys # Import sys module
from googlesearch import search
import Levenshtein

def find_closest_string(target, candidates):
    """
    Finds the closest string to a target from a list of candidates.
    """
    if not candidates:
        return None
        
    # Find the string with the minimum Levenshtein distance
    closest_string = min(candidates, key=lambda s: Levenshtein.distance(target, s))
    
    return closest_string

# The URL for the LM Studio API endpoint.
# Make sure your LM Studio server is running.
LM_STUDIO_URL = os.getenv('LM_STUDIO_URL', 'http://localhost:1234/v1/chat/completions')

class Assistant:
    """
    An autonomous AI assistant that can perform development tasks.
    """

    VALID_TOOLS = ["write_file", "read_file", "run_shell_command", "google_search", "finish"]

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
            self.history.append({"role": "assistant", "response": response_json})
            llm_content = response_json['choices'][0]['message']['content']
            return llm_content
        except requests.exceptions.RequestException as e:
            self.output_callback(f"Error connecting to LM Studio: {e}")
            return None

    def execute_tool(self, tool_call_str):
        """
        Parses and executes a tool call string from the LLM.
        This implementation is designed to be more robust against syntax errors.
        """
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

            # Find the actual tool method using exact match from VALID_TOOLS
            tool_name = find_closest_string(tool_name, self.VALID_TOOLS)

            # Call the corresponding tool method
            if hasattr(self, tool_name) and callable(getattr(self, tool_name)):
                if tool_name == 'write_file':
                    if len(args) != 2:
                        return f"Error: write_file requires 2 arguments (path, content), but received {len(args)}."
                elif tool_name == 'read_file':
                    if len(args) != 1:
                        return f"Error: read_file requires 1 argument (path), but received {len(args)}."
                elif tool_name == 'run_shell_command':
                    if len(args) != 1:
                        return f"Error: run_shell_command requires 1 argument (command), but received {len(args)}."
                elif tool_name == 'google_search':
                    if len(args) != 1:
                        return f"Error: google_search requires 1 argument (query), but received {len(args)}."
                elif tool_name == 'finish':
                    if len(args) > 1:
                        return f"Error: finish requires at most 1 argument (message), but received {len(args)}."
                else:
                    return f"Unknown tool: {tool_name}"
                return getattr(self, tool_name)(*args)

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

    def finish(self, message=""):
        """
        Stops the assistant's execution loop and returns a final message.
        """
        self.stop()
        if not message:
            return "Task finished with no specific message."
        else:
            return f"Task finished with message: {message}"

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
- `write_file("write to a file according to your needs; or create one if its not there", "content for the file")`: Creates or overwrites a file. **ALWAYS use absolute paths.** This tool requires exactly two arguments: the absolute path and the content.
- `read_file("read a file according to your needs")`: Reads the full content of a file. **ALWAYS use absolute paths.** This tool requires exactly one argument: the absolute path.
- `run_shell_command("run the command you want to run")`: Executes a command in the shell. **If you are facing any errors searching in google will get you some commands that can fix your problem, so try to use this tool its very useful**
- `google_search("search the thing you want to get info about")`: Searches the web for information.

**IMPORTANT:**
- For simple greetings or questions (e.g., "hello", "hii", "what is your name?"), you MUST use the `finish` tool immediately to provide a direct response. Example: `finish("Hello! How can I help you today?")`
- For complex tasks, carefully analyze the `Observation` from previous tool executions. Pay close attention to success messages, error messages, and any output from shell commands or file operations. Do not repeat actions that have already been performed or have failed. Plan your next step logically based on the *current* state and the overall goal.
- When using `run_shell_command` for installations (e.g., `pip install`), always check the `Observation` for success or failure. If a module is already installed or the installation fails, do NOT attempt to install it again. Instead, proceed with the next logical step or use `finish` if the task cannot be completed.
- Your response MUST be a single tool call, and nothing else. Do NOT include any conversational text, explanations, or markdown formatting (like ```python) around the tool call. Just the tool call itself.
- The `Observation` will be provided to you within `---OBSERVATION START---` and `---OBSERVATION END---` delimiters. Analyze its content carefully.
"""
        
        self.history = [{"role": "system", "content": system_prompt}]
        
        last_result = "No commands have been executed yet. This is the beginning of the task."

        while self._is_running:
            prompt = f"""
                        ---OBSERVATION START---
                            {last_result}
                        ---OBSERVATION END---
                    Based on your goal, what is the next single tool call you should execute? Respond with only the tool call."""
            
            tool_call = self.get_llm_response(prompt)
            
            if tool_call is None:
                self.output_callback("Could not get a response from the LLM. Aborting.")
                break

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