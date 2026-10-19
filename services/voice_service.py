"""Servicio opt-in aislado: STT local + TTS Piper con modelo proporcionado por el operador."""
import io
import sys
import os
import subprocess
import tempfile
import threading
from pathlib import Path
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import Response
from pydantic import BaseModel, Field

app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
_model = None
_lock = threading.Lock()
MAX_AUDIO = 8 * 1024 * 1024

class SpeakRequest(BaseModel):
    text: str = Field(min_length=1, max_length=1800)

@app.get('/healthz')
def health():
    model = os.environ.get('VOICE_PIPER_MODEL', '/voices/es.onnx')
    return {'status':'ok','stt':'available_on_demand','tts':'ready' if Path(model).is_file() else 'missing_model'}

@app.post('/transcribe')
def transcribe(file: UploadFile = File(...)):
    global _model
    data = file.file.read(MAX_AUDIO + 1)
    if not data or len(data) > MAX_AUDIO:
        raise HTTPException(413, 'Audio vacío o mayor a 8 MiB.')
    # VAD, STT y la carga del modelo permanecen en este servicio opcional.
    with _lock:
        try:
            if _model is None:
                from faster_whisper import WhisperModel
                _model = WhisperModel(os.getenv('VOICE_STT_MODEL','tiny'), device='cpu', compute_type='int8',
                                      download_root='/voice-models', cpu_threads=2, num_workers=1)
            segments, info = _model.transcribe(io.BytesIO(data), language='es', beam_size=2, vad_filter=True)
            text = ' '.join(s.text.strip() for s in segments).strip()
            return {'text':text,'language':info.language,'warning':'Transcripción automática: confirmar los datos antes de una acción contable.'}
        except Exception as exc:
            raise HTTPException(503, f'STT indisponible: {type(exc).__name__}. Revisar modelo/codec/recursos.') from exc

@app.post('/speak')
def speak(payload: SpeakRequest):
    model = Path(os.environ.get('VOICE_PIPER_MODEL', '/voices/es.onnx'))
    if not model.is_file() or not Path(str(model)+'.json').is_file():
        raise HTTPException(503, 'Falta modelo Piper es.onnx y/o es.onnx.json en ./voices.')
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / 'answer.wav'
        try:
            proc = subprocess.run([sys.executable,'-m','piper','-m',str(model),'-f',str(out),'--',payload.text],
                                  capture_output=True, timeout=75, check=False)
            if proc.returncode or not out.exists():
                raise HTTPException(503, 'Piper no pudo generar el audio. Revisar los archivos de voz.')
            return Response(out.read_bytes(), media_type='audio/wav')
        except subprocess.TimeoutExpired as exc:
            raise HTTPException(504, 'Piper excedió el tiempo límite.') from exc
