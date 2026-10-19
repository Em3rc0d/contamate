"""API local para PoC/MVP-001. Nunca devuelve archivos originales ni opera sobre SUNAT.
Ejecutar solo detrás de la publicación 127.0.0.1 de Compose; NO exponer a una LAN.
"""
import hmac
import io
import json
import os
from contextlib import contextmanager
from datetime import date
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen, Request

from fastapi import Depends, FastAPI, HTTPException, Request as HttpRequest, UploadFile, File
from fastapi.responses import Response, FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.concurrency import run_in_threadpool
from pydantic import BaseModel, Field

from . import __version__
from .db import add_company, add_root, company, connect, home, list_tasks
from .documents import scan
from .review import compare, report_md
from .knowledge import search as knowledge_search, add_source
from .llm import ask_local
from .runtime import resources

app = FastAPI(title='ContaMate Local', version=__version__, docs_url=None, redoc_url=None, openapi_url=None)


@app.middleware('http')
async def security_headers(request: HttpRequest, call_next):
    response = await call_next(request)
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['Referrer-Policy'] = 'no-referrer'
    response.headers['Cache-Control'] = 'no-store'
    response.headers['Content-Security-Policy'] = "default-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'; script-src 'self'; style-src 'self'; connect-src 'self'; media-src 'self' blob:"
    return response


def auth(request: HttpRequest):
    expected = os.getenv('CONTAMATE_API_TOKEN', '')
    if len(expected) < 32 or expected.startswith('REEMPLAZAR_'):
        raise HTTPException(503, 'Configura CONTAMATE_API_TOKEN seguro de 32+ caracteres en .env.')
    provided = request.headers.get('X-ContaMate-Token', '')
    if not hmac.compare_digest(provided, expected):
        raise HTTPException(401, 'Token local requerido.')


@contextmanager
def db():
    conn = connect()
    try:
        yield conn
    finally:
        conn.close()


def safe_import(path: str) -> str:
    """Solo rutas de los volúmenes montados en lectura."""
    p = Path(path).resolve(strict=True)
    roots = [Path('/imports').resolve(), Path('/samples').resolve()]
    if not any(p.is_relative_to(root) for root in roots) or not p.exists():
        raise ValueError('Solo se admiten rutas dentro de /imports o /samples.')
    return str(p)


class CompanyIn(BaseModel):
    ruc: str = Field(min_length=11, max_length=11)
    name: str = Field(min_length=1, max_length=180)


class FolderIn(BaseModel):
    folder: str = Field(min_length=1, max_length=2048)


class AskIn(BaseModel):
    period: str = Field(pattern=r'^\d{4}-\d{2}$')
    question: str = Field(min_length=1, max_length=1000)
    model: str | None = Field(default=None, max_length=150)


class TaskIn(BaseModel):
    title: str = Field(min_length=1, max_length=500)
    due: date | None = None


class SourceIn(BaseModel):
    path: str
    title: str
    source: str
    valid_from: date | None = None
    valid_until: date | None = None


class TextIn(BaseModel):
    text: str = Field(min_length=1, max_length=1800)


def fail(exc):
    if isinstance(exc, (ValueError, LookupError)):
        raise HTTPException(422, str(exc)) from exc
    if isinstance(exc, (RuntimeError, OSError)):
        raise HTTPException(503, str(exc)) from exc
    raise exc


@app.get('/healthz')
def health():
    return {'status':'ok','version':__version__}


@app.get('/api/runtime', dependencies=[Depends(auth)])
def runtime():
    info = {'version':__version__, 'resources':resources(), 'ollama':'offline', 'installed_models':[], 'voice':'disabled_or_offline'}
    try:
        endpoint = os.getenv('CONTAMATE_OLLAMA_URL', 'http://127.0.0.1:11434')
        # Solo endpoint definido por Compose / localhost.
        if endpoint in ('http://ollama:11434','http://127.0.0.1:11434'):
            with urlopen(endpoint+'/api/tags', timeout=2) as response:
                models=json.load(response).get('models',[])
            info['installed_models'] = [m['name'] for m in models if 'name' in m]
            info['ollama']='ready'
    except (OSError, URLError, ValueError):
        pass
    try:
        if os.getenv('CONTAMATE_DOCKER') == '1':
            with urlopen('http://voice:8780/healthz',timeout=1.5) as resp:
                info['voice']=json.load(resp)
    except (OSError, ValueError):
        pass
    return info


@app.get('/api/companies', dependencies=[Depends(auth)])
def companies():
    with db() as c:
        return [dict(x) for x in c.execute('SELECT ruc,name FROM companies ORDER BY name')]


@app.post('/api/companies', dependencies=[Depends(auth)])
def create_company(payload: CompanyIn):
    try:
        with db() as c:
            add_company(c,payload.ruc,payload.name)
        return {'ok':True, 'ruc':payload.ruc}
    except Exception as exc:
        fail(exc)


@app.post('/api/companies/{ruc}/roots', dependencies=[Depends(auth)])
def allow_folder(ruc: str, payload: FolderIn):
    try:
        target = safe_import(payload.folder)
        with db() as c:
            add_root(c,ruc,target)
        return {'ok':True,'folder':target,'read_only':True}
    except Exception as exc:
        fail(exc)


