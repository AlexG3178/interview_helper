Interview Assistant.

Overview
This repository provides a real-time interview assistant application for transcribing audio and generating AI-driven responses. 
The project includes:
- Audio Transcription: Real-time transcription using Google Cloud Speech-to-Text with silence detection.
- AI-Powered Responses: Contextual and concise answers generated via OpenAI GPT-4.
- User Interface: A Tkinter-based GUI with synchronized panes for questions and answers.
- Real-Time Interaction: Automatic highlighting and scrolling for active questions and answers.

Features
- Dynamic Transcription: Captures and processes audio in real time with optimized silence handling.
- AI Integration: Generates relevant responses for transcribed questions.
- Interactive GUI: Provides split panes, auto-scroll, and easy controls for recording.
- Customizable Configurations: Adjustable thresholds, API keys, and audio settings.

Requirements
To run the project, the following libraries are required:
- PyAudio
- Pydub
- Google Cloud Speech-to-Text
- OpenAI API (GPT-4)
- Tkinter
- Numpy
