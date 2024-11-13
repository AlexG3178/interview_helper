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
        self.answer_text.bind("<Configure>", lambda event: self.ensure_answer_visibility())
    
    
    def ensure_answer_visibility(self):
        """Ensure the highlighted answer remains visible during window resizing."""
        if self.question_listbox.curselection():
            selected_index = self.question_listbox.curselection()[0]
            self.answer_text.see(f"{selected_index * 2 + 1}.0")  # Adjust to match line spacing
 
 
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
            self.start_recording(True)
        else:
            self.record_button.config(text="Record", bg="green")
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
        """Highlight the selected answer in the text widget and ensure full visibility."""
        self.answer_text.config(state=tk.NORMAL)  # Temporarily enable editing for updates
        self.answer_text.delete(1.0, tk.END)
    
        # Insert all answers and highlight the selected one
        for i, answer in enumerate(answers):
            tag = "highlight" if i == selected_index else None
            self.answer_text.insert(tk.END, f"{answer}\n\n", tag if tag else "normal")
    
        # Configure the highlight tag for styling
        self.answer_text.tag_configure("highlight", background="yellow", foreground="black")
        self.answer_text.config(state=tk.DISABLED)  # Disable editing again
    
        # Ensure the highlighted answer is fully visible
        if selected_index is not None:
            # Calculate start and end lines for the selected answer
            start_line = selected_index * 2 + 1
            end_line = start_line + 1  # Include the blank line after the answer
    
            # Scroll to ensure both start and end lines are visible
            self.answer_text.see(f"{start_line}.0")
            self.answer_text.see(f"{end_line}.0")
    
            # Scroll slightly more to ensure padding space for visibility
            self.answer_text.yview_scroll(-1, "units")  # Scroll up by 1 unit for better visibility

    
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
            self.start_recording(True)
        else:
            self.record_button_state = "record"
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
        