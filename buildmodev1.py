import tkinter as tk
from tkinter import scrolledtext, messagebox
import requests
import json
import os
import subprocess

# Load local env.txt if present (never commit secrets)
_ENV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "env.txt")
if os.path.exists(_ENV_PATH):
    with open(_ENV_PATH, "r", encoding="utf-8") as _fh:
        for _line in _fh:
            _line = _line.strip()
            if not _line or _line.startswith("#") or "=" not in _line:
                continue
            _k, _v = _line.split("=", 1)
            os.environ.setdefault(_k.strip(), _v.strip())

# API key from environment
API_KEY = os.environ.get("OPENAI_API_KEY", "")
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {API_KEY}"
}

# Set the directory for storing files
base_dir = os.path.join(os.path.expanduser("~"), "Desktop", "MartinCode")
working_file = os.path.join(base_dir, "working_file.py")
rollback_file = os.path.join(base_dir, "rollback_file.py")
gold_copy_file = os.path.join(base_dir, "gold_copy.py")

# Ensure the directory and files exist
os.makedirs(base_dir, exist_ok=True)
for file in [working_file, rollback_file, gold_copy_file]:
    if not os.path.exists(file):
        with open(file, 'w') as f:
            f.write("")

def check_api_key():
    try:
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json={
                "model": "gpt-4o-2024-05-13",
                "messages": [{"role": "user", "content": "Say 'API key is valid'"}],
                "max_tokens": 4000,
                "temperature": 0.0
            }
        )
        if response.status_code == 200:
            response_json = response.json()
            message = response_json['choices'][0]['message']['content'].strip()
            messagebox.showinfo("API Key Check", message)
        else:
            message = f"API Key Check Failed: {response.status_code}"
            messagebox.showerror("API Key Check", message)
    except Exception as e:
        messagebox.showerror("API Key Check", f"Error: {str(e)}")

def extract_code_from_response(response_text):
    prompt = f"""Extract only the Python code from the following response without any markdown, explanation, or additional text. 
                 Only provide the complete Python code, nothing else:
                 {response_text}"""
    data = {
        "model": "gpt-4o-2024-05-13",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.0,  # Lower temperature for more deterministic output
        "max_tokens": 4000
    }
    response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=data)
    if response.status_code == 200:
        response_json = response.json()
        code = response_json['choices'][0]['message']['content'].strip()
        # Clean up any incomplete code
        if code.startswith("```python"):
                code = code[9:].strip()
        if code.endswith("```"):
            code = code[:-3].strip()
        return code
    else:
        return response_text  # Return the original response if API call fails

def save_code_to_file(code, filename):
    with open(filename, 'w') as f:
        f.write(code)

def update_files_with_new_code(new_code):
    # Save the current working file to rollback file
    with open(working_file, 'r') as wf:
        rollback_code = wf.read()
    save_code_to_file(rollback_code, rollback_file)

    # Save the new code to working file
    save_code_to_file(new_code, working_file)

def handle_user_feedback():
    feedback_window = tk.Toplevel(root)
    feedback_window.title("User Feedback")

    def save_as_gold():
        save_code_to_file(open(working_file).read(), gold_copy_file)
        console_output_area.insert(tk.END, "Saved as gold copy.\n")
        feedback_window.destroy()

    def rollback_to_working():
        save_code_to_file(open(rollback_file).read(), working_file)
        console_output_area.insert(tk.END, "Rolled back to last working copy.\n")
        feedback_window.destroy()

    def rollback_to_gold():
        save_code_to_file(open(gold_copy_file).read(), working_file)
        console_output_area.insert(tk.END, "Rolled back to gold copy.\n")
        feedback_window.destroy()

    tk.Button(feedback_window, text="Save as Gold", command=save_as_gold).pack(pady=5)
    tk.Button(feedback_window, text="Rollback to Working", command=rollback_to_working).pack(pady=5)
    tk.Button(feedback_window, text="Rollback to Gold", command=rollback_to_gold).pack(pady=5)

