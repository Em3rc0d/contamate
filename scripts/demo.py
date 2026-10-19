"""Demo reproducible y offline con datos 100 % ficticios. Ejecutar python scripts/demo.py."""
import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
from contamate.cli import main
from contamate.db import connect, company
from contamate.review import compare


def main_demo():
    parser=argparse.ArgumentParser()
    parser.add_argument('--out',default=str(ROOT/'demo-output'))
    args=parser.parse_args()
    target=Path(args.out).expanduser().resolve()
    target.mkdir(parents=True,exist_ok=True)
    os.environ['CONTAMATE_HOME']=str(target/'state')
    # Repeatable: permit reruns with the same files.
    conn=connect()
    for ruc,name in [('20123456789','Comercial Ejemplo A (ficticia)'),('20987654321','Servicios Ejemplo B (ficticia)')]:
        if conn.execute('SELECT 1 FROM companies WHERE ruc=?',(ruc,)).fetchone() is None:
            assert main(['company','add','--ruc',ruc,'--name',name])==0
        sample_base = Path('/samples') if (Path('/samples') / 'empresa_a').is_dir() else ROOT / 'samples'
        folder=sample_base/('empresa_a' if ruc=='20123456789' else 'empresa_b')
        assert main(['allow','--ruc',ruc,'--folder',str(folder)])==0
        assert main(['scan','--ruc',ruc])==0
    a=compare(conn,company(conn,'20123456789'),'2026-09')
    b=compare(conn,company(conn,'20987654321'),'2026-09')
    assert sorted(x['code'] for x in a['issues'])==['AMOUNT_MISMATCH','MISSING_XML']
    assert len(b['issues'])==1 and b['issues'][0]['code']=='MISSING_REGISTER'
    ra=target/'empresa_a-2026-09.md'
    rb=target/'empresa_b-2026-09.md'
    assert main(['report','--ruc','20123456789','--period','2026-09','--out',str(ra)])==0
    assert main(['report','--ruc','20987654321','--period','2026-09','--out',str(rb)])==0
    conn.close()
    print('\nDEMO OFFLINE OK:',len(a['issues']),'hallazgos A,',len(b['issues']),'hallazgo B')
    print('Informes:',ra,rb)
    print('No se conectó con SUNAT, ni se ejecutó Ollama o voz.')


if __name__=='__main__':
    main_demo()
