import unittest
import os
import tempfile
import json

from main import Assistant

import shutil

class TestToolParser(unittest.TestCase):

    def setUp(self):
        self.assistant = Assistant()
        self.temp_dir = os.path.join(os.getcwd(), "parser_test_temp")
        os.makedirs(self.temp_dir, exist_ok=True)
        self.assistant.set_output_callback(lambda x: None)

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_write_file(self):
        temp_file_path = os.path.join(self.temp_dir, "test_write_file.txt")
        tool_call = {
            "tool": "write_file",
            "args": {"path": temp_file_path, "content": "hello world"}
        }
        result = self.assistant.execute_tool(json.dumps(tool_call))
        self.assertEqual(result, f"Successfully wrote to {temp_file_path}.")
        with open(temp_file_path, "r") as f:
            content = f.read()
        self.assertEqual(content, "hello world")

    def test_run_shell_command(self):
        tool_call = {
            "tool": "run_shell_command",
            "args": {"command": "echo hello"}
        }
        result = self.assistant.execute_tool(json.dumps(tool_call))
        self.assertIn("STDOUT:\nhello", result)
        self.assertIn("STDERR:\n(empty)", result)

    def test_command_with_quotes_in_string(self):
        temp_file_path = os.path.join(self.temp_dir, "test_quotes.txt")
        tool_call = {
            "tool": "write_file",
            "args": {"path": temp_file_path, "content": "this is a \"test\" with quotes"}
        }
        result = self.assistant.execute_tool(json.dumps(tool_call))
        self.assertEqual(result, f"Successfully wrote to {temp_file_path}.")
        with open(temp_file_path, "r") as f:
            content = f.read()
        self.assertEqual(content, 'this is a "test" with quotes')

    def test_finish_tool_with_message(self):
        tool_call = {
            "tool": "finish",
            "args": {"message": "Task completed successfully."}
        }
        result = self.assistant.execute_tool(json.dumps(tool_call))
        self.assertEqual(result, "Task finished with message: Task completed successfully.")

    def test_finish_tool_without_message(self):
        tool_call = {"tool": "finish", "args": {}}
        result = self.assistant.execute_tool(json.dumps(tool_call))
        self.assertEqual(result, "Task finished with no specific message.")

    def test_write_file_relative_path_is_now_allowed(self):
        # This test now checks that relative paths are correctly handled
        relative_path = "test_relative_write.txt"
        absolute_path = os.path.abspath(relative_path)
        tool_call = {
            "tool": "write_file",
            "args": {"path": relative_path, "content": "relative content"}
        }
        result = self.assistant.execute_tool(json.dumps(tool_call))
        self.assertEqual(result, f"Successfully wrote to {absolute_path}.")
        with open(absolute_path, "r") as f:
            content = f.read()
        self.assertEqual(content, "relative content")
        os.remove(absolute_path)

    def test_read_file_relative_path_is_now_allowed(self):
        # This test now checks that relative paths are correctly handled
        relative_path = "test_relative_read.txt"
        absolute_path = os.path.abspath(relative_path)
        with open(absolute_path, "w") as f:
            f.write("relative read")

        tool_call = {
            "tool": "read_file",
            "args": {"path": relative_path}
        }
        result = self.assistant.execute_tool(json.dumps(tool_call))
        self.assertEqual(result, "relative read")
        os.remove(absolute_path)

    def test_invalid_json(self):
        invalid_json = '{"tool": "run_shell_command", "args": {"command": "echo hello"}' # Missing closing brace
        result = self.assistant.execute_tool(invalid_json)
        self.assertIn("Error: Invalid JSON from LLM.", result)

    def test_unknown_tool(self):
        tool_call = {"tool": "non_existent_tool", "args": {}}
        result = self.assistant.execute_tool(json.dumps(tool_call))
        self.assertIn("Error: The tool 'non_existent_tool' is not valid.", result)

    def test_fuzzy_match_tool_name_success(self):
        # Test with a typo that should be corrected
        temp_file_path = os.path.join(self.temp_dir, "fuzzy_test.txt")
        tool_call = {
            "tool": "write_fil", # Typo for "write_file"
            "args": {"path": temp_file_path, "content": "fuzzy content"}
        }
        result = self.assistant.execute_tool(json.dumps(tool_call))
        self.assertEqual(result, f"Successfully wrote to {temp_file_path}.")
        with open(temp_file_path, "r") as f:
            self.assertEqual(f.read(), "fuzzy content")

    def test_fuzzy_match_tool_name_failure(self):
        # Test with a typo that is too different to be corrected
        tool_call = {
            "tool": "completely_wrong_tool",
            "args": {}
        }
        result = self.assistant.execute_tool(json.dumps(tool_call))
        self.assertIn("Error: The tool 'completely_wrong_tool' is not valid.", result)


if __name__ == '__main__':
    unittest.main()