def run_generated_code():
    try:
        process = subprocess.Popen(['python', working_file], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()
        console_output_area.insert(tk.END, stdout.decode() + stderr.decode())
        
        if stderr:
            iterate_code_fix(stderr.decode())
        else:
            console_output_area.insert(tk.END, "Code ran successfully.\n")
    except Exception as e:
        console_output_area.insert(tk.END, f"Error running code: {str(e)}\n")
    handle_user_feedback()

def iterate_code_fix(error_log):
    try:
        with open(working_file, 'r') as wf:
            current_code = wf.read()
        
        data = {
            "model": "gpt-4o-2024-05-13",
            "messages": [
                {"role": "user", "content": f"Here is the current code:\n\n{current_code}\n\nHere is the error log:\n\n{error_log}\n\nPlease provide a fixed version of the code."}
            ],
            "max_tokens": 4000,
            "temperature": 0.0
        }
        
        response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=data)
        if response.status_code == 200:
            response_json = response.json()
            full_response = response_json['choices'][0]['message']['content'].strip()
            code = extract_code_from_response(full_response)
            update_files_with_new_code(code)
            console_output_area.insert(tk.END, "Code updated with the fix.\n")
            run_generated_code()
        else:
            console_output_area.insert(tk.END, "Failed to fix the code. Please check the API key and try again.\n")
    except Exception as e:
        console_output_area.insert(tk.END, f"Error during code fixing: {str(e)}\n")

def generate_code():
    request = entry.get()
    
    try:
        with open(working_file, 'r') as wf:
            current_code = wf.read()
        
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json={
                "model": "gpt-4o-2024-05-13",
                "messages": [{"role": "user", "content": f"Generate a simple {request} code in Python. Here is the current code context:\n{current_code}"}],
                "max_tokens": 4000,
                "temperature": 0.0
            }
        )
        if response.status_code == 200:
            response_json = response.json()
            full_response = response_json['choices'][0]['message']['content'].strip()
            code = extract_code_from_response(full_response)
            update_files_with_new_code(code)
            console_output_area.insert(tk.END, "Code saved successfully.\n")
            run_generated_code()
        else:
            full_response = "Failed to generate code. Please check the API key and try again."
            code = full_response
    except Exception as e:
        full_response = f"Error: {str(e)}"
        code = full_response
    
    chat_output_area.insert(tk.END, f"User: {request}\nAI: {full_response}\n\n")
    code_output_area.delete('1.0', tk.END)
    code_output_area.insert(tk.END, code)

# Create the main window
root = tk.Tk()
root.title("Simple AI Code Generator")

# Set up the layout
root.grid_rowconfigure(1, weight=1)
root.grid_rowconfigure(3, weight=1)
root.grid_columnconfigure(1, weight=1)

# Entry widget at the top left
entry_label = tk.Label(root, text="Enter your request:")
entry_label.grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)

entry = tk.Entry(root, width=50)
entry.grid(row=0, column=1, padx=5, pady=5, sticky=tk.EW)

# Button widget next to the entry widget
generate_button = tk.Button(root, text="Generate Code", command=generate_code)
generate_button.grid(row=0, column=2, padx=5, pady=5, sticky=tk.E)

# Button to run the current working file
run_button = tk.Button(root, text="Run Current Working File", command=run_generated_code)
run_button.grid(row=0, column=3, padx=5, pady=5, sticky=tk.E)


# Chat output area
chat_label = tk.Label(root, text="Chat History:")
chat_label.grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)

chat_output_area = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=30, height=20)
chat_output_area.grid(row=2, column=0, padx=5, pady=5, rowspan=3, sticky=tk.NS)

# Code output area
code_label = tk.Label(root, text="Generated Code:")
code_label.grid(row=1, column=1, columnspan=2, padx=5, pady=5, sticky=tk.W)

code_output_area = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=70, height=15)
code_output_area.grid(row=2, column=1, columnspan=3, padx=5, pady=5, sticky=tk.NSEW)

# Console output area
console_label = tk.Label(root, text="Console Log:")
console_label.grid(row=3, column=1, columnspan=2, padx=5, pady=5, sticky=tk.W)

console_output_area = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=70, height=15)
console_output_area.grid(row=4, column=1, columnspan=3, padx=5, pady=5, sticky=tk.NSEW)

# Ensure the GUI is fully set up before running the main loop
root.update_idletasks()

# Run the API key check on load
check_api_key()

# Run the application
root.mainloop()
