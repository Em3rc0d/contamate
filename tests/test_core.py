import io
import json
from pathlib import Path
from unittest.mock import patch
import pytest
from contamate.db import company, add_root, connect
from contamate.documents import read_document, scan, DocumentError
from contamate.review import compare, report_md
from contamate.llm import ask_local
from conftest import A,B


def invoice(receiver=A,number='F001-00000001',total='1180.00',issuer='20444555666'):
    return f'''<?xml version="1.0" encoding="utf-8"?>
<Invoice xmlns="urn:oasis:names:specification:ubl:schema:xsd:Invoice-2"
 xmlns:cac="urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2"
 xmlns:cbc="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">
<cbc:ID>{number}</cbc:ID><cbc:IssueDate>2026-09-15</cbc:IssueDate>
<cbc:InvoiceTypeCode>01</cbc:InvoiceTypeCode><cbc:DocumentCurrencyCode>PEN</cbc:DocumentCurrencyCode>
<cac:AccountingSupplierParty><cac:Party><cac:PartyIdentification><cbc:ID>{issuer}</cbc:ID></cac:PartyIdentification></cac:Party></cac:AccountingSupplierParty>
<cac:AccountingCustomerParty><cac:Party><cac:PartyIdentification><cbc:ID>{receiver}</cbc:ID></cac:PartyIdentification></cac:Party></cac:AccountingCustomerParty>
<cac:LegalMonetaryTotal><cbc:PayableAmount currencyID="PEN">{total}</cbc:PayableAmount></cac:LegalMonetaryTotal>
</Invoice>'''


def register_line(number='F001-00000001',total='1180.00',issuer='20444555666',receiver=A):
    return f'{issuer},{receiver},{number},2026-09-15,PEN,{total},01\n'

HEAD='ruc_emisor,ruc_receptor,serie_numero,fecha_emision,moneda,total,tipo_comprobante\n'


def test_end_to_end(env):
    c,fa,fb=env
    (fa/'a.xml').write_text(invoice(),encoding='utf-8')
    (fa/'b.xml').write_text(invoice(number='F001-00000002',total='236.00'),encoding='utf-8')
    (fa/'c.xml').write_text(invoice(number='F001-00000004',total='55.00'),encoding='utf-8')
    (fa/'registro.csv').write_text(HEAD+register_line()+register_line('F001-00000002','230.00')+register_line('F001-00000003','700.00'),encoding='utf-8')
    run=scan(c,company(c,A))
    assert run['imported']==4,run
    rev=compare(c,company(c,A),'2026-09')
    assert rev['xml_records']==3
    assert rev['register_records']==3
    assert rev['matched_keys']==2
    assert sorted(x['code'] for x in rev['issues'])==['AMOUNT_MISMATCH','MISSING_REGISTER','MISSING_XML']
    assert all(x['evidence'] for x in rev['issues'])
    text=report_md(rev)
    assert 'registro.csv' in text
    assert 'NO ES UNA VALIDACIÓN DE SUNAT' in text
    again=scan(c,company(c,A))
    assert again['unchanged']==4
    assert again['imported']==0
    assert not compare(c,company(c,B),'2026-09')['issues']


def test_reject_xml_wrong_company(env):
    c,fa,fb=env
    (fa/'other.xml').write_text(invoice(receiver=B),encoding='utf-8')
    r=scan(c,company(c,A))
    assert r['errors']==1
    assert compare(c,company(c,A),'2026-09')['xml_records']==0


def test_defused_xml_dtd(env):
    c,fa,fb=env
    (fa/'bad.xml').write_text('<!DOCTYPE x [<!ENTITY a "BOOM">]><x>&a;</x>',encoding='utf-8')
    r=scan(c,company(c,A))
    assert r['errors']==1
    assert 'rejected' not in r['notes'][0].lower() or 'xml' in r['notes'][0].lower()


