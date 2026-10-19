"""Búsqueda local textual de fuentes documentales versionadas (sin inferir vigencia legal)."""
import hashlib
import re
from datetime import date
from pathlib import Path

from .documents import MAX_SIZE, DocumentError


def _chunks(s, limit=1300):
    # Dividir aproximadamente por párrafos manteniendo citas por página.
    s = re.sub(r'\s+', ' ', s).strip()
    for i in range(0, len(s), limit):
        yield s[i:i+limit]


def add_source(conn, filepath, title, source_uri, valid_from=None, valid_until=None):
    p = Path(filepath).expanduser().resolve(strict=True)
    if not p.is_file() or p.suffix.lower() not in ('.txt','.md','.pdf'):
        raise DocumentError('Fuentes admitidas: PDF digital, TXT o MD.')
    if p.stat().st_size > MAX_SIZE:
        raise DocumentError('La fuente supera el límite de 20 MiB.')
    if not title.strip() or not source_uri.strip():
        raise ValueError('Se requieren título y origen documentado de la fuente.')
    for d in (valid_from, valid_until):
        if d: date.fromisoformat(d)
    if valid_from and valid_until and valid_from > valid_until:
        raise ValueError('El fin de vigencia precede al inicio.')
    text_by_page = []
    if p.suffix.lower() == '.pdf':
        from pypdf import PdfReader
        try:
            reader=PdfReader(p, strict=True)
            if len(reader.pages)>500:raise DocumentError('Fuente de más de 500 páginas: procesar por secciones.')
            text_by_page=[(i+1, reader.pages[i].extract_text() or '') for i in range(len(reader.pages))]
        except DocumentError:raise
        except Exception as exc:raise DocumentError(f'PDF no legible: {exc}') from exc
    else:
        text_by_page=[(1,p.read_text(encoding='utf-8-sig'))]
    blocks=[(i,part) for i,text in text_by_page for part in _chunks(text) if len(part.strip())>20]
    if not blocks:
        raise DocumentError('Sin texto extraíble; no se aplicó OCR.')
    digest=hashlib.sha256(p.read_bytes()).hexdigest()
    with conn:
        cur=conn.execute('''INSERT INTO knowledge_sources(title,source_uri,local_path,sha256,effective_from,effective_until)
                            VALUES (?,?,?,?,?,?)''',(title.strip(),source_uri.strip(),str(p),digest,valid_from,valid_until))
        sid=cur.lastrowid
        conn.executemany('INSERT INTO knowledge_chunks(body,source_id,page) VALUES(?,?,?)',
                         [(part,sid,i) for i,part in blocks])
    return {'source_id':sid,'chunks':len(blocks),'title':title,
            'warning':'Metadatos declarados por el usuario; vigencia y autenticidad NO verificadas automáticamente.'}


def search(conn, query, as_of=None, limit=6):
    if as_of: date.fromisoformat(as_of)
    words=[x for x in re.findall(r'[^\W_]{3,}',query.lower(),flags=re.UNICODE) if x not in {
        'que','los','las','del','una','con','para','por','sobre','como','cual','esta','este','hay','son','puedo','quiero','cuanto','saber','normativa'}]
    if not words:return []
    # Construcción segura: palabras filtradas, entrecomilladas para evitar operadores FTS5.
    match=' OR '.join('"'+w.replace('"','')+'"' for w in dict.fromkeys(words[:10]))
    filt=''
    args=[match]
    if as_of:
        # Solo fuentes con fechas informadas y compatibles en el intervalo.
        filt=' AND s.effective_from IS NOT NULL AND s.effective_from<=? AND (s.effective_until IS NULL OR s.effective_until>=?)'
        args.extend([as_of,as_of])
    args.append(limit)
    rows=conn.execute('''SELECT s.title,s.source_uri,s.local_path,s.effective_from,s.effective_until,
                       k.page,k.body,bm25(knowledge_chunks) AS score
                       FROM knowledge_chunks k JOIN knowledge_sources s ON s.id=CAST(k.source_id AS INTEGER)
                       WHERE knowledge_chunks MATCH ? '''+filt+' ORDER BY score LIMIT ?',args).fetchall()
    return [dict(x) for x in rows]
