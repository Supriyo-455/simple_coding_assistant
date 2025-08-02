
import tkinter as tk
from tkinter import scrolledtext, ttk
from main import Assistant
import threading

class UIManager:
    def __init__(self, root):
        self.root = root
        self.root.title("CodeGuru")
        self.root.geometry("800x600") # Set a default window size

        # Configure style for ttk widgets
        self.style = ttk.Style()
        self.style.theme_use('clam') # A good base theme for customization

        # Define a modern color palette
        self.primary_color = '#4CAF50'  # Green
        self.secondary_color = '#2196F3' # Blue
        self.background_color = '#ECEFF1' # Light Grey
        self.text_color = '#263238'     # Dark Grey
        self.output_bg_color = '#FFFFFF' # White

        # Configure general styles
        self.style.configure('TFrame', background=self.background_color)
        self.style.configure('TLabel', background=self.background_color, foreground=self.text_color, font=('Segoe UI', 10))
        self.style.configure('TButton', font=('Segoe UI', 10, 'bold'), foreground='white', background=self.primary_color, borderwidth=0)
        self.style.map('TButton', background=[('active', self.secondary_color)])

        # Configure specific widget styles
        self.style.configure('Title.TLabel', font=('Segoe UI', 18, 'bold'), foreground=self.primary_color)
        self.style.configure('Goal.TLabel', font=('Segoe UI', 11, 'bold'), foreground=self.text_color)
        

        # Root window background
        self.root.configure(background=self.background_color)

        # Main frame
        self.main_frame = ttk.Frame(root, padding="20 20 20 20")
        self.main_frame.pack(fill="both", expand=True)

        # Title
        self.title_label = ttk.Label(self.main_frame, text="CodeGuru", style='Title.TLabel')
        self.title_label.pack(pady=(0, 20))

        # Goal input frame
        self.goal_frame = ttk.Frame(self.main_frame)
        self.goal_frame.pack(fill="x", pady=(0, 10))

        self.label = ttk.Label(self.goal_frame, text="Enter your development goal:", style='Goal.TLabel')
        self.label.pack(side=tk.TOP, anchor=tk.W, padx=(0, 5), pady=(0, 5))

        self.goal_entry = scrolledtext.ScrolledText(self.goal_frame, wrap=tk.WORD, height=4, relief=tk.FLAT, font=('Segoe UI', 10), bg=self.output_bg_color, fg=self.text_color)
        self.goal_entry.pack(side=tk.TOP, fill="x", expand=True)

        # Buttons frame
        self.button_frame = ttk.Frame(self.main_frame)
        self.button_frame.pack(fill="x", pady=(10, 20))

        self.run_button = ttk.Button(self.button_frame, text="Run Assistant", command=self.run_assistant)
        self.run_button.pack(side=tk.LEFT, padx=(0, 10))

        self.stop_button = ttk.Button(self.button_frame, text="Stop Assistant", command=self.stop_assistant, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT)

        # Output area
        self.output_area = scrolledtext.ScrolledText(self.main_frame, wrap=tk.WORD, relief=tk.FLAT, font=('Consolas', 10), bg=self.output_bg_color, fg=self.text_color)
        self.output_area.pack(pady=(0, 0), fill="both", expand=True)

        self.assistant = Assistant()
        self.assistant.set_output_callback(self.update_output)
        self.assistant_thread = None

    def update_output(self, text):
        self.output_area.insert(tk.END, text + "\n")
        self.output_area.see(tk.END)

    def clear_output(self):
        self.output_area.delete(1.0, tk.END)

    def run_assistant(self):
        if self.assistant_thread and self.assistant_thread.is_alive():
            self.update_output("Assistant is already running.")
            return

        goal = self.goal_entry.get("1.0", tk.END).strip()
        if not goal:
            self.update_output("Please enter a development goal.")
            return

        self.clear_output() # Clear previous output
        self.run_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.goal_entry.config(state=tk.DISABLED) # Disable entry while running
        self.update_output(f"Starting assistant with goal: {goal}")

        self.assistant_thread = threading.Thread(target=self._run_assistant_thread, args=(goal,))
        self.assistant_thread.daemon = True
        self.assistant_thread.start()

    def _run_assistant_thread(self, goal):
        try:
            self.assistant.run(goal)
        finally:
            # Ensure buttons are re-enabled even if an error occurs
            self.root.after(0, self._reset_ui_state) # Use after to update UI from thread

    def stop_assistant(self):
        if self.assistant_thread and self.assistant_thread.is_alive():
            self.assistant.stop()
            self.update_output("Assistant stopped.")
        self._reset_ui_state()

    def _reset_ui_state(self):
        self.run_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.goal_entry.config(state=tk.NORMAL)
        self.update_output("\n--- Assistant is ready for a new goal. ---")

if __name__ == "__main__":
    root = tk.Tk()
    app = UIManager(root)
    root.mainloop()
