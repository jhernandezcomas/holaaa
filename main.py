import asyncio
import os
import threading
from pathlib import Path
from typing import Optional

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

load_dotenv()

from src.audio import AudioCapture
from src.transcriber import Transcriber
from src.assistant import InterviewAssistant

app = FastAPI(title="Zoom Interview Assistant")

# ── Global state ─────────────────────────────────────────────────────────────
_clients: list[WebSocket] = []
_audio: Optional[AudioCapture] = None
_transcriber: Optional[Transcriber] = None
_assistant: Optional[InterviewAssistant] = None
_running = False
_event_loop: Optional[asyncio.AbstractEventLoop] = None


# ── Routes ───────────────────────────────────────────────────────────────────
@app.get("/")
async def index():
    return HTMLResponse(Path("src/ui/index.html").read_text(encoding="utf-8"))


@app.get("/api/devices")
async def list_devices():
    devices = AudioCapture.list_devices()
    # Highlight monitor sources (Linux PulseAudio loopback for speaker audio)
    input_devices = [d for d in devices if d["input_channels"] > 0]
    return {"devices": input_devices}


@app.post("/api/start")
async def start(device_id: Optional[int] = None):
    global _audio, _transcriber, _assistant, _running, _event_loop

    if _running:
        return {"status": "already_running"}

    _event_loop = asyncio.get_event_loop()
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        return {"status": "error", "message": "ANTHROPIC_API_KEY no encontrada en .env"}

    whisper_model = os.getenv("WHISPER_MODEL", "base")
    chunk_dur = float(os.getenv("AUDIO_CHUNK_DURATION", "3"))

    _assistant = InterviewAssistant(profile_path="profile.md", api_key=api_key)
    _transcriber = Transcriber(model_size=whisper_model)
    _audio = AudioCapture(device=device_id, chunk_duration=chunk_dur)

    _running = True
    threading.Thread(target=_pipeline_loop, daemon=True).start()
    return {"status": "started"}


@app.post("/api/stop")
async def stop():
    global _running, _audio
    _running = False
    if _audio:
        _audio.stop()
    return {"status": "stopped"}


@app.post("/api/reset")
async def reset():
    if _assistant:
        _assistant.reset()
    return {"status": "reset"}


@app.websocket("/ws")
async def ws_endpoint(websocket: WebSocket):
    await websocket.accept()
    _clients.append(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        if websocket in _clients:
            _clients.remove(websocket)


# ── Pipeline ─────────────────────────────────────────────────────────────────
def _pipeline_loop():
    silence_threshold = int(os.getenv("SILENCE_THRESHOLD", "2"))
    _audio.start()

    pending_texts: list[str] = []
    silent_chunks = 0

    while _running:
        chunk = _audio.get_chunk(timeout=1.0)

        if chunk is None:
            silent_chunks += 1
        else:
            rms = AudioCapture.rms(chunk)

            if rms < 0.005:
                silent_chunks += 1
            else:
                text = _transcriber.transcribe(chunk)
                if text:
                    silent_chunks = 0
                    pending_texts.append(text)
                    _broadcast_sync({"type": "live", "text": text})
                else:
                    silent_chunks += 1

        # After enough silence, flush accumulated text to Claude
        if pending_texts and silent_chunks >= silence_threshold:
            full_text = " ".join(pending_texts)
            pending_texts.clear()
            silent_chunks = 0
            _process_text(full_text)


def _process_text(text: str):
    result = _assistant.process(text)
    if result:
        _broadcast_sync({"type": "analysis", "data": result})


def _broadcast_sync(data: dict):
    if _event_loop and _clients:
        asyncio.run_coroutine_threadsafe(_broadcast(data), _event_loop)


async def _broadcast(data: dict):
    dead = []
    for client in _clients:
        try:
            await client.send_json(data)
        except Exception:
            dead.append(client)
    for c in dead:
        if c in _clients:
            _clients.remove(c)


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 55)
    print("  Zoom Interview Assistant")
    print("  Abre tu navegador en: http://localhost:8000")
    print("=" * 55)
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="warning")