@app.get('/api/companies/{ruc}/roots', dependencies=[Depends(auth)])
def folders(ruc: str):
    with db() as c:
        entry=company(c,ruc)
        return [x['path'] for x in c.execute('SELECT path FROM allowed_roots WHERE company_id=?',(entry['id'],))]


@app.post('/api/companies/{ruc}/scan', dependencies=[Depends(auth)])
def scan_company(ruc: str):
    try:
        with db() as c:
            return scan(c,company(c,ruc))
    except Exception as exc:
        fail(exc)


@app.get('/api/companies/{ruc}/review', dependencies=[Depends(auth)])
def review_company(ruc: str, period: str):
    try:
        with db() as c:
            return compare(c,company(c,ruc),period)
    except Exception as exc:
        fail(exc)


@app.get('/api/companies/{ruc}/report', dependencies=[Depends(auth)])
def report(ruc: str, period: str):
    try:
        with db() as c:
            row=company(c,ruc)
            text=report_md(compare(c,row,period),list_tasks(c,row['id']))
            return Response(text,media_type='text/markdown; charset=utf-8',
                            headers={'Content-Disposition':f'attachment; filename="contamate-{ruc}-{period}.md"'})
    except Exception as exc:
        fail(exc)


@app.post('/api/companies/{ruc}/ask', dependencies=[Depends(auth)])
def ask(ruc: str, payload: AskIn):
    try:
        with db() as c:
            row=company(c,ruc)
            rev=compare(c,row,payload.period)
            tasks=list_tasks(c,row['id'])
            snippets=knowledge_search(c,payload.question,payload.period+'-01')
            answer=ask_local(payload.question,rev,tasks,payload.model,knowledge=snippets)
            return {'answer':answer,'sources':snippets,'limitations':rev['limitations']}
    except Exception as exc:
        fail(exc)


@app.get('/api/companies/{ruc}/tasks', dependencies=[Depends(auth)])
def tasks(ruc: str):
    with db() as c:
        return list_tasks(c,company(c,ruc)['id'])


@app.post('/api/companies/{ruc}/tasks', dependencies=[Depends(auth)])
def add_task(ruc: str, payload: TaskIn):
    try:
        with db() as c:
            row=company(c,ruc)
            with c:
                task_id=c.execute('INSERT INTO tasks(company_id,title,due_date) VALUES(?,?,?)',
                                  (row['id'],payload.title.strip(),payload.due.isoformat() if payload.due else None)).lastrowid
        return {'id':task_id}
    except Exception as exc:
        fail(exc)


@app.post('/api/companies/{ruc}/tasks/{id}/done', dependencies=[Depends(auth)])
def done(ruc: str,id: int):
    with db() as c:
        row=company(c,ruc)
        with c:
            updated=c.execute('UPDATE tasks SET done=1 WHERE id=? AND company_id=?',(id,row['id'])).rowcount
        if not updated:
            raise HTTPException(404,'Tarea no encontrada en esta empresa.')
        return {'ok':True}


@app.get('/api/knowledge/search', dependencies=[Depends(auth)])
def knowledge(query: str, as_of: str | None = None):
    try:
        with db() as c:
            return knowledge_search(c,query,as_of)
    except Exception as exc:
        fail(exc)


@app.post('/api/knowledge/sources', dependencies=[Depends(auth)])
def source_add(payload: SourceIn):
    try:
        p=safe_import(payload.path)
        with db() as c:
            return add_source(c,p,payload.title,payload.source,
                              payload.valid_from.isoformat() if payload.valid_from else None,
                              payload.valid_until.isoformat() if payload.valid_until else None)
    except Exception as exc:
        fail(exc)


def voice_request(path: str, data: bytes, content_type: str, timeout=90):
    if os.getenv('CONTAMATE_DOCKER') != '1':
        raise HTTPException(503,'La voz solo está disponible desde Compose --profile voice.')
    req=Request('http://voice:8780'+path, data=data, method='POST', headers={'Content-Type':content_type})
    try:
        with urlopen(req,timeout=timeout) as response:
            return response.read()
    except Exception as exc:
        raise HTTPException(503,'Servicio de voz no disponible o modelo no preparado. Revisar docker compose --profile voice logs voice.') from exc


@app.post('/api/voice/transcribe', dependencies=[Depends(auth)])
async def speech_to_text(file: UploadFile = File(...)):
    data=await file.read(8*1024*1024+1)
    if len(data)>8*1024*1024 or not data:
        raise HTTPException(413,'Audio inválido o mayor a 8 MiB.')
    # Multipart interno: bytes controlados, sin filepaths del cliente.
    boundary='contamate-voice-boundary'
    body=(f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="audio.webm"\r\n'
          'Content-Type: application/octet-stream\r\n\r\n').encode()+data+(f'\r\n--{boundary}--\r\n').encode()
    raw=await run_in_threadpool(voice_request,'/transcribe',body,f'multipart/form-data; boundary={boundary}',180)
    return json.loads(raw)


@app.post('/api/voice/speak', dependencies=[Depends(auth)])
def text_to_speech(payload: TextIn):
    raw=voice_request('/speak',json.dumps({'text':payload.text}).encode(),'application/json')
    return Response(raw,media_type='audio/wav')


WEB = Path('/app/web') if Path('/app/web').exists() else Path(__file__).resolve().parents[2] / 'web'
app.mount('/', StaticFiles(directory=str(WEB),html=True), name='web')
