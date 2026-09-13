"""
VieNeu-TTS v3 Turbo — API server để mentor gọi tổng hợp giọng nói tiếng Việt.
"""
import base64
import io
import os
import re
import tempfile
from typing import Optional

import librosa #là một thư viện Python dùng để xử lý tín hiệu âm thanh và âm nhạc
import numpy as np
import soundfile as sf
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from vieneu import Vieneu

# ---- Cấu hình ----
SAMPLE_RATE = 48000  # VieNeu-TTS v3 Turbo sinh audio 48kHz
DEFAULT_REF_AUDIO = os.path.join(os.path.dirname(__file__), "ref_audio.wav")
MAX_CHARS = 3600  # chặn request quá dài làm server bị treo lâu
CHUNK_MAX_CHARS = 200  # độ dài tối đa mỗi câu/chunk đưa vào model 1 lần
SILENCE_GAP_SEC = 0.25  # khoảng lặng chèn giữa các chunk khi ghép
TRIM_TOP_DB = 30  # ngưỡng coi là "im lặng" khi trim (dB dưới đỉnh biên độ)

app = FastAPI(title="VieNeu-TTS v3 Turbo API", version="1.0")
_tts = Vieneu(mode="v3turbo")

def split_into_chunks(text: str, max_chars: int = CHUNK_MAX_CHARS) -> list[str]:
    """Cắt văn bản thành các câu, rồi gộp câu liền nhau lại thành chunk không quá max_chars."""
    sentences = re.split(r'(?<=[.!?…])\s+', text.strip())
    chunks, current = [], ""
    for sent in sentences:
        if not sent:
            continue
        candidate = f"{current} {sent}".strip() if current else sent
        if len(candidate) <= max_chars:
            current = candidate
        else:
            if current:
                chunks.append(current)
            current = sent
    if current:
        chunks.append(current)
    return chunks or [text.strip()]


def trim_silence(audio: np.ndarray, sr: int) -> np.ndarray:
    """Cắt bỏ khoảng lặng thừa ở đầu/cuối 1 đoạn audio."""
    trimmed, _ = librosa.effects.trim(audio, top_db=TRIM_TOP_DB)
    return trimmed

def synthesize_long_text(text: str, ref_audio: str, denoise: bool) -> np.ndarray:
    """Cắt câu dài thành từng chunk, sinh audio riêng, trim rồi nối bằng khoảng lặng cố định."""
    chunks = split_into_chunks(text)
    silence = np.zeros(int(SILENCE_GAP_SEC * SAMPLE_RATE), dtype=np.float32)

    pieces = []
    for chunk in chunks:
        audio = _tts.infer(chunk, ref_audio=ref_audio, denoise=denoise)
        audio = trim_silence(np.asarray(audio, dtype=np.float32), SAMPLE_RATE)
        pieces.append(audio)

    if len(pieces) == 1:
        return pieces[0]

    joined = pieces[0]
    for piece in pieces[1:]:
        joined = np.concatenate([joined, silence, piece])
    return joined

class TTSRequest(BaseModel):
    text: str
    ref_audio_base64: Optional[str] = None  # audio mẫu để clone giọng (.wav, base64) — bỏ trống để dùng giọng mặc định
    denoise: bool = True

@app.get("/health")
def health():
    return {"status": "ok", "model": "VieNeu-TTS-v3-Turbo", "sample_rate": SAMPLE_RATE}

@app.post("/tts")
def synthesize(req: TTSRequest):
    text = (req.text or "").strip()
    if not text:
        raise HTTPException(status_code=400, detail="Trường 'text' không được để trống")
    if len(text) > MAX_CHARS:
        raise HTTPException(status_code=400, detail=f"Văn bản quá dài (tối đa {MAX_CHARS} ký tự)")

    ref_audio_path = DEFAULT_REF_AUDIO
    tmp_file = None
    if req.ref_audio_base64:
        try:
            audio_bytes = base64.b64decode(req.ref_audio_base64)
        except Exception:
            raise HTTPException(status_code=400, detail="ref_audio_base64 không hợp lệ (không giải mã được base64)")
        tmp_file = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        tmp_file.write(audio_bytes)
        tmp_file.flush()
        tmp_file.close()
        ref_audio_path = tmp_file.name
    elif not os.path.exists(DEFAULT_REF_AUDIO):
        raise HTTPException(
            status_code=500,
            detail="Không tìm thấy ref_audio.wav mặc định — đặt file này cạnh app.py, "
                   "hoặc truyền ref_audio_base64 trong request.",
        )
    try:
        audio = synthesize_long_text(text, ref_audio_path, req.denoise)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi khi sinh audio: {e}")
    finally:
        if tmp_file:
            os.remove(tmp_file.name)

    buf = io.BytesIO()
    sf.write(buf, audio, SAMPLE_RATE, format="WAV")
    buf.seek(0)
    return StreamingResponse(
        buf,
        media_type="audio/wav",
        headers={"Content-Disposition": "attachment; filename=output.wav"},
    )
