import os
import wave
import time
import openai
import pyaudio
import tempfile
import threading
import numpy as np
import tkinter as tk
from tkinter import ttk
import assemblyai as aai
from selenium import webdriver
import undetected_chromedriver as uc
from assemblyai import Transcriber
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
 
from config import config
from ui import InterviewAssistantUI

# API configurations
openai.api_key = config['api_key_openai']
aai.settings.api_key = config['api_key_assemblyai']

# Audio configurations
CHUNK = 2048
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000

# Custom directory for temporary files
CUSTOM_TEMP_DIR = "C:\\custom_temp"
os.makedirs(CUSTOM_TEMP_DIR, exist_ok=True)  # Ensure the directory exists


class InterviewAssistant:
    SYSTEM_SILENCE_THRESHOLD = 20
    MEETING_SILENCE_THRESHOLD = 20

    def __init__(self):
        self.questions = []
        self.answers = []
        self.audio = pyaudio.PyAudio()

        self.root = tk.Tk()
        self.ui = InterviewAssistantUI(self.root, self.on_question_select, self.start_recording)

        self.transcribing = False
        self.transcriber = None
        self.recording_mode = "system_audio"

        self.root.mainloop()

    def start_recording(self):
        """Handle UI button press to start recording."""
        print("Start recording function triggered")
        self.recording_mode = self.ui.recording_mode.get()
        meeting_url = self.ui.url_entry.get().strip()

        if self.recording_mode == "meeting_audio" and meeting_url:
            print("Connecting to meeting...")
            threading.Thread(target=self.transcribe_meeting, args=(meeting_url,)).start()
        else:
            print("Recording system audio...")
            threading.Thread(target=self.transcribe_system_audio).start()

    def transcribe_system_audio(self):
        """Start transcription of system audio using file-based transcription."""
        print("Starting system audio transcription...")
        self.transcribing = True
        stream = self.audio.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)

        while self.transcribing:
            audio_data = self.capture_audio(stream)
            if audio_data and not self.is_silent(audio_data):
                self.save_and_transcribe(audio_data)
            else:
                print("Silence detected, skipping transcription.")

        stream.stop_stream()
        stream.close()

    def save_and_transcribe(self, audio_data):
        """Save audio data to a temporary file and transcribe it."""
        temp_audio_file = tempfile.NamedTemporaryFile(dir=CUSTOM_TEMP_DIR, delete=False, suffix=".wav")  # Custom temp directory
        # print(f"Created temporary file: {temp_audio_file.name}")
        try:
            with wave.open(temp_audio_file.name, 'wb') as wf:
                wf.setnchannels(CHANNELS)
                wf.setsampwidth(self.audio.get_sample_size(FORMAT))
                wf.setframerate(RATE)
                wf.writeframes(audio_data)

            # Transcribe the audio
            transcription = self.transcribe_audio_file(temp_audio_file.name)
            if transcription:
                self.questions.append(transcription)
                self.ui.populate_questions(self.questions)

                # Generate an answer for the question
                threading.Thread(target=self.generate_answer, args=(transcription,)).start()
        except Exception as e:
            print(f"Transcription error: {e}")
        finally:
            # Explicitly delete the file after use
            try:
                temp_audio_file.close()
                os.unlink(temp_audio_file.name)  # Cleanup temp file
                # print(f"Deleted temporary file: {temp_audio_file.name}")
            except Exception as cleanup_error:
                print(f"Error cleaning up temporary file: {cleanup_error}")

    def capture_audio(self, stream):
        """Capture audio frames and return the combined audio data."""
        try:
            frames = [stream.read(CHUNK, exception_on_overflow=False) for _ in range(0, int(RATE / CHUNK * 2))]
            return b''.join(frames)
        except OSError as e:
            print(f"Audio input overflowed: {e}")
            return None

    def is_silent(self, audio_data, threshold=None):
        """Check if the audio data is silent based on amplitude and threshold."""
        threshold = threshold if threshold is not None else self.SYSTEM_SILENCE_THRESHOLD
        if audio_data:
            amplitude = np.frombuffer(audio_data, dtype=np.int16)
            rms = np.sqrt(np.mean(amplitude**2))
            return rms < threshold
        return True

    def transcribe_audio_file(self, audio_file_path):
        """Transcribes an audio file using AssemblyAI's file-based API."""
        try:
            transcriber = Transcriber()  # AssemblyAI file-based transcription
            transcript = transcriber.transcribe(audio_file_path)
            print("Full Transcript:", transcript.text)
            return transcript.text
        except Exception as e:
            print(f"Transcription error: {e}")
            return f"Error: {e}"
        
    def transcribe_meeting(self, meeting_url):
        """Capture audio from a Google Meet session and transcribe."""
        print("Joining Google Meet session...")

        # Initialize undetected Chrome
        options = uc.ChromeOptions()
        options.add_argument("--use-fake-ui-for-media-stream")  # Automatically allow mic permissions
        options.add_argument("C:\\Users\\Maut\\AppData\\Local\\Google\\Chrome\\User Data")  # Keep logged in session

        driver = uc.Chrome(options=options)  # Initialize undetected ChromeDriver

        try:
            driver.get(meeting_url)
            # Wait for the "Join" button to appear
            wait = WebDriverWait(driver, 60)
            join_button = wait.until(EC.element_to_be_clickable(
                (By.XPATH, "//span[contains(text(), 'Join now') or contains(text(), 'Ask to join')]")
            ))
            join_button.click()
            print("Joined the meeting")

            self.transcribing = True
            threading.Thread(target=self.transcribe_audio_loopback).start()

            while self.transcribing:
                time.sleep(1)
        except Exception as e:
            print(f"Error in meeting transcription: {e}")
        finally:
            driver.quit()
            

    def transcribe_audio_loopback(self):
        """Capture audio from system loopback and transcribe."""
        stream = self.audio.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)
        print("Starting loopback audio transcription...")

        while self.transcribing:
            audio_data = self.capture_audio(stream)
            if audio_data and not self.is_silent(audio_data, self.MEETING_SILENCE_THRESHOLD):
                self.save_and_transcribe(audio_data)
            else:
                print("Silence detected.")

        stream.stop_stream()
        stream.close()
        print("Loopback audio transcription stopped.")

    def generate_answer(self, question):
        """Generate an answer using OpenAI's GPT-4 model."""
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4",  # Explicitly use GPT-4
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": f"Answer the following question concisely: {question}"}
                ],
                max_tokens=150
            )
            answer = response.choices[0].message['content'].strip()
            print("Generated Answer:", answer)
            self.answers.append(answer)
            self.ui.display_answer(answer)
        except Exception as e:
            print(f"Error generating answer: {e}")
            self.answers.append("Error generating answer.")
            self.ui.display_answer("Error generating answer.")

    def on_question_select(self, event):
        """Handle selection of a question from the UI."""
        selected_question_index = self.ui.question_listbox.curselection()
        if selected_question_index:
            index = selected_question_index[0]
            answer = self.answers[index] if index < len(self.answers) else ""
            self.ui.display_answer(answer)


def main():
    InterviewAssistant()


if __name__ == "__main__":
    main()