import os
import subprocess
import requests
import json
import sys # Import sys module
from googlesearch import search
import Levenshtein
from bs4 import BeautifulSoup

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

    VALID_TOOLS = ["write_file", "read_file", "run_shell_command", "google_search", "scrape_website", "finish", "list_files"]

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
            self.history.append(response_json['choices'][0]['message'])
            llm_content = response_json['choices'][0]['message']['content']

            # Remove <think> blocks
            while "<think>" in llm_content and "</think>" in llm_content:
                start_index = llm_content.find("<think>")
                end_index = llm_content.find("</think>") + len("</think>")
                llm_content = llm_content[:start_index] + llm_content[end_index:]

            return llm_content.strip()
        except requests.exceptions.RequestException as e:
            self.output_callback(f"Error connecting to LM Studio: {e}")
            return None

    def execute_tool(self, tool_json):
        """
        Parses and executes a tool call from the LLM in JSON format.
        """
        try:
            tool_data = json.loads(tool_json)
            tool_name = tool_data.get("tool")
            tool_args = tool_data.get("args", {})

            # Fuzzy match the tool name to handle minor typos
            if tool_name not in self.VALID_TOOLS:
                closest_tool = find_closest_string(tool_name, self.VALID_TOOLS)
                # Only use the closest match if the Levenshtein distance is small (e.g., <= 3)
                if closest_tool and Levenshtein.distance(tool_name, closest_tool) <= 3:
                    self.output_callback(f"Warning: Tool '{tool_name}' not found. Using closest match '{closest_tool}'.")
                    tool_name = closest_tool

            if tool_name not in self.VALID_TOOLS:
                return f"Error: The tool '{tool_name}' is not valid. Please choose from {self.VALID_TOOLS}"

            self.output_callback(f"Executing tool: {tool_name} with args: {tool_args}")

            # Dynamically call the tool method
            tool_method = getattr(self, tool_name, None)
            if tool_method:
                return tool_method(**tool_args)
            else:
                return f"Error: The tool '{tool_name}' is not implemented."

        except json.JSONDecodeError as e:
            return f"Error: Invalid JSON from LLM. The response must be a valid JSON object. Error: {e}"
        except Exception as e:
            return f"Error executing tool: {e}"

    # --- Tool Implementations ---

    def write_file(self, path, content):
        """Writes content to a file. Paths are relative to the current working directory."""
        safe_path = os.path.abspath(path)
        if not safe_path.startswith(os.getcwd()):
            return "Error: Path is outside the current working directory."
        try:
            # Ensure the directory exists
            os.makedirs(os.path.dirname(safe_path), exist_ok=True)
            with open(safe_path, 'w') as f:
                f.write(content)
            return f"Successfully wrote to {safe_path}."
        except Exception as e:
            return f"Error writing to file: {e}"

    def read_file(self, path):
        """Reads content from a file. Paths are relative to the current working directory."""
        safe_path = os.path.abspath(path)
        if not safe_path.startswith(os.getcwd()):
            return "Error: Path is outside the current working directory."
        try:
            with open(safe_path, 'r') as f:
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

    def scrape_website(self, url):
        """Scrapes the text content of a website."""
        try:
            response = requests.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            return soup.get_text()
        except Exception as e:
            return f"Error scraping website: {e}"

    def list_files(self, path="."):
        """Lists files and directories at a given path."""
        try:
            # For security, ensure path is within the current working directory.
            # This is a simple check, a more robust implementation would be needed for production.
            safe_path = os.path.abspath(path)
            if not safe_path.startswith(os.getcwd()):
                return "Error: Path is outside the current working directory."

            files = os.listdir(safe_path)
            return f"Files in '{safe_path}':\n" + "\n".join(files)
        except FileNotFoundError:
            return f"Error: Directory not found at '{path}'"
        except Exception as e:
            return f"Error listing files: {e}"

    def finish(self, message=""):
        """
        Stops the assistant's execution loop and returns a final message.
        """
        self.stop()
        if not message:
            return "Task finished with no specific message."
        else:
            return f"Task finished with message: {message}"

    def run(self, goal, files=None):
        """
        Runs the assistant to achieve a given goal.
        """
        self._is_running = True

        file_list_prompt = ""
        if files:
            file_list_prompt = "The user has provided the following files. Use the `read_file` tool to access their content when needed:\n" + "\n".join(files)

        system_prompt = f"""
You are a helpful AI assistant. Your goal is to help the user with their development task: {goal}

Information about the system you are currently running on ->
  - all functions from posix or nt, e.g. unlink, stat, etc.
  - os.path - {os.path}
  - os.name - {os.name}
  - os.curdir - {os.curdir}
  - os.pardir - {os.pardir}
  - os.sep - {os.sep}
  - os.extsep - {os.extsep}
  - os.altsep - {os.altsep}
  - os.pathsep - {os.pathsep}
  - os.linesep - {os.linesep}


{file_list_prompt}

To achieve this, you have access to a set of tools. You must respond with a single JSON object that specifies the tool to use and the arguments to pass to it. Your response must be ONLY the JSON object, with no other text before or after.

Available Tools:

- `finish(message: str)`: Call this when the task is complete. The message should summarize the result.
- `run_shell_command(command: str)`: Execute a shell command.
- `list_files(path: str)`: List files in a directory. Defaults to the current directory (`.`).
- `google_search(query: str)`: Perform a Google search.
- `scrape_website(url: str)`: Scrape the text content of a website.
- `write_file(path: str, content: str)`: Write content to a file. The path is relative to the current working directory.
- `read_file(path: str)`: Read the content of a file. The path is relative to the current working directory.

Example of a valid response:
{{"tool": "run_shell_command", "args": {{"command": "ls -l"}}}}

Example of another valid response:
{{"tool": "finish", "args": {{"message": "I have successfully listed the files."}}}}

Now, analyze the goal and the latest observation, and provide the next tool call as a JSON object.
"""
        
        self.history = [{"role": "system", "content": system_prompt}]
        
        last_result = "No commands have been executed yet. This is the beginning of the task."

        while self._is_running:
            prompt = f"""
                        ---OBSERVATION START---
                            {last_result}
                        ---OBSERVATION END---
                    Analyze the result above. Based on that information and your main goal ({goal}), determine the absolute next single tool call to execute. If the previous result was an error, you MUST try to fix it or use a different tool. Do not repeat failed commands."""
            
            tool_call = self.get_llm_response(prompt)
            
            if tool_call is None:
                self.output_callback("Could not get a response from the LLM. Aborting.")
                break

            self.output_callback(f"\n--- LLM decided to run ---\n{tool_call}\n---------------------------")
            
            last_result = self.execute_tool(tool_call)

            self.output_callback(f"\n--- Tool execution result ---\n{last_result}\n-----------------------------")


if __name__ == '__main__':
    # This allows the assistant to be run from the command line
    # or imported and used by another script (like the GUI).
    print("Welcome to CodeGuru (CLI Mode)!")
    print("For the GUI, please run 'python gui.py'")
    user_goal = input("Please state your development goal: ")
    assistant = Assistant()
    assistant.run(user_goal, files=[])
