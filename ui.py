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

        # Create a custom style for the entry widget
        style = ttk.Style()
        style.configure(
            "Custom.TEntry",
            foreground="grey",
            fieldbackground="#1D1E1E",
            insertcolor="grey",         # Cursor color
            insertbackground="green"
        )  
        
        # Meeting URL entry with placeholder
        self.url_entry = ttk.Entry(
            top_frame,
            width=40,
            style="Custom.TEntry"
        )
        self.url_entry.pack(side=tk.LEFT, padx=5)
        self.url_entry.insert(0, "Paste meeting URL to record")

        # Bind events to handle placeholder behavior
        self.url_entry.bind("<FocusIn>", self.clear_placeholder)
        self.url_entry.bind("<FocusOut>", self.add_placeholder)

        self.create_record_button(top_frame)
 
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
        self.answer_text = tk.Text(
            right_frame, 
            wrap=tk.WORD, 
            state=tk.DISABLED, 
            bg="#1D1E1E", 
            fg="white", 
            insertbackground="white",
            borderwidth=0,
            highlightthickness=0
        )
        self.answer_text.pack(fill=tk.BOTH, expand=True)
 
 
    def clear_placeholder(self, event):
        if self.url_entry.get() == "Paste meeting URL to record":
            self.url_entry.delete(0, tk.END)
            self.url_entry.config(fg="black")
 
 
    def add_placeholder(self, event):
        if not self.url_entry.get():
            self.url_entry.insert(0, "Paste meeting URL to record")
            self.url_entry.config(fg="light gray")
 
 
    def scroll_to_end(self):
        """Scroll both the question list and answer text to the end."""
        self.question_listbox.yview_moveto(1.0)
        self.answer_text.yview_moveto(1.0)


    def scroll_to_question(self, index):
        """Scroll to the specific question in the list."""
        self.question_listbox.see(index)


    def toggle_recording(self):
        self.is_recording = not self.is_recording

        if self.is_recording:
            self.record_button.config(text="Stop", bg="red")
            self.url_entry.config(state=tk.DISABLED)  # Lock the field
            self.start_recording(True)
        else:
            self.record_button.config(text="Record", bg="green")
            self.url_entry.config(state=tk.NORMAL)  # Unlock the field
            self.start_recording(False)

        self.root.after(100, self.scroll_to_end)
 
 
    def populate_questions_and_answers(self, questions, answers):
        self.question_listbox.delete(0, tk.END)
        self.answer_text.delete(1.0, tk.END)
 
        for question in questions:
            self.question_listbox.insert(tk.END, question)
 
        for answer in answers:
            self.answer_text.insert(tk.END, f"{answer}\n\n")
 
 
    def highlight_answer(self, selected_index, answers):
        """Highlight the selected answer in the text widget."""
        self.answer_text.config(state=tk.NORMAL)  # Temporarily enable editing for updates
        self.answer_text.delete(1.0, tk.END)
        for i, answer in enumerate(answers):
            tag = "highlight" if i == selected_index else None
            self.answer_text.insert(tk.END, f"{answer}\n\n", tag if tag else "normal")
        self.answer_text.tag_configure("highlight", background="yellow", foreground="black")
        self.answer_text.config(state=tk.DISABLED)  # Disable editing again
        
    
    def scroll_to_highlight(self):
        if self.is_recording:
            self.question_listbox.yview_moveto(1)
            self.answer_text.yview_moveto(1)
        else:
            selected = self.question_listbox.curselection()
            if selected:
                self.question_listbox.see(selected[0])


    def draw_record_button(self):
        """Draw the record or stop button based on the state."""
        self.record_canvas.delete("all")  # Clear the canvas
        if self.record_button_state == "record":
            self.record_canvas.create_rectangle(0, 0, 100, 40, fill="green", outline="")
            self.record_canvas.create_text(50, 20, text="Record", fill="white", font=("Arial", 14))
        else:
            self.record_canvas.create_rectangle(0, 0, 100, 40, fill="red", outline="")
            self.record_canvas.create_text(50, 20, text="Stop", fill="white", font=("Arial", 14))


    def toggle_record_custom_button(self, event):
        """Toggle the state of the custom record button."""
        if self.record_button_state == "record":
            self.record_button_state = "stop"
            self.url_entry.config(state=tk.DISABLED)  # Lock the field
            self.start_recording(True)
        else:
            self.record_button_state = "record"
            self.url_entry.config(state=tk.NORMAL)  # Unlock the field
            self.start_recording(False)

        self.draw_record_button()


    def create_record_button(self, frame):
        """Create a custom record button."""
        self.record_canvas = tk.Canvas(frame, width=100, height=40, bg="black", highlightthickness=0)
        self.record_canvas.pack(side=tk.LEFT, padx=5)

        # Initial button state
        self.record_button_state = "record"  # Can be 'record' or 'stop'

        # Draw the button
        self.draw_record_button()

        # Bind events
        self.record_canvas.bind("<Button-1>", self.toggle_record_custom_button)
        