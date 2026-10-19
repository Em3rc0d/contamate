"""Pruebas HTTP: autenticación, permisos, separación de RUC y revisión sin inferencia."""
import os
from pathlib import Path
from unittest.mock import patch
import pytest
from fastapi.testclient import TestClient
from contamate.api import app
from contamate.db import add_company, add_root, connect
from test_core import invoice, register_line, HEAD
from conftest import A,B

TOKEN='local-test-token-of-at-least-thirty-two-characters'

@pytest.fixture
def client(monkeypatch, tmp_path):
    monkeypatch.setenv('CONTAMATE_HOME',str(tmp_path/'data'))
    monkeypatch.setenv('CONTAMATE_API_TOKEN',TOKEN)
    monkeypatch.setenv('CONTAMATE_DOCKER','1')
    return TestClient(app)


def h():return {'X-ContaMate-Token':TOKEN}


def test_web_health_and_security(client):
    assert client.get('/healthz').status_code==200
    assert client.get('/').status_code==200
    assert 'Centro de revisión' in client.get('/').text
    assert client.get('/api/companies').status_code==401
    assert client.get('/api/companies',headers={'X-ContaMate-Token':'wrong'}).status_code==401
    assert client.get('/api/companies',headers=h()).status_code==200
    assert client.get('/').headers['X-Frame-Options']=='DENY'


def test_fail_closed_with_default_token(client,monkeypatch):
    monkeypatch.setenv('CONTAMATE_API_TOKEN','REEMPLAZAR_CON_TOKEN_ALEATORIO_SEGURO_32_CHAR')
    assert client.get('/api/companies',headers=h()).status_code==503


def test_api_review_and_isolation(client,tmp_path,monkeypatch):
    # Simular carpeta autorizada sin necesitar crear /imports en el host.
    a=tmp_path/'firma_a';b=tmp_path/'firma_b';a.mkdir();b.mkdir()
    (a/'factura.xml').write_text(invoice(receiver=A),encoding='utf-8')
    (a/'registro.csv').write_text(HEAD+register_line(total='1181.00'),encoding='utf-8')
    (b/'factura.xml').write_text(invoice(receiver=B),encoding='utf-8')
    for ruc in (A,B):
        assert client.post('/api/companies',headers=h(),json={'ruc':ruc,'name':'Ficticia '+ruc}).status_code==200
    # API solo monta /imports; mock autorización rutas en este test, DB valida raíces realmente.
    with patch('contamate.api.safe_import',side_effect=lambda x: x):
        assert client.post(f'/api/companies/{A}/roots',headers=h(),json={'folder':str(a)}).status_code==200
        assert client.post(f'/api/companies/{B}/roots',headers=h(),json={'folder':str(b)}).status_code==200
    assert client.post(f'/api/companies/{A}/scan',headers=h()).json()['imported']==2
    assert client.post(f'/api/companies/{B}/scan',headers=h()).json()['imported']==1
    ra=client.get(f'/api/companies/{A}/review',headers=h(),params={'period':'2026-09'}).json()
    rb=client.get(f'/api/companies/{B}/review',headers=h(),params={'period':'2026-09'}).json()
    assert [i['code'] for i in ra['issues']]==['AMOUNT_MISMATCH']
    assert [i['code'] for i in rb['issues']]==['MISSING_REGISTER']
    assert str(b) not in str(ra['issues'])
    report=client.get(f'/api/companies/{A}/report',headers=h(),params={'period':'2026-09'})
    assert report.status_code==200 and 'AMOUNT_MISMATCH' in report.text
    assert 'NO ES UNA VALIDACIÓN DE SUNAT' in report.text
    task=client.post(f'/api/companies/{A}/tasks',headers=h(),json={'title':'Revisar factura'}).json()
    assert client.post(f'/api/companies/{B}/tasks/{task["id"]}/done',headers=h()).status_code==404
    assert client.post(f'/api/companies/{A}/tasks/{task["id"]}/done',headers=h()).status_code==200
    assert client.get(f'/api/companies/{A}/tasks',headers=h()).json()[0]['done']==1


def test_api_path_restrictions(client,tmp_path):
    from contamate.api import safe_import
    safe=tmp_path/'outside';safe.mkdir()
    with pytest.raises(ValueError):safe_import(str(safe))
    with pytest.raises(ValueError):safe_import('/etc/hosts')
    assert client.post('/api/companies',headers=h(),json={'ruc':A,'name':'Prueba'}).status_code==200
    r=client.post(f'/api/companies/{A}/roots',headers=h(),json={'folder':'/etc'})
    assert r.status_code==422
    assert client.post('/api/companies',headers=h(),json={'ruc':'abc','name':'Wrong'}).status_code==422


def test_ask_ollama_synthetic(client,monkeypatch):
    assert client.post('/api/companies',headers=h(),json={'ruc':A,'name':'Prueba'}).status_code==200
    with patch('contamate.api.ask_local',return_value='No existe evidencia SUNAT de aceptación.') as fn:
        response=client.post(f'/api/companies/{A}/ask',headers=h(),json={'period':'2026-09','question':'¿Es válido el XML?'})
        assert response.status_code==200
        assert 'No existe evidencia' in response.json()['answer']
        fn.assert_called_once()


def test_llm_docker_endpoint_allowed(client):
    from contamate.llm import ask_local
    from contamate.review import compare
    from contamate.db import company
    import io,json
    with connect() as c:
        from contamate.db import add_company
        add_company(c,A,'X')
        r=compare(c,company(c,A),'2026-09')
    with patch('contamate.llm.urlopen') as fake:
        fake.return_value.__enter__.return_value=io.BytesIO(json.dumps({'message':{'content':'OK'}}).encode())
        answer=ask_local('hola',r,[],model='qwen3:1.7b',endpoint='http://ollama:11434')
        assert answer=='OK'
    with pytest.raises(ValueError):ask_local('hola',r,[],model='qwen3:1.7b',endpoint='http://example.com:11434')


def test_no_overlapping_company_roots(tmp_path,monkeypatch):
    monkeypatch.setenv('CONTAMATE_HOME',str(tmp_path/'db'))
    from contamate.db import add_root
    root=tmp_path/'docs';root.mkdir();(root/'nested').mkdir()
    with connect() as c:
        add_company(c,A,'A');add_company(c,B,'B')
        add_root(c,A,str(root))
        with pytest.raises(ValueError):add_root(c,B,str(root/'nested'))
