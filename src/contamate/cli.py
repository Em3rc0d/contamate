"""Interfaz de terminal sin dependencia cloud."""
import argparse
import json
import sys
import time
from datetime import date
from pathlib import Path

from . import __version__
from .db import add_company, add_root, company, connect, home, list_tasks
from .documents import scan
from .llm import ask_local
from .review import compare, report_md


def _parser():
    p = argparse.ArgumentParser(prog='contamate',description='ContaMate Local: agente documental peruano, sin envío cloud')
    p.add_argument('--version', action='version', version=__version__)
    sp = p.add_subparsers(dest='command',required=True)
    sp.add_parser('init',help='Inicializar base SQLite local')
    sp.add_parser('doctor',help='Diagnóstico de entorno y recursos')
    cmp = sp.add_parser('company',help='Operaciones de empresas')
    csp = cmp.add_subparsers(dest='action',required=True)
    cadd = csp.add_parser('add');cadd.add_argument('--ruc',required=True);cadd.add_argument('--name',required=True)
    csp.add_parser('list')
    allow = sp.add_parser('allow',help='Autorizar carpeta local de lectura');allow.add_argument('--ruc',required=True);allow.add_argument('--folder',required=True)
    for name in ('scan','watch'):
        sub=sp.add_parser(name,help='Importar documentos autorizados' if name=='scan' else 'Vigilar carpetas autorizadas')
        sub.add_argument('--ruc',required=True)
        if name=='watch':sub.add_argument('--interval',type=int,default=300)
    for name in ('review','report','ask','brief'):
        sub=sp.add_parser(name,help={'review':'Comparar XML con registro','report':'Generar informe Markdown','ask':'Consultar análisis con Ollama local','brief':'Resumen diario sin IA'}[name])
        sub.add_argument('--ruc',required=True);sub.add_argument('--period',required=True)
        if name=='report':sub.add_argument('--out')
        if name=='ask':sub.add_argument('--question',required=True);sub.add_argument('--model')
    know=sp.add_parser('knowledge',help='Corpus documental local con procedencia y vigencia declarada')
    ksp=know.add_subparsers(dest='action',required=True)
    kadd=ksp.add_parser('add');kadd.add_argument('--file',required=True);kadd.add_argument('--title',required=True)
    kadd.add_argument('--source',required=True);kadd.add_argument('--valid-from');kadd.add_argument('--valid-until')
    kfind=ksp.add_parser('search');kfind.add_argument('--query',required=True);kfind.add_argument('--as-of')
    tasks=sp.add_parser('task');tsp=tasks.add_subparsers(dest='action',required=True)
    tadd=tsp.add_parser('add');tadd.add_argument('--ruc',required=True);tadd.add_argument('--title',required=True);tadd.add_argument('--due')
    tlist=tsp.add_parser('list');tlist.add_argument('--ruc',required=True)
    tdone=tsp.add_parser('done');tdone.add_argument('--ruc',required=True);tdone.add_argument('--id',type=int,required=True)
    voice=sp.add_parser('voice',help='Voz local opcional (requiere whisper.cpp / Piper)')
    vsp=voice.add_subparsers(dest='action',required=True)
    trans=vsp.add_parser('transcribe');trans.add_argument('--wav',required=True);trans.add_argument('--whisper-bin',required=True);trans.add_argument('--whisper-model',required=True)
    speak=vsp.add_parser('speak');speak.add_argument('--text',required=True);speak.add_argument('--piper-bin',required=True);speak.add_argument('--piper-model',required=True);speak.add_argument('--out',required=True)
    va=vsp.add_parser('ask');va.add_argument('--ruc',required=True);va.add_argument('--period',required=True)
    va.add_argument('--wav',required=True);va.add_argument('--whisper-bin',required=True);va.add_argument('--whisper-model',required=True)
    va.add_argument('--piper-bin',required=True);va.add_argument('--piper-model',required=True);va.add_argument('--out',required=True);va.add_argument('--model')
    return p


def _doctor():
    import platform
    import os
    from urllib.request import urlopen
    print(f'ContaMate {__version__} | {platform.platform()} | Python {platform.python_version()}')
    print('Datos:',home())
    try:
        import psutil
        m=psutil.virtual_memory()
        print(f'RAM total: {m.total / 1024**3:.1f} GiB | disponible: {m.available / 1024**3:.1f} GiB')
        if m.available < 4 * 1024**3:
            print('Aviso: RAM libre reducida. Preferir un modelo pequeño y ejecución secuencial.')
    except ImportError:
        print('psutil no instalado: sin información de RAM.')
    try:
        with urlopen(os.getenv('CONTAMATE_OLLAMA_URL', 'http://127.0.0.1:11434')+'/api/tags',timeout=2) as response:
            models=json.load(response).get('models',[])
        print('Ollama local:', ', '.join(x.get('name','?') for x in models) or 'sin modelos')
    except Exception:
        print('Ollama local: no disponible (el motor determinístico sigue funcionando).')
    print('Red externa: no utilizada por ContaMate en este diagnóstico.')


