"""Instala las dos empresas ficticias en el volumen principal. Nunca sustituye datos reales."""
from pathlib import Path
from contextlib import closing
from contamate.db import connect, add_company, add_root, company
from contamate.documents import scan
from contamate.review import compare


def main():
    data = [('20123456789','Comercial Ejemplo A (FICTICIA)','/samples/empresa_a'),
            ('20987654321','Servicios Ejemplo B (FICTICIA)','/samples/empresa_b')]
    with closing(connect()) as c:
        for ruc, name, folder in data:
            if not c.execute('SELECT 1 FROM companies WHERE ruc=?',(ruc,)).fetchone():
                add_company(c,ruc,name)
            add_root(c,ruc,folder)
            result = scan(c,company(c,ruc))
            rev = compare(c,company(c,ruc),'2026-09')
            print(f'{ruc}: importados={result["imported"]}; hallazgos={len(rev["issues"])}')
        print('Demo preparada: seleccionar período 2026-09 en el panel web.')

if __name__=='__main__':
    main()
