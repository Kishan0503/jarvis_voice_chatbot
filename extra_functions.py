def jarvisvoice(text):
    """
    This function uses Eleven Labs API key to generate text to Audio,
    This we can use if we want to make different voices for our voice agent
    """
    from elevenlabs.client import ElevenLabs
    from elevenlabs import play

    import os
    client = ElevenLabs(api_key=os.getenv("ELEVEN_LAB_API_KEY"))
    
    audio = client.text_to_speech.convert(
        text=text,
        voice_id="29vD33N1CtxCmqQRPOHJ",
        model_id="eleven_monolingual_v1",
        optimize_streaming_latency=1  # Optional: lower = faster but less natural
    )
    play(audio)

def speak_async(text):
    """
    This function can be use to make our voice assistant speak asyncronisly
    """
    import pyttsx3
    import threading
    
    engine=pyttsx3.init('sapi5')
    def speak():
        engine.say(text)
        engine.runAndWait()

    thread = threading.Thread(target=speak)
    thread.start()