def test_isolation_same_number(env):
    c,fa,fb=env
    (fa/'one.xml').write_text(invoice(receiver=A),encoding='utf-8')
    (fb/'two.xml').write_text(invoice(receiver=B),encoding='utf-8')
    scan(c,company(c,A));scan(c,company(c,B))
    a=compare(c,company(c,A),'2026-09')
    b=compare(c,company(c,B),'2026-09')
    assert len(a['issues'])==len(b['issues'])==1
    assert A in a['company']['ruc'] and B in b['company']['ruc']
    assert not any(str(fb) in e['file'] for i in a['issues'] for e in i['evidence'])
    assert not any(str(fa) in e['file'] for i in b['issues'] for e in i['evidence'])


def test_changed_and_removed_files_do_not_leave_stale_records(env):
    c,fa,fb=env
    p=fa/'one.xml'
    p.write_text(invoice(total='1180.00'),encoding='utf-8')
    scan(c,company(c,A))
    p.write_text(invoice(total='1181.00'),encoding='utf-8')
    assert scan(c,company(c,A))['imported']==1
    row=c.execute("SELECT total FROM records WHERE company_id=?",(company(c,A)['id'],)).fetchone()
    assert row['total']=='1181.00'
    p.unlink()
    assert scan(c,company(c,A))['missing']==1
    assert compare(c,company(c,A),'2026-09')['xml_records']==0
    assert compare(c,company(c,A),'2026-09')['unprocessed_documents'][0]['status']=='missing'


def test_duplicates_do_not_double_count(env):
    c,fa,fb=env
    (fa/'one.xml').write_text(invoice(),encoding='utf-8')
    (fa/'copy.xml').write_text(invoice(),encoding='utf-8')
    r=scan(c,company(c,A))
    assert r['duplicates']==1
    assert compare(c,company(c,A),'2026-09')['xml_records']==1


def test_conflicting_duplicate_key_is_flagged(env):
    c,fa,fb=env
    (fa/'one.xml').write_text(invoice(),encoding='utf-8')
    (fa/'other.xml').write_text(invoice(total='999.00'),encoding='utf-8')
    scan(c,company(c,A))
    codes=[x['code'] for x in compare(c,company(c,A),'2026-09')['issues']]
    assert codes==['DUPLICATE_KEY']


def test_outside_symlink_ignored(env,tmp_path):
    c,fa,fb=env
    private=tmp_path/'private.xml'
    private.write_text(invoice(),encoding='utf-8')
    try:
        (fa/'link.xml').symlink_to(private)
    except (OSError,NotImplementedError):
        pytest.skip('Symlink no disponible en este entorno')
    r=scan(c,company(c,A))
    assert r['scanned']==0


def test_csv_ambiguous_decimal_rejected(env):
    c,fa,fb=env
    (fa/'bad.csv').write_text(HEAD+register_line(total='1,180.00'),encoding='utf-8')
    r=scan(c,company(c,A))
    assert r['errors']==1
    assert compare(c,company(c,A),'2026-09')['register_records']==0


def test_pdf_index_only(env):
    from pypdf import PdfWriter
    c,fa,fb=env
    writer=PdfWriter();writer.add_blank_page(width=595,height=842)
    with (fa/'sample.pdf').open('wb') as stream:writer.write(stream)
    r=scan(c,company(c,A))
    assert r['imported']==1
    docs=compare(c,company(c,A),'2026-09')['unprocessed_documents']
    assert docs and docs[0]['status']=='indexed_only'


def test_xlsx_detects_and_processes(env):
    from openpyxl import Workbook
    c,fa,fb=env
    wb=Workbook()
    ws=wb.active
    ws.append(HEAD.strip().split(','))
    ws.append(['20444555666',A,'F001-00000001','2026-09-15','PEN','1180.00','01'])
    wb.save(fa/'compras.xlsx')
    r=scan(c,company(c,A))
    assert r['errors']==0 and r['imported']==1,r
    assert compare(c,company(c,A),'2026-09')['register_records']==1


