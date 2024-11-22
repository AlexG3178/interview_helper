import os

config = {
    'api_key_openai': os.getenv('OPENAI_API_KEY', ''),
    'google_service_account_key': '/Users/alexandrgrigoriev/Documents/Projects/interview_helper/nth-celerity-442111-f4-ad0229c215b1.json',
    'SILENCE_THRESHOLD': 20,
    'CAPTURING_INTERVAL': 0.5,
    'SILENCE_PAUSE_DURATION': 0.5,
    'CHUNK': 2048,
    'CHANNELS': 1,
    'RATE': 48000
}