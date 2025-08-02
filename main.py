import os
import subprocess
import requests
import json
import ast

# The URL for the LM Studio API endpoint.
# Make sure your LM Studio server is running.
LM_STUDIO_URL = 'http://localhost:1234/v1/chat/completions'

class Assistant:
    """
    An autonomous AI assistant that can perform development tasks.
    """

    def __init__(self):
        """
        Initializes the assistant.
        """
        self.history = []

    def get_llm_response(self, prompt):
        """
        Gets a response from the local LLM.
        The prompt should ask the LLM to choose the next action to take.
        """
        self.history.append({"role": "user", "content": prompt})
        
        headers = {'Content-Type': 'application/json'}
        data = {
            "messages": self.history,
            "temperature": 0.7,
        }
        
        try:
            response = requests.post(LM_STUDIO_URL, headers=headers, json=data)
            response.raise_for_status()  # Raise an exception for bad status codes
            response_json = response.json()
            llm_content = response_json['choices'][0]['message']['content']
            self.history.append({"role": "assistant", "content": llm_content})
            return llm_content
        except requests.exceptions.RequestException as e:
            print(f"Error connecting to LM Studio: {e}")
            return None

    def execute_tool(self, tool_call_str):
        """
        Parses and executes a tool call string from the LLM.
        This implementation is designed to be more robust against syntax errors.
        """
        try:
            # Extract the tool name and the arguments string
            tool_name = tool_call_str.split('(', 1)[0]
            args_str = tool_call_str.split('(', 1)[1][:-1] # Content between the first '(' and the last ')'

            # This is a more robust way to handle arguments, especially with complex strings.
            # It splits the arguments by commas, but only if the comma is not inside a string.
            args = []
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

            print(f"Executing tool: {tool_name} with args: {args}")

            # Call the corresponding tool method
            if hasattr(self, tool_name) and callable(getattr(self, tool_name)):
                return getattr(self, tool_name)(*args)
            elif tool_name == 'finish':
                 return f"Task finished with message: {args[0]}"
            else:
                return f"Unknown tool: {tool_name}"

        except Exception as e:
            return f"Error parsing or executing tool: {e}"

    # --- Tool Implementations ---

    def write_file(self, path, content):
        """Writes content to a file."""
        try:
            with open(path, 'w') as f:
                f.write(content)
            return f"Successfully wrote to {path}."
        except Exception as e:
            return f"Error writing to file: {e}"

    def read_file(self, path):
        """Reads content from a file."""
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
            return f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
        except subprocess.CalledProcessError as e:
            return f"Error executing command: {e}\nSTDOUT:\n{e.stdout}\nSTDERR:\n{e.stderr}"

    def google_search(self, query):
        """Performs a Google search (placeholder)."""
        # In a real scenario, this would use a library like `googlesearch-python`
        # or an API like the Google Custom Search JSON API.
        print(f"--- Pretending to search for: {query} ---")
        return "Search results for '{query}' would appear here. This is a placeholder."

    def run(self, goal):
        """
        Runs the assistant to achieve a given goal.
        """
        system_prompt = f"""You are an autonomous AI assistant. Your goal is to achieve the following: '{goal}'.
You will be given the result of the previous command's execution.
Based on the goal and the previous result, you must decide which single tool to execute next.
Do not ask for clarification. Make your best judgment and execute a command.
Your available tools are:
- `write_file("path/to/file.ext", "content for the file")`: Creates or overwrites a file.
- `read_file("path/to/file.ext")`: Reads the full content of a file.
- `run_shell_command("your shell command")`: Executes a command in the shell.
- `google_search("your search query")`: Searches the web for information.
- `finish("a final message to the user")`: Use this tool when you believe the goal has been fully achieved.

You must respond with ONLY the single tool call you want to execute. Do not add any other text or explanation.
For example:
write_file("main.py", "print('Hello, World!')")
"""
        
        self.history = [{"role": "system", "content": system_prompt}]
        
        last_result = "No commands have been executed yet. This is the beginning of the task."

        while True:
            prompt = f"Previous command result:\n```\n{last_result}\n```\nBased on your goal, what is the next single tool call you should execute? Respond with only the tool call."
            
            tool_call = self.get_llm_response(prompt)
            
            if tool_call is None:
                print("Could not get a response from the LLM. Aborting.")
                break

            print(f"\n--- LLM decided to run ---\n{tool_call}\n---------------------------\n")
            
            if tool_call.startswith("finish("):
                print(f"Goal achieved: {tool_call}")
                break

            last_result = self.execute_tool(tool_call)

            print(f"\n--- Tool execution result ---\n{last_result}\n-----------------------------")


if __name__ == '__main__':
    print("Welcome to the Autonomous AI Assistant!")
    user_goal = input("Please state your development goal: ")
    assistant = Assistant()
    assistant.run(user_goal)
