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
        
        # Question text widget
        self.question_text = tk.Text(
            left_frame,
            wrap=tk.WORD,
            state=tk.DISABLED,
            bg="#1D1E1E",
            fg="white",
            insertbackground="white",
            borderwidth=0,
            highlightthickness=0
        )
        self.question_text.pack(fill=tk.BOTH, expand=True)
        self.question_text.bind("<Button-1>", self.on_question_click)

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
        if self.question_text.tag_ranges("highlight"):
            start_index = self.question_text.tag_ranges("highlight")[0]  # Get the start of the highlight tag
            self.answer_text.see(start_index)  # Scroll to match the question's index

 
    def scroll_to_end(self):
        """Scroll both the question list and answer text to the end."""
        self.question_text.yview_moveto(1.0)
        self.answer_text.yview_moveto(1.0)


    def scroll_to_question(self, index):
        """Scroll to the specific question in the list."""
        self.question_text.see(index)


    def toggle_recording(self):
        self.is_recording = not self.is_recording

        if self.is_recording:
            self.record_button.config(text="Stop", bg="red")
            self.start_recording(True)
        else:
            self.record_button.config(text="Record", bg="green")
            self.start_recording(False)

        self.root.after(100, self.scroll_to_end)


    def on_question_click(self, event, index=None):
        """Handle the selection of a question in the text widget."""
        if index is not None:
            self.start_recording(False)  # Stop recording when a question is selected
            self.on_question_select(index)


 
    def update_questions_and_answers(self, questions, answers):
        """Update the UI to display all questions and answers."""
        self.question_text.config(state=tk.NORMAL)
        self.answer_text.config(state=tk.NORMAL)
        self.question_text.delete(1.0, tk.END)
        self.answer_text.delete(1.0, tk.END)

        # Populate questions in the text widget
        for i, question in enumerate(questions):
            tag = f"question_{i}"
            start = self.question_text.index(tk.END)
            self.question_text.insert(tk.END, f"{question}\n\n", tag)
            end = self.question_text.index(tk.END)
            self.question_text.tag_add(tag, start, end)
            self.question_text.tag_bind(tag, "<Button-1>", lambda event, index=i: self.on_question_click(event, index))

        # Populate answers in the text widget
        for answer in answers:
            self.answer_text.insert(tk.END, f"{answer}\n\n")

        self.question_text.config(state=tk.DISABLED)
        self.answer_text.config(state=tk.DISABLED)

 
    def highlight_answer(self, selected_index, answers):
        """Highlight the selected answer and corresponding question."""
        # Enable editing temporarily
        self.answer_text.config(state=tk.NORMAL)
        self.question_text.config(state=tk.NORMAL)

        # Clear previous highlights
        self.answer_text.tag_remove("highlight", "1.0", tk.END)
        self.question_text.tag_remove("highlight", "1.0", tk.END)

        # Highlight the selected question
        if selected_index is not None:
            question_start = f"{selected_index * 2 + 1}.0"
            question_end = f"{selected_index * 2 + 2}.0"
            self.question_text.tag_add("highlight", question_start, question_end)
            self.question_text.tag_configure("highlight", background="yellow", foreground="black")
            self.question_text.see(question_start)

        # Highlight the selected answer
        for i, answer in enumerate(answers):
            answer_start = f"{i * 2 + 1}.0"
            answer_end = f"{i * 2 + 2}.0"
            if i == selected_index:
                self.answer_text.tag_add("highlight", answer_start, answer_end)
                self.answer_text.tag_configure("highlight", background="yellow", foreground="black")
                self.answer_text.see(answer_start)

        # Disable editing again
        self.answer_text.config(state=tk.DISABLED)
        self.question_text.config(state=tk.DISABLED)

    
    def scroll_to_highlight(self):
        if self.is_recording:
            self.question_text.yview_moveto(1)
            self.answer_text.yview_moveto(1)
        else:
            selected = self.question_text.curselection()
            if selected:
                self.question_text.see(selected[0])


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
        