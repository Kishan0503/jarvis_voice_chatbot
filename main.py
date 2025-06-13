from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs
from elevenlabs import play

import google.generativeai as genai
import pyttsx3
import datetime
import speech_recognition as sr
import os
# import threading

load_dotenv()


# Initialize TTS
# engine=pyttsx3.init('sapi5')
# voices=engine.getProperty('voices')
# engine.setProperty('voice',voices[0].id)

# Initialize Model
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-2.0-flash')

# Initializing TTS
client = ElevenLabs(api_key=os.getenv("ELEVEN_LAB_API_KEY"))
# voices = client.voices.get_all()
# for voice in voices.voices:
#     print(f"{voice.name}: {voice.voice_id}")

# def speak_async(text):
#     def speak():
#         engine.say(text)
#         engine.runAndWait()

#     thread = threading.Thread(target=speak)
#     thread.start()
    
def jarvisvoice(text):
    # engine.say(audio)
    # engine.runAndWait()
    audio = client.text_to_speech.convert(
        text=text,
        voice_id="29vD33N1CtxCmqQRPOHJ",
        model_id="eleven_monolingual_v1",
        optimize_streaming_latency=1  # Optional: lower = faster but less natural
    )
    play(audio)

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
            # speak_async("I didn't hear anything.")
        
        except sr.UnknownValueError:
            print("Could not understand the audio.")
            # speak_async("Sorry, Say that again please.")
        
        except sr.RequestError as e:
            print(f"Could not request results from Google Speech Recognition service; {e}")
            jarvisvoice("I'm having trouble connecting to the recognition service.")
        
        except Exception as e:
            print(f"Unexpected error: {e}")
            jarvisvoice("Something went wrong.")
            exit(1)

        return None

def generate_reply(user_input):
    response = model.generate_content(f"{user_input}, generate response in human like talks, include words which contains emotions and behavior as well, provide the response in simple paragraph, do not include any special keywords or styling words")
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

