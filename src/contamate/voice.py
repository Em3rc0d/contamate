"""Adaptadores de voz bajo demanda, sin micrófono continuamente activo."""
import subprocess
import tempfile
from pathlib import Path


def transcribe(wav, binary, model):
    audio = Path(wav).expanduser().resolve(strict=True)
    exe = Path(binary).expanduser().resolve(strict=True)
    mdl = Path(model).expanduser().resolve(strict=True)
    if not audio.is_file() or audio.suffix.lower() != '.wav':
        raise ValueError('Se requiere un archivo WAV existente.')
    with tempfile.TemporaryDirectory() as tmp:
        prefix = Path(tmp) / 'whisper_transcript'
        result = subprocess.run([str(exe),'-m',str(mdl),'-f',str(audio),'-otxt','-of',str(prefix),'-nt'],
                                text=True,capture_output=True,timeout=180,check=False)
        output = Path(str(prefix)+'.txt')
        if result.returncode != 0 or not output.exists():
            raise RuntimeError(f'whisper.cpp no pudo transcribir: {result.stderr[-400:]}')
        spoken = output.read_text(encoding='utf-8').strip()
        if not spoken:
            raise RuntimeError('No se reconoció texto en el audio.')
        return spoken


def speak(text, binary, model, out):
    exe = Path(binary).expanduser().resolve(strict=True)
    mdl = Path(model).expanduser().resolve(strict=True)
    path = Path(out).expanduser().resolve()
    path.parent.mkdir(parents=True,exist_ok=True)
    if not text.strip():
        raise ValueError('No se puede sintetizar texto vacío.')
    result = subprocess.run([str(exe), '--model', str(mdl), '--output_file', str(path)],
                            input=text+'\n',text=True,capture_output=True,timeout=180,check=False)
    if result.returncode != 0 or not path.is_file():
        raise RuntimeError(f'Piper no pudo sintetizar audio: {result.stderr[-400:]}')
    return path
