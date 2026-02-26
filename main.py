import os
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from auth.auth_routes import router as auth_router
from auth.auth_utils import get_current_user
from auth.auth_models import TokenData
from gemini_client import gemini_client
from tools.elevenlabs_tts import text_to_speech_stream

app = FastAPI()

# Allow CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Replace with actual domain later
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for frontend
app.mount("/static", StaticFiles(directory="frontend"), name="static")

# Include authentication routes
app.include_router(auth_router, prefix="/auth", tags=["authentication"])

# Serve index.html at root path
@app.get("/")
async def serve_index():
    return FileResponse(os.path.join("frontend", "index.html"))

# Define the request body model
class ChatRequest(BaseModel):
    message: str
    agent: str  # 'jarvis' or 'zara'


class TTSRequest(BaseModel):
    text: str
    agent: str  # 'jarvis' or 'zara'


@app.post("/chat")
async def chat_response(req: ChatRequest, current_user: TokenData = Depends(get_current_user)):
    try:
        reply = await gemini_client.send_message_to_gemini(
            req.message, agent=req.agent, user_email=current_user.email
        )
        return JSONResponse(content={"reply": reply})

    except Exception as e:
        print(f"Error in FastAPI chat_response endpoint: {e}")
        error_msg = (
            "I do apologize, Sir/Madam, but I encountered an error. Might we try again?"
            if req.agent.lower() == "jarvis"
            else "Oh no! I ran into a problem. Let's try that again!"
        )
        return JSONResponse(
            content={"reply": error_msg}, 
            status_code=500
        )


@app.post("/tts")
async def text_to_speech(req: TTSRequest, current_user: TokenData = Depends(get_current_user)):
    try:
        audio_stream = text_to_speech_stream(req.text, req.agent)
        return StreamingResponse(audio_stream, media_type="audio/mpeg")
    except Exception as e:
        print(f"Error in /tts endpoint: {e}")
        return JSONResponse(content={"detail": "Failed to generate speech audio."}, status_code=500)