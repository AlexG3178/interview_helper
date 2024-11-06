import tkinter as tk
from tkinter import ttk
import threading
import time
import openai
import pyaudio
import tempfile
import wave
import numpy as np
from selenium import webdriver
from selenium.webdriver.common.by import By

from config import config
from ui import InterviewAssistantUI

openai.api_key = config['api_key']

# Audio configurations
CHUNK = 2048
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000

class InterviewAssistant:
    # Silence threshold for background noise filtering
    SYSTEM_SILENCE_THRESHOLD  = 20  
    MEETING_SILENCE_THRESHOLD = 25
    
    def __init__(self):
        self.questions = []
        self.answers = []
        self.audio = pyaudio.PyAudio()
        
        self.root = tk.Tk()
        self.ui = InterviewAssistantUI(self.root, self.on_question_select, self.start_recording)
        
        self.transcribing = False
        self.recording_mode = "system_audio"
        self.root.mainloop()

    def start_recording(self):
        print("Start recording function triggered")
        self.recording_mode = self.ui.recording_mode.get()
        meeting_url = self.ui.url_entry.get().strip()

        if self.recording_mode == "meeting_audio" and meeting_url:
            print("Connecting to meeting...")
            threading.Thread(target=self.transcribe_meeting, args=(meeting_url,)).start()
        else:
            print("Recording system audio...")
            threading.Thread(target=self.transcribe_system_audio).start()

    def capture_audio(self, stream):
        """Capture audio frames and return the combined audio data."""
        try:
            frames = [stream.read(CHUNK, exception_on_overflow=False) for _ in range(0, int(RATE / CHUNK * 2))]
            return b''.join(frames)
        except OSError as e:
            print(f"Audio input overflowed: {e}")
            return None

    def is_silent(self, audio_data, threshold=None):
        """Check if the audio data is silent based on the amplitude and given threshold."""
        threshold = threshold if threshold is not None else self.SYSTEM_SILENCE_THRESHOLD
        if audio_data:
            amplitude = np.frombuffer(audio_data, dtype=np.int16)
            rms = np.sqrt(np.mean(amplitude**2))
            return rms < threshold
        return True

    def transcribe_system_audio(self):
        print("Starting system audio transcription...")
        self.transcribing = True
        stream = self.audio.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)
        
        while self.transcribing:
            audio_data = self.capture_audio(stream)
            if audio_data and not self.is_silent(audio_data):
                self.save_and_transcribe(audio_data)
            else:
                print("Silence detected, skipping transcription")

        stream.stop_stream()
        stream.close()

    def save_and_transcribe(self, audio_data):
        """Save audio data to a temporary file and transcribe it."""
        with tempfile.NamedTemporaryFile(delete=True, suffix=".wav") as temp_audio_file:
            with wave.open(temp_audio_file, 'wb') as wf:
                wf.setnchannels(CHANNELS)
                wf.setsampwidth(self.audio.get_sample_size(FORMAT))
                wf.setframerate(RATE)
                wf.writeframes(audio_data)

            # Transcribe the audio file using the Whisper API
            temp_audio_file.seek(0)
            transcription = self.transcribe_audio(temp_audio_file)
        
        if transcription:
            self.add_transcription_to_list(transcription)

    def add_transcription_to_list(self, transcription):
        """Adds each transcription result to the left listbox as a new item."""
        self.questions.append(transcription)
        self.ui.populate_questions(self.questions)

    def transcribe_meeting(self, meeting_url):
        """Captures audio from a Google Meet session and transcribes it."""
        print("Joining Google Meet session...")
        options = webdriver.ChromeOptions()
        options.add_argument("--use-fake-ui-for-media-stream")  # Automatically allow mic permissions
        driver = webdriver.Chrome(config['chromedriver_path'], options=options)

        try:
            driver.get(meeting_url)
            time.sleep(5)  # Wait for the page to load

            # Find and click the 'Join' button (modify the XPath if necessary)
            join_button = driver.find_element(By.XPATH, "//span[contains(text(), 'Join now') or contains(text(), 'Ask to join')]")
            join_button.click()
            print("Joined the meeting")

            # Start audio capture for transcription
            self.transcribing = True
            audio_thread = threading.Thread(target=self.transcribe_audio_loopback)
            audio_thread.start()

            # Keep the browser open as long as transcription is running
            while self.transcribing:
                time.sleep(1)

        except Exception as e:
            print(f"Error in meeting transcription: {e}")
        finally:
            driver.quit()

    def transcribe_audio_loopback(self):
        """Capture audio from the system loopback and transcribe."""
        stream = self.audio.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)
        print("Starting loopback audio transcription...")

        while self.transcribing:
            try:
                frames = [stream.read(CHUNK, exception_on_overflow=False) for _ in range(0, int(RATE / CHUNK * 2))]
            except OSError as e:
                print(f"Audio input overflowed: {e}")
                continue

            audio_data = b''.join(frames)
            if not self.is_silent(audio_data, self.MEETING_SILENCE_THRESHOLD):
                with tempfile.NamedTemporaryFile(delete=True, suffix=".wav") as temp_audio_file:
                    with wave.open(temp_audio_file, 'wb') as wf:
                        wf.setnchannels(CHANNELS)
                        wf.setsampwidth(self.audio.get_sample_size(FORMAT))
                        wf.setframerate(RATE)
                        wf.writeframes(audio_data)

                    # Send the audio file to Whisper API for transcription
                    temp_audio_file.seek(0)
                    transcription = self.transcribe_audio(temp_audio_file)
                
                if transcription:
                    self.add_transcription_to_list(transcription)

        stream.stop_stream()
        stream.close()
        print("Loopback audio transcription stopped.")

    def transcribe_audio(self, file_obj):
        """Send audio file to OpenAI Whisper API for transcription."""
        try:
            response = openai.Audio.transcribe("whisper-1", file_obj)
            return response.get("text", "")
        except Exception as e:
            print(f"Transcription error: {e}")
        return ""

    def on_question_select(self, event):
        selected_question_index = self.ui.question_listbox.curselection()
        if selected_question_index:
            index = selected_question_index[0]
            answer = self.answers[index] if index < len(self.answers) else ""
            self.ui.display_answer(answer)
            
def main():
    InterviewAssistant()

if __name__ == "__main__":
    main()
