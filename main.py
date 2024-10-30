import tkinter as tk
from tkinter import ttk
import threading
import time
import openai
import pyaudio
import tempfile
import wave

from config import config
from ui import InterviewAssistantUI

openai.api_key = config['api_key']

# Audio configurations
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100

class InterviewAssistant:
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
            # Connect to meeting (implement if needed based on selenium)
            threading.Thread(target=self.transcribe_meeting, args=(meeting_url,)).start()
        else:
            print("Recording system audio...")
            threading.Thread(target=self.transcribe_system_audio).start()

    def transcribe_system_audio(self):
        print("Starting system audio transcription...")
        self.transcribing = True
        stream = self.audio.open(format=FORMAT, channels=CHANNELS,
                                 rate=RATE, input=True,
                                 frames_per_buffer=CHUNK)
        while self.transcribing:
            # Capture audio frames and combine them
            frames = [stream.read(CHUNK) for _ in range(0, int(RATE / CHUNK * 2))]
            audio_data = b''.join(frames)

            # Save audio data to a temporary file
            with tempfile.NamedTemporaryFile(delete=True, suffix=".wav") as temp_audio_file:
                with wave.open(temp_audio_file, 'wb') as wf:
                    wf.setnchannels(CHANNELS)
                    wf.setsampwidth(self.audio.get_sample_size(FORMAT))
                    wf.setframerate(RATE)
                    wf.writeframes(audio_data)

                # Transcribe the audio file using the Whisper API
                temp_audio_file.seek(0)  # Move to the beginning of the file
                transcription = self.transcribe_audio(temp_audio_file)

            if transcription:
                self.add_transcription_to_list(transcription)

        stream.stop_stream()
        stream.close()

    def add_transcription_to_list(self, transcription):
        """Adds each transcription result to the left listbox as a new item."""
        self.questions.append(transcription)
        self.ui.populate_questions(self.questions)

    def transcribe_meeting(self, meeting_url):
        # Placeholder for capturing audio from Google Meet
        print("Meeting transcription not yet implemented")

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