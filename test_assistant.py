import unittest
import os
import tempfile
from unittest.mock import patch, MagicMock
import subprocess

from main import Assistant

class TestAssistant(unittest.TestCase):

    def setUp(self):
        self.assistant = Assistant()
        self.temp_dir = tempfile.mkdtemp()
        self.assistant.output_callback = lambda x: None # Suppress print output during tests

    def tearDown(self):
        # Clean up the temporary directory and its contents
        for root, dirs, files in os.walk(self.temp_dir, topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
            for name in dirs:
                os.rmdir(os.path.join(root, name))
        os.rmdir(self.temp_dir)

    # Test cases for write_file
    def test_write_file_success(self):
        file_path = os.path.join(self.temp_dir, "test_file.txt")
        content = "Hello, world!"
        result = self.assistant.write_file(file_path, content)
        self.assertEqual(result, f"Successfully wrote to {file_path}.")
        with open(file_path, "r") as f:
            self.assertEqual(f.read(), content)

    def test_write_file_empty_content(self):
        file_path = os.path.join(self.temp_dir, "empty_file.txt")
        content = ""
        result = self.assistant.write_file(file_path, content)
        self.assertEqual(result, f"Successfully wrote to {file_path}.")
        with open(file_path, "r") as f:
            self.assertEqual(f.read(), content)

    def test_write_file_special_characters(self):
        file_path = os.path.join(self.temp_dir, "special_chars.txt")
        content = "!@#$%^&*()_+{{}}[]|;:'\",.<>/?`~"
        result = self.assistant.write_file(file_path, content)
        self.assertEqual(result, f"Successfully wrote to {file_path}.")
        with open(file_path, "r") as f:
            self.assertEqual(f.read(), content)

    def test_write_file_overwrite_existing(self):
        file_path = os.path.join(self.temp_dir, "overwrite.txt")
        with open(file_path, "w") as f:
            f.write("original content")
        new_content = "new content"
        result = self.assistant.write_file(file_path, new_content)
        self.assertEqual(result, f"Successfully wrote to {file_path}.")
        with open(file_path, "r") as f:
            self.assertEqual(f.read(), new_content)

    def test_write_file_non_existent_directory(self):
        file_path = os.path.join(self.temp_dir, "non_existent_dir", "file.txt")
        content = "content"
        result = self.assistant.write_file(file_path, content)
        self.assertIn("Error writing to file:", result)

    # Test cases for read_file
    def test_read_file_success(self):
        file_path = os.path.join(self.temp_dir, "read_test.txt")
        content = "This is content to be read."
        with open(file_path, "w") as f:
            f.write(content)
        result = self.assistant.read_file(file_path)
        self.assertEqual(result, content)

    def test_read_file_empty(self):
        file_path = os.path.join(self.temp_dir, "read_empty.txt")
        with open(file_path, "w") as f:
            f.write("")
        result = self.assistant.read_file(file_path)
        self.assertEqual(result, "")

    def test_read_file_non_existent(self):
        file_path = os.path.join(self.temp_dir, "non_existent_read.txt")
        result = self.assistant.read_file(file_path)
        self.assertIn("Error reading file:", result)

    # Test cases for run_shell_command
    @patch('subprocess.run')
    def test_run_shell_command_success(self, mock_subprocess_run):
        mock_subprocess_run.return_value = MagicMock(stdout="hello", stderr="", returncode=0)
        command = "echo hello"
        result = self.assistant.run_shell_command(command)
        self.assertIn("STDOUT:\nhello", result)
        self.assertIn("STDERR:\n(empty)", result)
        mock_subprocess_run.assert_called_once_with(command, shell=True, check=True, capture_output=True, text=True)

    @patch('subprocess.run')
    def test_run_shell_command_stderr(self, mock_subprocess_run):
        mock_subprocess_run.return_value = MagicMock(stdout="", stderr="error message", returncode=0)
        command = "ls non_existent_file"
        result = self.assistant.run_shell_command(command)
        self.assertIn("STDOUT:\n(empty)", result)
        self.assertIn("STDERR:\nerror message", result)

    @patch('subprocess.run')
    def test_run_shell_command_failure(self, mock_subprocess_run):
        mock_subprocess_run.side_effect = subprocess.CalledProcessError(returncode=1, cmd="test_cmd", stderr="command failed")
        command = "exit 1"
        result = self.assistant.run_shell_command(command)
        self.assertIn("Error executing command:", result)
        self.assertIn("STDERR:\ncommand failed", result)

    # Test cases for google_search (mocked)
    @patch('main.search') # Patch the search function from googlesearch
    def test_google_search_success(self, mock_search):
        mock_search.return_value = ["http://example.com", "http://test.org"]
        query = "test query"
        result = self.assistant.google_search(query)
        self.assertIn("http://example.com", result)
        self.assertIn("http://test.org", result)
        mock_search.assert_called_once_with(query, num_results=5)

    @patch('main.search')
    def test_google_search_no_results(self, mock_search):
        mock_search.return_value = []
        query = "nonexistent query"
        result = self.assistant.google_search(query)
        self.assertIn("No search results found for 'nonexistent query'.", result)

    @patch('main.search')
    def test_google_search_error(self, mock_search):
        mock_search.side_effect = Exception("Network error")
        query = "error query"
        result = self.assistant.google_search(query)
        self.assertIn("Error during Google search: Network error", result)

    # Test cases for finish
    def test_finish_with_message(self):
        self.assistant._is_running = True
        result = self.assistant.execute_tool('finish("Task completed successfully.")')
        self.assertEqual(result, "Task finished with message: Task completed successfully.")
        self.assertFalse(self.assistant._is_running)

    def test_finish_without_message(self):
        self.assistant._is_running = True
        result = self.assistant.execute_tool('finish()')
        self.assertEqual(result, "Task finished with no specific message.")
        self.assertFalse(self.assistant._is_running)

    # Integration tests (simple scenarios)
    def test_write_and_read_integration(self):
        file_path = os.path.join(self.temp_dir, "integration_test.txt")
        content = "Integration test content."
        
        # Write the file
        write_command = f'write_file("{file_path}", "{content}")'
        write_result = self.assistant.execute_tool(write_command)
        self.assertEqual(write_result, f"Successfully wrote to {file_path}.")

        # Read the file
        read_command = f'read_file("{file_path}")'
        read_result = self.assistant.execute_tool(read_command)
        self.assertEqual(read_result, content)

    def test_shell_command_and_read_integration(self):
        file_path = os.path.join(self.temp_dir, "shell_output.txt")
        command_to_run = f'echo Hello from shell > {file_path}'

        # Run shell command to write to file
        shell_command = f'run_shell_command("{command_to_run}")'
        shell_result = self.assistant.execute_tool(shell_command)
        self.assertIn("STDOUT:\n(empty)", shell_result) # echo usually doesn't output to stdout

        # Read the file
        read_command = f'read_file("{file_path}")'
        read_result = self.assistant.execute_tool(read_command)
        self.assertEqual(read_result.strip(), "Hello from shell") # strip to handle potential newline differences

if __name__ == '__main__':
    unittest.main()
