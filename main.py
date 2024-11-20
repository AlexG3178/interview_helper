import os
import io
import openai
import pyaudio
import platform
import tempfile
import threading
import logging
import numpy as np
import tkinter as tk
from google.cloud import speech
from pydub import AudioSegment, effects
from config import config
from ui import InterviewAssistantUI

openai.api_key = config['api_key_openai']

FORMAT = pyaudio.paInt16
CHUNK = config['CHUNK']
CHANNELS = config['CHANNELS']
RATE = config['RATE'] # Match Voicemeeter's sample rate

CUSTOM_TEMP_DIR = "C:\\custom_temp"
os.makedirs(CUSTOM_TEMP_DIR, exist_ok=True)  # Ensure the directory exists



class InterviewAssistant:
    MIN_SILENCE_THRESHOLD = config['MIN_SILENCE_THRESHOLD']
 
    def __init__(self):
        self.questions = []
        self.answers = []
        self.audio = pyaudio.PyAudio()
        self.selected_index = None
        self.root = tk.Tk()
        self.ui = InterviewAssistantUI(self.root, self.on_question_select, self.start_recording)
        self.transcribing = False
        self.calibrate_silence_threshold()
         # Google Cloud Speech client setup
        self.speech_client = speech.SpeechClient.from_service_account_json(config['google_service_account_key'])
        self.root.mainloop()
        
        
    def calibrate_silence_threshold(self):
        print("Calibrating silence threshold...")
        stream = self.audio.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=RATE,
            input=True,
            frames_per_buffer=CHUNK
        )
        noise_samples = [
            np.sqrt(np.mean(np.frombuffer(stream.read(CHUNK), dtype=np.int16) ** 2))
            for _ in range(10)
        ]
        stream.stop_stream()
        stream.close()
        self.SILENCE_THRESHOLD = max(np.mean(noise_samples) * 1.5, config['MIN_SILENCE_THRESHOLD'])
        print(f"Silence threshold set to: {self.SILENCE_THRESHOLD}")


    def start_recording(self, start=True):
        if start:
            print("Start logging")
            self.transcribing = True   
            threading.Thread(target=self.transcribe_meeting).start()
        else:
            print("Recording stopped")
            self.stop_recording()
 
 
    def stop_recording(self):
        print("Stop recording")
        self.transcribing = False
 
 
    def transcribe_meeting(self):
        self.transcribing = True

        stream = self.audio.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=RATE,
            input=True,
            input_device_index=self.get_device_index(),
            frames_per_buffer=CHUNK
        )

        audio_buffer = b""  # Accumulate audio data here

        try:
            while self.transcribing:
                audio_data = self.capture_audio(stream)
                if audio_data:
                    if not self.is_silent(audio_data, self.SILENCE_THRESHOLD):
                        # Add audio data to buffer
                        audio_buffer += audio_data
                    else:
                        # If silence detected and buffer has audio, process it
                        if len(audio_buffer) > 0:
                            print("Pause detected, processing audio segment...")
                            self.save_and_transcribe(audio_buffer)
                            audio_buffer = b""  # Reset the buffer
                else:
                    print("No audio data captured.")
        finally:
            stream.stop_stream()
            stream.close()
            print("Meeting transcription stopped.")


    def save_and_transcribe(self, audio_buffer):
        """Save the accumulated audio buffer to a file and transcribe it."""
        temp_audio_file = tempfile.NamedTemporaryFile(dir=CUSTOM_TEMP_DIR, delete=False, suffix=".wav")
        try:
            audio_segment = AudioSegment(
                data=audio_buffer,
                sample_width=self.audio.get_sample_size(FORMAT),
                frame_rate=RATE,
                channels=CHANNELS
            )
            audio_segment.export(temp_audio_file.name, format="wav", codec="pcm_s16le")
            
            # Transcribe the saved audio file
            transcription = self.transcribe_audio_file(temp_audio_file.name)
            if transcription:
                self.questions.append(transcription)
                threading.Thread(target=self.generate_answer, args=(transcription,)).start()
        except Exception as e:
            print(f"Error processing audio buffer: {e}")
        finally:
            try:
                temp_audio_file.close()
                os.unlink(temp_audio_file.name)
            except Exception as cleanup_error:
                print(f"Error cleaning up temporary file: {cleanup_error}")


    def preprocess_audio(self, audio_data):
        audio_segment = AudioSegment(
            data=audio_data,
            sample_width=self.audio.get_sample_size(FORMAT),
            frame_rate=RATE,
            channels=CHANNELS
        )
        normalized_audio = effects.normalize(audio_segment)
        mono_audio = normalized_audio.set_channels(1)  # Convert to mono
        return mono_audio.raw_data


    def capture_audio(self, stream):
        """Capture audio frames, preprocess, and return the combined audio data."""
        try:
            frames = [stream.read(CHUNK, exception_on_overflow=False) for _ in range(0, int(RATE / CHUNK * 2))]
            raw_audio = b''.join(frames)
            processed_audio = self.preprocess_audio(raw_audio)
            return processed_audio
        except OSError as e:
            print(f"Audio input overflowed: {e}")
            return None


    def is_silent(self, audio_data, threshold=None):
        """Check if the audio data is silent based on amplitude and threshold."""
        if audio_data:
            amplitude = np.frombuffer(audio_data, dtype=np.int16)
            rms = np.sqrt(np.mean(amplitude ** 2))
            print(f"RMS Value: {rms}, Threshold: {threshold}")
            return rms < (threshold or self.SILENCE_THRESHOLD)
        return True


    def transcribe_audio_file(self, audio_file_path):
        """Transcribe an audio file using Google Speech-to-Text."""
        try:
            with io.open(audio_file_path, "rb") as audio_file:
                content = audio_file.read()

            audio = speech.RecognitionAudio(content=content)
            config = speech.RecognitionConfig(
                encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
                sample_rate_hertz=RATE,
                language_code="en-US",
            )

            response = self.speech_client.recognize(config=config, audio=audio)

            # Extract transcription
            transcript = " ".join([result.alternatives[0].transcript for result in response.results])
            print("Transcript:", transcript)
            return transcript

        except Exception as e:
            print(f"Google Speech-to-Text error: {e}")
            return f"Error: {e}"


    def generate_answer(self, question):
        """Generate an answer using OpenAI's GPT-4 model."""
        try:
            # response = openai.ChatCompletion.create(
            #     model="gpt-4",
            #     messages=[
            #         {"role": "system", "content": "You are a helpful assistant."},
            #         {"role": "user", "content": f"Answer the following question concisely: {question}"}
            #     ],
            #     max_tokens=150
            # )
            # answer = response.choices[0].message['content'].strip()
            answer = "Mock answer Mock answer Mock answer Mock answer Mock answer Mock answer Mock answer Mock answer Mock answer Mock answer Mock answer Mock answer Mock answer Mock answer Mock answer Mock answer Mock answer Mock answer Mock answer Mock answer Mock answer Mock answer Mock answer Mock answer Mock answer Mock answer Mock answer Mock answer Mock answer Mock answer Mock answer Mock answer Mock answer Mock answer Mock answer Mock answer Mock answer Mock answer Mock answer Mock answer Mock answer Mock answer Mock answer Mock answer Mock answer Mock answer Mock answer Mock answer Mock answer Mock answer Mock answer Mock answer Mock answer Mock answer Mock answer Mock answer Mock answer Mock answer Mock answer Mock answer Mock answer Mock answer Mock answer Mock answer Mock answer Mock answer Mock answer Mock answer Mock answer Mock answer Mock answer Mock answer Mock answer Mock answer Mock answer Mock answer Mock answer Mock answer Mock answer Mock answer Mock answer Mock answer Mock answer Mock answer Mock answer Mock answer Mock answer Mock answer Mock answer Mock answer Mock answer Mock answer Mock answer Mock answer Mock answer Mock answer Mock answer Mock answer Mock answer Mock answer Mock answer Mock answer Mock answer Mock answer Mock answer Mock answer Mock answer Mock answer Mock answer Mock answer Mock answer Mock answer Mock answer Mock answer Mock answer Mock answer Mock answer Mock answer Mock answer Mock answer Mock answer Mock answer Mock answer Mock answer Mock answer Mock answer Mock answer Mock answer Mock answer ."

            # Add the answer and refresh the UI
            self.answers.append(answer)

            # Ensure custom selection is respected
            if self.selected_index is not None and self.selected_index < len(self.questions):
                # Keep the current selection and do not auto-select the last question
                self.root.after(0, self.populate_questions_and_answers)
            else:
                # Auto-select the last question
                self.selected_index = len(self.questions) - 1
                self.root.after(0, self.populate_questions_and_answers)
        except Exception as e:
            print(f"Error generating answer: {e}")
            self.answers.append("Error generating answer.")
            self.root.after(0, self.populate_questions_and_answers)


    def populate_questions_and_answers(self):
        """Update the UI to display all questions and answers."""
        self.ui.question_listbox.delete(0, tk.END)
        self.ui.answer_text.delete(1.0, tk.END)

        # Populate questions in the listbox
        for question in self.questions:
            self.ui.question_listbox.insert(tk.END, question)

        # Populate answers in the text widget
        for answer in self.answers:
            self.ui.answer_text.insert(tk.END, f"{answer}\n\n")

        # Detect if the last question is currently selected
        is_last_selected = (
            self.selected_index is not None
            and self.selected_index == len(self.questions) - 2  # Check the second-to-last before appending
        )

        # Handle selection logic
        if is_last_selected:
            # Move selection to the new last question
            self.selected_index = len(self.questions) - 1
        elif self.selected_index is None:
            # Default to selecting the last question if no selection exists
            self.selected_index = len(self.questions) - 1

        # Apply the selection to the UI
        self.ui.question_listbox.selection_clear(0, tk.END)
        self.ui.question_listbox.selection_set(self.selected_index)
        self.ui.question_listbox.activate(self.selected_index)
        self.ui.highlight_answer(self.selected_index, self.answers)

        # Scroll behavior
        if is_last_selected:
            self.ui.scroll_to_end()
        else:
            self.ui.scroll_to_question(self.selected_index)
            

    def get_device_index(self, device_name_windows="CABLE Output", device_name_mac="BlackHole"):
        target_device_name = device_name_windows if platform.system() == "Windows" else device_name_mac
        indices = [i for i in range(self.audio.get_device_count())
                   if target_device_name in self.audio.get_device_info_by_index(i).get("name", "")]
        if indices:
            print(f"Using device '{target_device_name}' at index {indices[0]}")
            return indices[0]
        raise ValueError(f"Device '{target_device_name}' not found")

 
    def on_question_select(self, event):
        """Handle selection of a question from the UI."""
        selected_question_index = self.ui.question_listbox.curselection()
        if selected_question_index:
            self.selected_index = selected_question_index[0]
            self.ui.highlight_answer(self.selected_index, self.answers)


def main():
   InterviewAssistant()


if __name__ == "__main__":
   main()
