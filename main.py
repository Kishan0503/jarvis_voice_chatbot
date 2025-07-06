import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel # Keep BaseModel for request body validation

# NEW: Import the gemini_client instance
from gemini_client import gemini_client

app = FastAPI()

# Allow CORS for frontend (adjust origin for production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Replace with actual domain later
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for frontend
app.mount("/static", StaticFiles(directory="frontend"), name="static")

# Serve index.html at root path
@app.get("/")
async def serve_index():
    return FileResponse(os.path.join("frontend", "index.html"))

# Define the request body model
class ChatRequest(BaseModel):
    message: str

@app.post("/chat")
async def chat_response(req: ChatRequest):
    try:
        # NEW: Use the gemini_client to send the message and get the reply
        reply = await gemini_client.send_message_to_gemini(req.message)
        return JSONResponse(content={"reply": reply})

    except Exception as e:
        print(f"Error in FastAPI chat_response endpoint: {e}")
        return JSONResponse(content={"reply": "Oops! Jarvis encountered an error. Please try again later."}, status_code=500)