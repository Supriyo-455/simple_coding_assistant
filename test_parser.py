
import unittest
from main import Assistant

class TestToolParser(unittest.TestCase):

    def setUp(self):
        self.assistant = Assistant()

    def test_write_file(self):
        # This command failed in the user's example
        command = 'write_file("test.txt", "hello world")'
        result = self.assistant.execute_tool(command)
        self.assertEqual(result, "Successfully wrote to test.txt.")
        # Verify file was actually written
        with open("test.txt", "r") as f:
            content = f.read()
        self.assertEqual(content, "hello world")
        # Clean up
        self.assistant.execute_tool('run_shell_command("del test.txt")')

    def test_run_shell_command(self):
        # This command also failed
        command = 'run_shell_command("echo hello")'
        result = self.assistant.execute_tool(command)
        self.assertIn("hello", result)

    def test_command_with_quotes_in_string(self):
        command = 'write_file("test_quotes.txt", "this is a \"test\" with quotes")'
        result = self.assistant.execute_tool(command)
        self.assertEqual(result, "Successfully wrote to test_quotes.txt.")
        with open("test_quotes.txt", "r") as f:
            content = f.read()
        self.assertEqual(content, 'this is a "test" with quotes')
        self.assistant.execute_tool('run_shell_command("del test_quotes.txt")')

if __name__ == '__main__':
    unittest.main()