def _run(args):
    if args.command=='doctor':
        _doctor();return
    conn=connect()
    try:
        if args.command=='init':
            print('SQLite inicializada:',home() / 'contamate.sqlite3');return
        if args.command=='knowledge':
            from .knowledge import add_source, search
            if args.action=='add':
                print(json.dumps(add_source(conn,args.file,args.title,args.source,args.valid_from,args.valid_until),ensure_ascii=False,indent=2))
            else:
                print(json.dumps(search(conn,args.query,args.as_of),ensure_ascii=False,indent=2))
            return
        if args.command=='company':
            if args.action=='add':
                add_company(conn,args.ruc,args.name);print('Empresa registrada:',args.ruc)
            else:
                for x in conn.execute('SELECT ruc,name FROM companies ORDER BY name'):
                    print(x['ruc'],x['name'])
            return
        if args.command=='allow':
            add_root(conn,args.ruc,args.folder);print('Carpeta autorizada para lectura:',args.folder);return
        if args.command=='voice' and args.action in ('transcribe','speak'):
            from .voice import transcribe, speak
            if args.action=='transcribe':
                print(transcribe(args.wav,args.whisper_bin,args.whisper_model))
            else:
                print(speak(args.text,args.piper_bin,args.piper_model,args.out))
            return
        c=company(conn,args.ruc)
        if args.command=='scan':
            print(json.dumps(scan(conn,c),ensure_ascii=False,indent=2));return
        if args.command=='watch':
            if args.interval < 10:
                raise ValueError('Intervalo mínimo de vigilancia: 10 segundos.')
            print('Vigilancia local activa; Ctrl+C para salir. No graba micrófono.')
            try:
                while True:
                    print(json.dumps(scan(conn,c),ensure_ascii=False))
                    tasks=[t for t in list_tasks(conn,c['id']) if not t['done'] and t['due_date'] and t['due_date']<=date.today().isoformat()]
                    for t in tasks:print(f'PENDIENTE: {t["title"]} ({t["due_date"]})')
                    time.sleep(args.interval)
            except KeyboardInterrupt:
                print('\nVigilancia detenida.');return
        if args.command=='task':
            if args.action=='add':
                if not args.title.strip():raise ValueError('Título de tarea vacío.')
                if args.due:date.fromisoformat(args.due)
                with conn:
                    new=conn.execute('INSERT INTO tasks(company_id,title,due_date) VALUES(?,?,?)',
                                     (c['id'],args.title.strip(),args.due)).lastrowid
                print('Tarea registrada:',new)
            elif args.action=='list':
                print(json.dumps(list_tasks(conn,c['id']),ensure_ascii=False,indent=2))
            else:
                with conn:
                    updated=conn.execute('UPDATE tasks SET done=1 WHERE id=? AND company_id=?', (args.id,c['id'])).rowcount
                if not updated:raise ValueError('Tarea no encontrada para este RUC.')
                print('Tarea completada:',args.id)
            return
        if args.command=='voice':
            from .voice import transcribe, speak
            question=transcribe(args.wav,args.whisper_bin,args.whisper_model)
            print('Escuché:',question)
            rev=compare(conn,c,args.period)
            from .knowledge import search
            answer=ask_local(question,rev,list_tasks(conn,c['id']),args.model,knowledge=search(conn,question,args.period+'-01'))
            print('ContaMate:',answer)
            print('Audio:',speak(answer,args.piper_bin,args.piper_model,args.out));return
        rev=compare(conn,c,args.period)
        if args.command=='review':
            print(json.dumps(rev,ensure_ascii=False,indent=2));return
        if args.command=='brief':
            pending=[t for t in list_tasks(conn,c['id']) if not t['done']]
            due=[t for t in pending if t['due_date'] and t['due_date']<=date.today().isoformat()]
            print(f'ContaMate · {c["name"]} · {args.period}')
            print(f'Documentos comparados: {rev["matched_keys"]} | Hallazgos: {len(rev["issues"])} | Pendientes: {len(pending)} | Vencidos/hoy: {len(due)}')
            print(f'Archivos con advertencia: {len(rev["unprocessed_documents"])}')
            for t in due[:10]:print(f' - {t["title"]} ({t["due_date"]})')
            print('Revisión profesional necesaria; esto no confirma situación ante SUNAT.')
            return
        if args.command=='report':
            target=Path(args.out).expanduser().resolve() if args.out else home()/'reports'/f'{c["ruc"]}-{args.period}.md'
            target.parent.mkdir(parents=True,exist_ok=True)
            target.write_text(report_md(rev,list_tasks(conn,c['id'])),encoding='utf-8')
            print('Informe:',target);return
        if args.command=='ask':
            from .knowledge import search
            snippets=search(conn,args.question,args.period+'-01')
            print('ContaMate:',ask_local(args.question,rev,list_tasks(conn,c['id']),args.model,knowledge=snippets));return
    finally:
        conn.close()


def main(argv=None):
    args=_parser().parse_args(argv)
    try:
        _run(args)
    except (ValueError, OSError, RuntimeError, LookupError) as exc:
        print(f'ERROR: {exc}',file=sys.stderr)
        return 2
    return 0


if __name__ == '__main__':
    sys.exit(main())