def test_xlsx_zip_bomb_limit(env):
    c,fa,fb=env
    import zipfile
    p=fa/'bomb.xlsx'
    with zipfile.ZipFile(p,'w',compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr('huge.txt','a'*(81*1024*1024))
    r=scan(c,company(c,A))
    assert r['errors']==1


def test_reject_invalid_ruc(env):
    c,fa,fb=env
    from contamate.db import add_company
    with pytest.raises(ValueError):add_company(c,'200ABC12345','Nope')


def test_reject_invalid_date(env):
    c,fa,fb=env
    with pytest.raises(ValueError):compare(c,company(c,A),'2026-13')


def test_tasks_are_scoped(env):
    c,fa,fb=env
    from contamate.cli import main
    assert main(['task','add','--ruc',A,'--title','Cerrar octubre','--due','2026-10-30'])==0
    assert main(['task','done','--ruc',B,'--id','1'])==2
    assert main(['task','done','--ruc',A,'--id','1'])==0


def test_llm_only_localhost(env):
    c,fa,fb=env
    rev=compare(c,company(c,A),'2026-09')
    with pytest.raises(ValueError):ask_local('hola',rev,[],endpoint='https://example.com')
    with patch('contamate.llm.urlopen') as fake:
        fake.return_value.__enter__.return_value=io.BytesIO(json.dumps({'message':{'content':'Respuesta basada en informe'}}).encode())
        out=ask_local('resume',rev,[],model='qwen3:4b')
        assert 'Respuesta' in out
        payload=json.loads(fake.call_args.args[0].data)
        assert payload['stream'] is False
        assert payload['model']=='qwen3:4b'
        assert 'tools' not in payload


def test_read_document_reject_unknown_format(env):
    c,fa,fb=env
    p=fa/'unknown.yaml';p.write_text('a: b')
    with pytest.raises(DocumentError):read_document(p,A)


def test_knowledge_text_search_with_declared_validity(env):
    from contamate.knowledge import add_source,search
    c,fa,fb=env
    p=fa/'norma.txt'
    p.write_text('El registro de compras electrónico se organiza mediante procedimientos descritos por SUNAT. Esta es una fuente ficticia de prueba.',encoding='utf-8')
    meta=add_source(c,p,'Manual ficticio','https://example.org/ficcion',valid_from='2026-01-01',valid_until='2026-12-31')
    assert meta['chunks']==1
    assert len(search(c,'registro compras','2026-09-15'))==1
    assert search(c,'registro compras','2027-01-15')==[]
    assert search(c,'termino inexistente imposible','2026-09-15')==[]


def test_knowledge_unverified_source_not_used_for_date_filter(env):
    from contamate.knowledge import add_source,search
    c,fa,fb=env
    p=fa/'norma.md';p.write_text('Texto extenso de procedimientos de conciliación comercial con fines ilustrativos.')
    add_source(c,p,'Sin fecha','declaración del usuario')
    assert len(search(c,'conciliación'))==1
    assert search(c,'conciliación','2026-09-01')==[]


def test_model_autoselection(env):
    from contamate.llm import choose_model
    from unittest.mock import MagicMock
    choices={'models':[{'name':'qwen3:0.6b','size':600_000_000},{'name':'qwen3:4b','size':3_000_000_000}]}
    with patch('urllib.request.urlopen') as fake:
        fake.return_value.__enter__.return_value=io.BytesIO(json.dumps(choices).encode())
        selected=choose_model('http://127.0.0.1:11434')
        assert selected in ['qwen3:0.6b','qwen3:4b']


def test_duplicate_backup_restored_after_canonical_deleted(env):
    c,fa,fb=env
    original=fa/'a.xml'; backup=fa/'b.xml'
    original.write_text(invoice())
    backup.write_text(invoice())
    first=scan(c,company(c,A))
    assert first['duplicates']==1
    original.unlink()
    scan(c,company(c,A))
    restored=scan(c,company(c,A))
    assert restored['imported']==1
    assert compare(c,company(c,A),'2026-09')['xml_records']==1


def test_brief_no_model_needed(env,capsys):
    from contamate.cli import main
    assert main(['brief','--ruc',A,'--period','2026-09'])==0
    assert 'Revisión profesional necesaria' in capsys.readouterr().out
