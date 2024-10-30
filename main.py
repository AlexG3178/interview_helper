import tkinter as tk
from tkinter import ttk
import threading
import time
import openai
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

from config import config 
from ui import InterviewAssistantUI

openai.api_key = config['api_key']

chrome_options = Options()
#macOS
# chrome_options.add_argument("--user-data-dir=/Users/alexandrgrigoriev/Library/Application\\ Support/Google/Chrome")
#Windows
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
auto_scroll = True
lock = threading.Lock()

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

def get_gpt_response(question):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "system", "content": "You are a helpful assistant."},
                      {"role": "user", "content": question}],
            max_tokens=100,
            temperature=0.5,
        )
        return response.choices[0].message['content'].strip()
    except Exception as e:
        print(f"Error querying GPT: {e}")
        return None

def on_question_select(event):
    global current_question_index, auto_scroll
    selection = app_ui.question_listbox.curselection()
    if selection:
        current_question_index = selection[0]
        auto_scroll = (current_question_index == len(questions) - 1)
        update_ui()

def previous_question():
    global current_question_index
    if current_question_index > 0:
        current_question_index -= 1
        update_ui()

def next_question():
    global current_question_index
    if current_question_index < len(questions) - 1:
        current_question_index += 1
        update_ui()

def update_ui():
    app_ui.update_question_list(questions, current_question_index, auto_scroll)
    app_ui.update_answer_text(answers, current_question_index, auto_scroll)

def fetch_answer_in_background(question):
    answer = get_gpt_response(question)
    if answer:
        with lock:
            answers.append(answer)
        app_ui.root.after(0, update_ui)

def capture_transcription():
    global current_question_index
    while True:
        transcription = get_otter_transcription()
        if transcription and "?" in transcription:
            with lock:
                questions.append(transcription)
                current_question_index = len(questions) - 1
            app_ui.root.after(0, update_ui)
            threading.Thread(target=fetch_answer_in_background, args=(transcription,)).start()
        time.sleep(config['sleep_time'])

root = tk.Tk()
app_ui = InterviewAssistantUI(root, on_question_select, previous_question, next_question)
threading.Thread(target=capture_transcription, daemon=True).start()
root.mainloop()