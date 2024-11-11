import tkinter as tk
from tkinter.font import Font


class InterviewAssistantUI:
    def __init__(self, root, on_question_select, start_recording):
        self.default_font = Font(family="Helvetica", size=14)  # Font settings
        self.root = root
        self.root.option_add("*Font", self.default_font)
        self.root.title("Interview Assistant")
        self.root.geometry("1000x800")
        self.on_question_select = on_question_select
        self.start_recording = start_recording
        self.is_recording = False  # Recording state
        self.setup_ui()

    def setup_ui(self):
        # Set overall background color
        self.root.config(bg="#282828")

        # Top section for recording options
        top_frame = tk.Frame(self.root, bg="#282828")
        top_frame.pack(fill=tk.X, padx=10, pady=5)

        # Meeting URL entry with placeholder
        self.url_entry = tk.Entry(
            top_frame,
            width=40,
            fg="#bbbbbb",
            bg="#333333",
            insertbackground="white",
            relief=tk.FLAT
        )
        self.url_entry.insert(0, "Paste meeting URL to record")
        self.url_entry.pack(side=tk.LEFT, padx=5, pady=5, ipady=4)

        # Bind placeholder behavior
        self.url_entry.bind("<FocusIn>", self.clear_placeholder)
        self.url_entry.bind("<FocusOut>", self.add_placeholder)

        # Custom Record/Stop button
        self.record_button_canvas = tk.Canvas(
            top_frame,
            width=100,
            height=30,
            bg="#282828",
            highlightthickness=0
        )
        self.record_button_canvas.pack(side=tk.LEFT, padx=10, pady=5)
        self.draw_button("Record", "#28a745")  # Initial button: green

        # Bind click event to the button
        self.record_button_canvas.bind("<Button-1>", self.toggle_recording)

        # Paned window layout
        paned_window = tk.PanedWindow(self.root, orient=tk.HORIZONTAL, bg="#282828", sashrelief=tk.FLAT)
        paned_window.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Left frame for questions
        left_frame = tk.Frame(paned_window, bg="#333333", relief=tk.FLAT, bd=1)
        right_frame = tk.Frame(paned_window, bg="#333333", relief=tk.FLAT, bd=1)

        # Add frames to paned window
        paned_window.add(left_frame)
        paned_window.add(right_frame)
        paned_window.paneconfig(left_frame, minsize=300)

        # Question listbox
        self.question_listbox = tk.Listbox(
            left_frame,
            bg="#282828",
            fg="white",
            selectbackground="#007bff",  # Blue highlight for selected questions
            selectforeground="white",
            relief=tk.FLAT
        )
        self.question_listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.question_listbox.bind("<<ListboxSelect>>", self.on_question_select)

        # Answer display (right frame)
        self.answer_text = tk.Text(
            right_frame,
            wrap=tk.WORD,
            bg="#282828",
            fg="white",
            state=tk.DISABLED,
            insertbackground="white",
            relief=tk.FLAT
        )
        self.answer_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Status bar
        self.status_label = tk.Label(
            self.root,
            text="Idle",
            bd=1,
            relief=tk.SUNKEN,
            anchor=tk.W,
            bg="#282828",
            fg="white"
        )
        self.status_label.pack(side=tk.BOTTOM, fill=tk.X)

    def draw_button(self, text, color):
        """Draw a custom button on the canvas."""
        self.record_button_canvas.delete("all")  # Clear the canvas
        self.record_button_canvas.create_rectangle(
            0, 0, 100, 30,
            fill=color,
            outline=color
        )
        self.record_button_canvas.create_text(
            50, 15,
            text=text,
            fill="white",
            font=("Helvetica", 12, "bold")
        )

    def clear_placeholder(self, event):
        if self.url_entry.get() == "Paste meeting URL to record":
            self.url_entry.delete(0, tk.END)
            self.url_entry.config(fg="white")

    def add_placeholder(self, event):
        if not self.url_entry.get():
            self.url_entry.insert(0, "Paste meeting URL to record")
            self.url_entry.config(fg="#bbbbbb")

    def toggle_recording(self, event=None):
        """Toggle recording state and update the button/UI accordingly."""
        self.is_recording = not self.is_recording
        if self.is_recording:
            self.draw_button("Stop", "#dc3545")  # Red for "Stop"
            self.status_label.config(text="Recording started...")
            self.url_entry.config(state="disabled")  # Disable URL editing
            self.start_recording(True)
        else:
            self.draw_button("Record", "#28a745")  # Green for "Record"
            self.status_label.config(text="Recording stopped.")
            self.url_entry.config(state="normal")  # Enable URL editing
            self.start_recording(False)

    def populate_questions_and_answers(self, question, answer):
        """Add a new question-answer pair and display it."""
        self.question_listbox.insert(tk.END, question.strip())  # Add question to the listbox
        self.update_answers_display()  # Update the answer display dynamically

    def update_answers_display(self):
        """Update the right-side answers text box."""
        self.answer_text.config(state=tk.NORMAL)
        self.answer_text.delete(1.0, tk.END)  # Clear existing content
    
        # Display all answers with numbering
        for i, (_, answer) in enumerate(self.parent.qa_pairs):  # Parent holds `qa_pairs`
            self.answer_text.insert(tk.END, f"{i + 1}. {answer}\n\n")
    
        self.answer_text.config(state=tk.DISABLED)

    def display_answer(self, answer):
        """Display the selected answer in yellow."""
        self.answer_text.config(state=tk.NORMAL)
        self.answer_text.delete(1.0, tk.END)
        self.answer_text.insert(tk.END, answer)
        self.answer_text.tag_add("highlight", "1.0", "end")
        self.answer_text.tag_configure("highlight", background="#FFD700", foreground="black")  # Yellow
        self.answer_text.config(state=tk.DISABLED)

    def on_question_select(self, event):
        """Highlight the selected question and display the corresponding answer."""
        selected_index = self.question_listbox.curselection()
        if selected_index:
            index = selected_index[0]
            question, answer = self.qa_pairs[index]
            self.display_answer(answer)
