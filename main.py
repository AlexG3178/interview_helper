import time
import openai
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

from config import config 

openai.api_key = config['api_key']

chrome_options = Options()
#macOS
# chrome_options.add_argument("--user-data-dir=/Users/alexandrgrigoriev/Library/Application\\ Support/Google/Chrome")
#Windows
chrome_options.add_argument("--user-data-dir=C:\\Users\\Maut\\AppData\\Local\\Google\\Chrome")

chrome_options.add_argument("--profile-directory=Profile 1")  # Use the correct profile name
chrome_options.add_argument("--disable-dev-shm-usage")  # Overcome limited resource problems
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--no-sandbox")  # Bypass OS security model
chrome_options.add_argument("--disable-software-rasterizer")

driver = uc.Chrome(options=chrome_options) 

# Function to extract transcription from Otter.ai live session
def get_otter_transcription():
    try:
        driver.get(config['session_url'])  # Open the Otter.ai live session
        time.sleep(5)  # Let the page load completely
        # Locate all transcription elements on the page using the specified XPath
        transcription_elements = driver.find_elements(By.XPATH, config['message_container_path'])
        
        # Combine text from all found transcription elements
        combined_text = " ".join([element.text for element in transcription_elements])
        return combined_text
    except Exception as e:
        print(f"Error accessing Otter.ai: {e}")
        return None

# Function to send the text to OpenAI GPT and get a response
def get_gpt_response(question):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",  # Specify the model (e.g., gpt-4)
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

if __name__ == "__main__":
    while True:
        transcription = get_otter_transcription()
        if transcription:
            print(f"Captured: {transcription}")
            # Process to identify if the text is a question
            if "?" in transcription:  # Basic check for question
                print("Question detected, sending to GPT...")
                gpt_response = get_gpt_response(transcription)
                if gpt_response:
                    print(f"GPT Response: {gpt_response}")
                    # Here, you can add code to display it on a separate screen or save it.
        time.sleep(60)  