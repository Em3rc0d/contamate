import pytest
from contamate.db import connect, add_company, add_root, company

A='20123456789'
B='20987654321'

@pytest.fixture
def env(tmp_path,monkeypatch):
    monkeypatch.setenv('CONTAMATE_HOME',str(tmp_path/'state'))
    c=connect()
    add_company(c,A,'Comercial Ejemplo A (sintética)')
    add_company(c,B,'Servicios Ejemplo B (sintética)')
    folder_a=tmp_path/'a';folder_b=tmp_path/'b'
    folder_a.mkdir();folder_b.mkdir()
    add_root(c,A,str(folder_a));add_root(c,B,str(folder_b))
    yield c,folder_a,folder_b
    c.close()
