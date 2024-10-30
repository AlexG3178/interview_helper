import tkinter as tk
from tkinter import ttk

class InterviewAssistantUI:
    def __init__(self, root, on_question_select, previous_question, next_question):
        self.root = root
        self.root.title("Interview Assistant")
        self.root.geometry("600x500")

        self.on_question_select = on_question_select
        self.previous_question = previous_question
        self.next_question = next_question

        self.setup_ui()

    def setup_ui(self):
        # Paned window layout
        paned_window = tk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        paned_window.pack(fill=tk.BOTH, expand=True)

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

        # Navigation buttons
        button_frame = tk.Frame(left_frame)
        button_frame.pack(fill=tk.X)
        prev_button = tk.Button(button_frame, text="Previous", command=self.previous_question)
        next_button = tk.Button(button_frame, text="Next", command=self.next_question)
        prev_button.pack(side=tk.LEFT, padx=5, pady=5)
        next_button.pack(side=tk.LEFT, padx=5, pady=5)

        # Answer text area with scrollbar
        self.answer_text = tk.Text(right_frame, wrap="word", state=tk.DISABLED)
        self.answer_text.pack(fill=tk.BOTH, expand=True)
        answer_scrollbar = ttk.Scrollbar(right_frame, command=self.answer_text.yview)
        self.answer_text.config(yscrollcommand=answer_scrollbar.set)
        answer_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def update_question_list(self, questions, current_question_index, auto_scroll):
        self.question_listbox.delete(0, tk.END)
        for question in questions:
            self.question_listbox.insert(tk.END, question)

        if auto_scroll:
            self.question_listbox.selection_clear(0, tk.END)
            self.question_listbox.selection_set(current_question_index)
            self.question_listbox.activate(current_question_index)
            self.question_listbox.yview_moveto(1.0)
    
    def update_answer_text(self, answers, current_question_index, auto_scroll):
        self.answer_text.config(state=tk.NORMAL)
        self.answer_text.delete(1.0, tk.END)

        for i, answer in enumerate(answers):
            if i == current_question_index:
                self.answer_text.insert(tk.END, answer + "\n\n", "highlight")
                if auto_scroll:
                    self.answer_text.yview_moveto(1.0)
            else:
                self.answer_text.insert(tk.END, answer + "\n\n")
        
        self.answer_text.tag_config("highlight", background="yellow")
        self.answer_text.config(state=tk.DISABLED)