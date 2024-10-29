import tkinter as tk
from tkinter import ttk
import threading
import time
import openai
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

from config import config 

openai.api_key = config['api_key']

chrome_options = Options()
chrome_options.add_argument("--user-data-dir=C:\\Users\\Maut\\AppData\\Local\\Google\\Chrome")
chrome_options.add_argument("--profile-directory=Profile 1")  
chrome_options.add_argument("--disable-dev-shm-usage")  
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--no-sandbox")  
chrome_options.add_argument("--disable-software-rasterizer")

driver = uc.Chrome(options=chrome_options) 

questions = []
answers = []
current_question_index = 0
lock = threading.Lock()

# Function to extract transcription from Otter.ai live session
def get_otter_transcription():
    try:
        driver.get(config['session_url'])  
        time.sleep(5)  
        transcription_elements = driver.find_elements(By.XPATH, config['message_container_path'])
        combined_text = " ".join([element.text for element in transcription_elements])
        return combined_text
    except Exception as e:
        print(f"Error accessing Otter.ai: {e}")
        return None

# Function to send the text to OpenAI GPT and get a response
def get_gpt_response(question):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",  
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": question}
            ],
            max_tokens=100,
            temperature=0.5,
        )
        return response.choices[0].message['content'].strip()
    except Exception as e:
        print(f"Error querying GPT: {e}")
        return None

def show_question():
    global current_question_index
    question_listbox.selection_clear(0, tk.END)
    question_listbox.selection_set(current_question_index)
    question_listbox.activate(current_question_index)
    question_listbox.see(current_question_index)

    answer_text.config(state=tk.NORMAL)
    answer_text.delete(1.0, tk.END)

    # Display all answers in sequence
    for answer in answers:
        answer_text.insert(tk.END, answer + "\n\n")

    answer_text.config(state=tk.DISABLED)

def update_ui():
    with lock:
        question_listbox.delete(0, tk.END)
        for question in questions:
            question_listbox.insert(tk.END, question)
        if questions:
            show_question()

def fetch_answer_in_background(question):
    print(f"Fetching answer for: {question}")
    answer = get_gpt_response(question)
    if answer:
        with lock:
            # Append the new answer instead of overwriting
            answers.append(answer)
        # Update the answer in the UI through the main thread
        root.after(0, show_question)
    else:
        print(f"Failed to get an answer for: {question}")

def ui_thread():
    global current_question_index, question_listbox, answer_text, root

    def next_question():
        global current_question_index
        if current_question_index < len(questions) - 1:
            current_question_index += 1
            show_question()

    def previous_question():
        global current_question_index
        if current_question_index > 0:
            current_question_index -= 1
            show_question()

    root = tk.Tk()
    root.title("Interview Assistant")
    root.geometry("800x600")

    paned_window = tk.PanedWindow(root, orient=tk.HORIZONTAL)
    paned_window.pack(fill=tk.BOTH, expand=True)

    left_frame = tk.Frame(paned_window, width=200)
    paned_window.add(left_frame)

    right_frame = tk.Frame(paned_window)
    paned_window.add(right_frame)

    question_listbox = tk.Listbox(left_frame)
    question_listbox.pack(fill=tk.BOTH, expand=True)

    button_frame = tk.Frame(left_frame)
    button_frame.pack(fill=tk.X)
    prev_button = tk.Button(button_frame, text="Previous", command=previous_question)
    next_button = tk.Button(button_frame, text="Next", command=next_question)
    prev_button.pack(side=tk.LEFT, padx=5, pady=5)
    next_button.pack(side=tk.LEFT, padx=5, pady=5)

    answer_text = tk.Text(right_frame, wrap="word", state=tk.DISABLED)
    answer_text.pack(fill=tk.BOTH, expand=True)
    answer_scrollbar = ttk.Scrollbar(right_frame, command=answer_text.yview)
    answer_text.config(yscrollcommand=answer_scrollbar.set)
    answer_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    root.after(1000, update_ui)  
    root.mainloop()

def capture_transcription():
    global current_question_index

    while True:
        transcription = get_otter_transcription()
        if transcription:
            print(f"Captured: {transcription}")

            if "?" in transcription:
                print("Question detected, sending to GPT...")

                with lock:
                    # Treat each instance of the question uniquely by appending it to the list
                    questions.append(transcription)
                    current_question_index = len(questions) - 1

                threading.Thread(target=fetch_answer_in_background, args=(transcription,)).start()
            else:
                print("No question detected.")
        time.sleep(10)

# Start capture transcription in a separate thread
threading.Thread(target=capture_transcription, daemon=True).start()

# Run UI on the main thread
ui_thread()
