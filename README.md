# CodeGuru

CodeGuru is a simple, locally-run AI assistant designed to help with development tasks. You can provide it with a goal, and it will use a set of tools to try and achieve it. It's a great way to experiment with AI agents without relying on cloud services.

## How it works

The assistant uses a local Large Language Model (LLM) to make decisions. You can connect it to any LLM that has an OpenAI-compatible API endpoint (like LM Studio). The assistant is given a set of tools (like file I/O, shell commands, and web search) and uses the LLM to decide which tool to use to accomplish the goal.

## Running the assistant

1.  **Start your local LLM:** Make sure your local LLM (e.g., LM Studio) is running and the API endpoint is active.
2.  **Install dependencies:** `pip install -r requirements.txt`
3.  **Run the GUI:** `python gui.py`
4.  **Set your goal:** Enter a development goal in the input box and click "Run Assistant". You can also attach local files to provide the assistant with more context.