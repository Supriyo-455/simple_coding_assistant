import unittest
import os
import tempfile

from main import Assistant

class TestToolParser(unittest.TestCase):

    def setUp(self):
        self.assistant = Assistant()

    def test_write_file(self):
        temp_file_path = os.path.join(tempfile.gettempdir(), "test_write_file.txt")
        command = f'write_file("{temp_file_path}", "hello world")'
        result = self.assistant.execute_tool(command)
        self.assertEqual(result, f"Successfully wrote to {temp_file_path}.")
        with open(temp_file_path, "r") as f:
            content = f.read()
        self.assertEqual(content, "hello world")
        os.remove(temp_file_path)

    def test_run_shell_command(self):
        command = 'run_shell_command("echo hello")'
        result = self.assistant.execute_tool(command)
        self.assertIn("STDOUT:\nhello\n", result)
        self.assertIn("STDERR:\n(empty)", result)

    def test_command_with_quotes_in_string(self):
        temp_file_path = os.path.join(tempfile.gettempdir(), "test_quotes.txt")
        command = f'write_file("{temp_file_path}", "this is a \"test\" with quotes")'
        result = self.assistant.execute_tool(command)
        self.assertEqual(result, f"Successfully wrote to {temp_file_path}.")
        with open(temp_file_path, "r") as f:
            content = f.read()
        self.assertEqual(content, 'this is a "test" with quotes')
        os.remove(temp_file_path)

    def test_finish_tool_with_message(self):
        command = 'finish("Task completed successfully.")'
        result = self.assistant.execute_tool(command)
        self.assertEqual(result, "Task finished with message: Task completed successfully.")

    def test_finish_tool_without_message(self):
        command = 'finish()'
        result = self.assistant.execute_tool(command)
        self.assertEqual(result, "Task finished with no specific message.")

    def test_execute_tool_with_backticks(self):
        command_with_backticks = '```run_shell_command("echo test")```'
        result = self.assistant.execute_tool(command_with_backticks)
        self.assertIn("STDOUT:\ntest\n", result)
        self.assertIn("STDERR:\n(empty)", result)

    def test_write_file_relative_path(self):
        command = 'write_file("relative_path.txt", "some content")'
        result = self.assistant.execute_tool(command)
        self.assertIn("Error: write_file requires an absolute path", result)

    def test_read_file_relative_path(self):
        command = 'read_file("relative_path.txt")'
        result = self.assistant.execute_tool(command)
        self.assertIn("Error: read_file requires an absolute path", result)

if __name__ == '__main__':
    unittest.main()