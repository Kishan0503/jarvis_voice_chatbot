from dotenv import load_dotenv
import google.generativeai as genai
import pyttsx3
import datetime
import speech_recognition as sr
import os
import platform


load_dotenv()

# Initialize TTS
# Choose driver based on OS
def get_driver_name():
    os_name = platform.system()
    if os_name == 'Windows':
        return 'sapi5'
    elif os_name == 'Darwin':  # macOS
        return 'nsss'
    else:  # Linux or others
        return 'espeak'

driver = get_driver_name()
engine=pyttsx3.init(driver)
voices=engine.getProperty('voices')
engine.setProperty('voice',voices[0].id)
    
def jarvisvoice(text):
    engine.say(text)
    engine.runAndWait()

def wish():
    hour = int(datetime.datetime.now().hour)
    greeting = "Good Morning sir" if 0 <= hour < 12 else "Good Afternoon sir" if 12 <= hour < 18 else "Good Evening sir"
    print(greeting)
    print("My name is Jarvis your personal voice assistant. What do you want to talk about today?")
    
    jarvisvoice(greeting)
    jarvisvoice("My name is Jarvis your personal voice assistant. What do you want to talk about today?")
    
def takecommand():
    recognizer = sr.Recognizer()
    mic_index = 3  # You can make this configurable or autodetect if needed
    
    for i, mic in enumerate(sr.Microphone.list_microphone_names()):
        print(f"{i}: {mic}")  # Optional: print available mics

    with sr.Microphone(device_index=mic_index) as source:
        print("Listening...")
        recognizer.adjust_for_ambient_noise(source, duration=0.5)  # helps with background noise
        recognizer.pause_threshold = 0.7  # reduced to respond faster

        try:
            audio = recognizer.listen(source, timeout=10, phrase_time_limit=10)
            print("Recognizing...")
            query = recognizer.recognize_google(audio, language='en-IN')
            print("You said:", query)
            return query
        
        except sr.WaitTimeoutError:
            print("No speech detected (timeout).")
            jarvisvoice("I didn't hear anything. Could you please repeat?")
        
        except sr.UnknownValueError:
            print("Could not understand the audio.")
        
        except sr.RequestError as e:
            print(f"Could not request results from Google Speech Recognition service; {e}")
            jarvisvoice("I'm having trouble connecting to the recognition service.")
        
        except Exception as e:
            print(f"Unexpected error: {e}")
            jarvisvoice("Something went wrong.")
            exit(1)

        return None

# Initialize Model
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-2.0-flash')

# Simulate system instruction by setting it as the first user message
initial_instruction = (
    "From now on, respond like a thoughtful and emotionally intelligent person."
    "Reply to any user input using natural, conversational language in a single small paragraph."
    "Express emotions and human behavior where appropriate."
    "Avoid technical language, special formatting, or keywords."
)

# Start the chat with that context in the history
chat = model.start_chat(history=[
    {
        "role": "user",
        "parts": [initial_instruction]
    }
])

# Function to send user input to model
def generate_reply(user_input):
    response = chat.send_message(user_input)
    print(f"Reply : {response.text} \n")
    return response.text

                      
# Starts from Here
wish()
while True:
    query = takecommand()
    if query:
        query=query.lower()

        if "bye" in query or "stop" in query or "exit" in query:
            print("Okay! Have a great day, Bye Bye")
            jarvisvoice("Okay! Have a great day, Bye Bye")
            break
        
        else:
            response = generate_reply(query)
            jarvisvoice(response)