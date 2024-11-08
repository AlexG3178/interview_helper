import tkinter as tk
from tkinter import ttk

class InterviewAssistantUI:
    def __init__(self, root, on_question_select, start_recording):
        self.root = root
        self.root.title("Interview Assistant")
        self.root.geometry("1000x800")
        self.on_question_select = on_question_select
        self.start_recording = start_recording
        self.is_recording = False
        self.record_button = None
        self.setup_ui()

    def setup_ui(self):
        # Top section for recording options
        top_frame = tk.Frame(self.root)
        top_frame.pack(fill=tk.X, padx=10, pady=5)

        # Meeting URL entry with placeholder
        self.url_entry = tk.Entry(top_frame, width=40, fg="light gray")
        self.url_entry.insert(0, "Paste meeting URL to record")
        self.url_entry.pack(side=tk.LEFT, padx=5)
        
        # Bind events to handle placeholder behavior
        self.url_entry.bind("<FocusIn>", self.clear_placeholder)
        self.url_entry.bind("<FocusOut>", self.add_placeholder)

        # Record button
        self.record_button = tk.Button(
            top_frame, 
            text="Record", 
            command=self.toggle_recording, 
            bg="green", 
            fg="white"
        )
        self.record_button.pack(side=tk.LEFT)

        # Paned window layout
        paned_window = tk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        paned_window.pack(fill=tk.BOTH, expand=True)

        # Left frame for questions
        left_frame = tk.Frame(paned_window, width=300)
        right_frame = tk.Frame(paned_window)
        
        # Add frames to paned window
        paned_window.add(left_frame)
        paned_window.add(right_frame)
        paned_window.paneconfig(left_frame, minsize=300)

        # Question listbox
        self.question_listbox = tk.Listbox(left_frame)
        self.question_listbox.pack(fill=tk.BOTH, expand=True)
        self.question_listbox.bind("<<ListboxSelect>>", self.on_question_select)

        # Answer display (right frame)
        self.answer_text = tk.Text(right_frame, wrap=tk.WORD)
        self.answer_text.pack(fill=tk.BOTH, expand=True)

    def clear_placeholder(self, event):
        if self.url_entry.get() == "Paste meeting URL to record":
            self.url_entry.delete(0, tk.END)
            self.url_entry.config(fg="black")

    def add_placeholder(self, event):
        if not self.url_entry.get():
            self.url_entry.insert(0, "Paste meeting URL to record")
            self.url_entry.config(fg="light gray")
            
    def toggle_recording(self):
        self.is_recording = not self.is_recording

        if self.is_recording:
            self.record_button.config(text="Stop", bg="red")
            self.start_recording(True)    
        else:
            self.record_button.config(text="Record", bg="green")
            self.start_recording(False)

    def populate_questions(self, questions):
        self.question_listbox.delete(0, tk.END)
        for question in questions:
            self.question_listbox.insert(tk.END, question)

    def display_answer(self, answer):
        self.answer_text.delete(1.0, tk.END)
        self.answer_text.insert(tk.END, answer)
