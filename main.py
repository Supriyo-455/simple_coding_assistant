
import argparse
import os
import subprocess
import requests

def main():
    """
    The main function of the coding assistant.
    """
    parser = argparse.ArgumentParser(description='A simple coding assistant.')
    parser.add_argument('command', help='The command to execute.')
    parser.add_argument('args', nargs='*', help='The arguments for the command.')
    args = parser.parse_args()

    if args.command == 'run':
        execute_code(' '.join(args.args))
    elif args.command == 'write':
        write_file(args.args[0], ' '.join(args.args[1:]))
    elif args.command == 'edit':
        edit_file(args.args[0], ' '.join(args.args[1:]))
    elif args.command == 'delete':
        delete_file(args.args[0])
    elif args.command == 'push':
        push_to_github(' '.join(args.args))
    elif args.command == 'llm':
        get_llm_response(' '.join(args.args))
    else:
        print(f'Unknown command: {args.command}')

def execute_code(command):
    """
    Executes the given code.
    """
    try:
        subprocess.run(command, shell=True, check=True)
    except subprocess.CalledProcessError as e:
        print(f'Error executing code: {e}')

def write_file(path, content):
    """
    Writes the given content to the given file.
    """
    with open(path, 'w') as f:
        f.write(content)

def edit_file(path, content):
    """
    Edits the given file with the given content.
    """
    with open(path, 'a') as f:
        f.write(content)

def delete_file(path):
    """
    Deletes the given file.
    """
    os.remove(path)

def push_to_github(message):
    """
    Pushes the current code to GitHub.
    """
    subprocess.run(['git', 'add', '.'])
    subprocess.run(['git', 'commit', '-m', message])
    subprocess.run(['git', 'push'])

def get_llm_response(prompt):
    """
    Gets a response from the LLM.
    """
    # Replace with your LM-Studio API endpoint
    url = 'http://localhost:1234/v1/chat/completions'
    headers = {'Content-Type': 'application/json'}
    data = {
        'messages': [
            {'role': 'user', 'content': prompt}
        ]
    }
    response = requests.post(url, headers=headers, json=data)
    print(response.json()['choices'][0]['message']['content'])

if __name__ == '__main__':
    main()
