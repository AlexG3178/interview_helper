import os
import wave
import tempfile
import openai
import pyaudio
import platform
import threading
import numpy as np
import tkinter as tk
import assemblyai as aai
from assemblyai import Transcriber
from config import config
from ui import InterviewAssistantUI

# API configurations
openai.api_key = config['api_key_openai']
aai.settings.api_key = config['api_key_assemblyai']

# Create a transcriber instance
transcriber = Transcriber()

# Audio configurations
CHUNK = 2048
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 48000

# Directory for temporary files
CUSTOM_TEMP_DIR = tempfile.gettempdir()


class InterviewAssistant:
    SYSTEM_SILENCE_THRESHOLD = 20
    MEETING_SILENCE_THRESHOLD = 20

    def __init__(self):
        self.qa_pairs = []  # Store (question, answer) pairs
        self.audio = pyaudio.PyAudio()

        # Initialize the UI
        self.root = tk.Tk()
        self.ui = InterviewAssistantUI(self.root, self.on_question_select, self.start_recording)

        self.transcribing = False
        self.recording_mode = "system_audio"

        self.root.mainloop()

    def start_recording(self, start=True):
        """Start or stop recording based on the current state."""
        if start:
            print("Start recording triggered")
            self.transcribing = True
            meeting_url = self.ui.url_entry.get().strip()

            if meeting_url:
                print(f"Connecting to meeting: {meeting_url}")
                threading.Thread(target=self.transcribe_meeting, args=(meeting_url,)).start()
            else:
                print("Recording system audio...")
                threading.Thread(target=self.transcribe_system_audio).start()
        else:
            print("Stop recording triggered")
            self.stop_recording()

    def stop_recording(self):
        """Stop the transcription process."""
        print("Stopping recording...")
        self.transcribing = False

    def transcribe_meeting(self, meeting_url):
        """Handle transcription for meeting audio."""
        print(f"Connecting to meeting URL: {meeting_url}")
        self.transcribing = True

        # Open PyAudio stream
        stream = self.audio.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=RATE,
            input=True,
            input_device_index=self.get_device_index(),
            frames_per_buffer=CHUNK
        )

        print("Starting transcription of meeting audio...")
        while self.transcribing:
            audio_data = self.capture_audio(stream)
            if audio_data:
                if not self.is_silent(audio_data, self.MEETING_SILENCE_THRESHOLD):
                    self.save_and_transcribe(audio_data)
                else:
                    print("Silence detected in meeting audio, skipping transcription.")

        stream.stop_stream()
        stream.close()
        print("Meeting transcription stopped.")

    def transcribe_system_audio(self):
        """Handle transcription for system audio."""
        print("Starting system audio transcription...")
        self.transcribing = True

        # Open PyAudio stream
        stream = self.audio.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=RATE,
            input=True,
            input_device_index=self.get_device_index(),
            frames_per_buffer=CHUNK
        )

        while self.transcribing:
            audio_data = self.capture_audio(stream)
            if audio_data and not self.is_silent(audio_data):
                self.save_and_transcribe(audio_data)
            else:
                print("Silence detected, skipping transcription.")

        stream.stop_stream()
        stream.close()

    def save_and_transcribe(self, audio_data):
        temp_audio_file = tempfile.NamedTemporaryFile(dir=CUSTOM_TEMP_DIR, delete=False, suffix=".wav")
        try:
            with wave.open(temp_audio_file.name, 'wb') as wf:
                wf.setnchannels(CHANNELS)
                wf.setsampwidth(self.audio.get_sample_size(FORMAT))
                wf.setframerate(RATE)
                wf.writeframes(audio_data)

            print(f"Audio file saved: {temp_audio_file.name}")

            transcription = self.transcribe_audio_file(temp_audio_file.name)
            if transcription:
                print(f"Transcription result: {transcription}")
                self.qa_pairs.append((transcription, "Answer pending..."))
                self.ui.populate_questions_and_answers(transcription, "Answer pending...")
                threading.Thread(target=self.generate_answer, args=(transcription,)).start()
            else:
                print("No transcription received.")
                self.qa_pairs.append(("Could not transcribe audio", "No answer available."))
                self.ui.populate_questions_and_answers("Could not transcribe audio", "No answer available.")
        except Exception as e:
            print(f"Error in save_and_transcribe: {e}")
        finally:
            try:
                temp_audio_file.close()
                os.unlink(temp_audio_file.name)
            except Exception as cleanup_error:
                print(f"Error cleaning up temporary file: {cleanup_error}")

    def capture_audio(self, stream):
        """Capture audio data from the stream."""
        try:
            frames = [stream.read(CHUNK, exception_on_overflow=False) for _ in range(0, int(RATE / CHUNK * 2))]
            return b''.join(frames)
        except OSError as e:
            print(f"Audio input error: {e}")
            return None

    def is_silent(self, audio_data, threshold=None):
        """Check if the audio data is silent based on amplitude and threshold."""
        threshold = threshold if threshold is not None else self.SYSTEM_SILENCE_THRESHOLD
        amplitude = np.frombuffer(audio_data, dtype=np.int16)
        rms = np.sqrt(np.mean(amplitude ** 2))
        print(f"RMS Value: {rms}, Threshold: {threshold}")
        return rms < threshold  # Return False if RMS > threshold

    def transcribe_audio_file(self, audio_file_path):
        """Send an audio file to AssemblyAI for transcription."""
        try:
            print(f"Sending file to AssemblyAI: {audio_file_path}")
            transcript = transcriber.transcribe(audio_file_path)
            if transcript and transcript.text:
                return transcript.text.strip()
            else:
                print(f"Transcription failed. Full response: {transcript}")
                return None
        except Exception as e:
            print(f"Error in transcribe_audio_file: {e}")
            return None

    def generate_answer(self, question):
        """Generate an answer using OpenAI's GPT API."""
        def update_ui_with_answer(answer):
            self.ui.populate_questions_and_answers(question, answer)

        try:
            print("Sending question to OpenAI:", question)
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": f"Answer the following question concisely: {question}"}
                ],
                max_tokens=150,
                request_timeout=30
            )
            print("Received response from OpenAI:", response)
            answer = response.choices[0].message['content'].strip()
        except Exception as e:
            print(f"Error in generate_answer: {e}")
            answer = "Error generating answer."

        # Safely update the UI
        self.root.after(0, update_ui_with_answer, answer)

    def get_device_index(self, device_name_windows="CABLE Output", device_name_mac="BlackHole"):
        """Find the correct audio input device."""
        target_device_name = device_name_windows if platform.system() == "Windows" else device_name_mac
        for i in range(self.audio.get_device_count()):
            info = self.audio.get_device_info_by_index(i)
            if target_device_name in info.get("name", ""):
                print(f"Found device '{target_device_name}' at index {i}")
                return i
        raise ValueError(f"Device '{target_device_name}' not found")

    def on_question_select(self, event):
        """Handle question selection and display the corresponding answer."""
        selected_question_index = self.ui.question_listbox.curselection()
        if selected_question_index:
            index = selected_question_index[0]
            question, answer = self.qa_pairs[index]
            self.ui.highlight_question(index)
            self.ui.display_answer(answer)


def main():
    InterviewAssistant()


if __name__ == "__main__":
    main()
