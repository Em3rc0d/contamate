"""Daemon dockerizado opcional para escaneo incremental y recordatorio mediante logs.
Sin acceso al micrófono; no invoca LLM ni servicios externos.
"""
import argparse
import logging
from contextlib import closing
import signal
import threading
from datetime import date
from contamate.db import connect, company, list_tasks
from contamate.documents import scan

stop = threading.Event()


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--interval', type=int, default=300)
    args=p.parse_args()
    if args.interval < 30:raise ValueError('El intervalo mínimo es 30 segundos.')
    logging.basicConfig(level=logging.INFO,format='%(asctime)s %(levelname)s %(message)s')
    signal.signal(signal.SIGTERM,lambda *_:stop.set())
    signal.signal(signal.SIGINT,lambda *_:stop.set())
    logging.info('Iniciado. Escaneo solo de carpetas expresamente autorizadas.')
    while not stop.is_set():
        try:
            with closing(connect()) as conn:
                for entry in conn.execute('SELECT ruc FROM companies ORDER BY ruc').fetchall():
                    if stop.is_set():break
                    try:
                        c=company(conn,entry['ruc'])
                        result=scan(conn,c)
                        logging.info('%s: importados=%s sin_cambios=%s errores=%s',
                                     entry['ruc'],result['imported'],result['unchanged'],result['errors'])
                        for t in list_tasks(conn,c['id']):
                            if not t['done'] and t['due_date'] and t['due_date']<=date.today().isoformat():
                                logging.warning('Pendiente vencido: RUC %s ID tarea %s',entry['ruc'],t['id'])
                    except (OSError,ValueError,RuntimeError) as exc:
                        logging.error('Error de empresa %s: %s',entry['ruc'],exc)
        except (OSError,RuntimeError) as exc:
            logging.error('Error scheduler: %s',exc)
        stop.wait(args.interval)
    logging.info('Detenido sin modificar documentos originales.')


if __name__=='__main__':main()
