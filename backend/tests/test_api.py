from io import BytesIO
from docx import Document
from pypdf import PdfWriter
from fastapi.testclient import TestClient
import pytest
from app import main
from app.store import Store
from app.materials import extract, MAX_BYTES
from app.llm import ModelUnavailable


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(main, 'store', Store(tmp_path))
    monkeypatch.setattr(main.settings,'data_dir',tmp_path)
    monkeypatch.setattr(main.engine,'schema',lambda:[dict(name='LAB.EMPLOYEES',columns=[dict(name='ID',type='NUMBER')],relationships=[])])
    monkeypatch.setattr(main.engine,'check',lambda *args:(['ID'],[(1,)]))
    monkeypatch.setattr(main.engine,'evaluate',lambda *args:dict(execution='success',verdict='correct',columns=['ID'],rows=[[1]],feedback_code='correct'))
    monkeypatch.setattr(main.model,'complete',lambda *args: (_ for _ in ()).throw(ModelUnavailable()))
    return TestClient(main.app, base_url='http://127.0.0.1:8000')


def prepare(client):
    assert client.put('/api/tables',json=['LAB.EMPLOYEES']).status_code==200
    m=client.post('/api/materials',files={'file':('lesson.md',b'# SELECT\nSpalten auswaehlen.','text/markdown')}).json()
    client.put(f"/api/materials/{m['id']}/assignment",json={'topic':'select','tables':['LAB.EMPLOYEES']})
    body=dict(title='IDs lesen',topic='select',prompt='Zeige alle IDs.',reference_sql='SELECT id FROM LAB.EMPLOYEES',
              hints=['Spalte suchen','SELECT verwenden','Spalte ID wählen'],material_ids=[m['id']],tables=['LAB.EMPLOYEES'])
    e=client.post('/api/admin/exercises',json=body).json()
    assert client.post(f"/api/admin/exercises/{e['id']}/publish").status_code==200
    return e,body


def test_full_flow_versions_restart(client,tmp_path):
    e,body=prepare(client)
    s=client.post('/api/sessions',json={}).json()
    current=client.get(f"/api/sessions/{s['id']}/exercise").json()
    assert 'reference_sql' not in current['exercise'] and 'hints' not in current['exercise']
    assert current['materials'][0]['source']=='lesson.md'
    a=client.post(f"/api/sessions/{s['id']}/attempts",json={'sql':'SELECT id FROM LAB.EMPLOYEES'}).json()
    assert a['result']['verdict']=='correct' and not a['supported']
    assert client.get('/api/progress').json()[0]['state']=='independent'
    c=client.post(f"/api/sessions/{s['id']}/chat",json={'message':'Warum SELECT?'}).json()
    assert c['fallback'] and 'korrekt' in c['response']
    edited=client.put(f"/api/admin/exercises/{e['id']}",json={**body,'title':'Neue Version'}).json()
    assert edited['id']!=e['id'] and edited['version']==2 and edited['status']=='draft'
    assert client.get(f"/api/sessions/{s['id']}/exercise").json()['exercise']['title']=='IDs lesen'
    reopened=Store(tmp_path)
    assert reopened.get('session',s['id'])['exercise_id']==e['id']
    assert reopened.list('attempt')[0]['sql']=='SELECT id FROM LAB.EMPLOYEES'


def test_hints_solution_supported(client):
    prepare(client)
    s=client.post('/api/sessions',json={}).json()
    for level in [1,2,3,3]:
        assert client.post(f"/api/sessions/{s['id']}/hint").json()['level']==level
    assert len(client.get(f"/api/sessions/{s['id']}/exercise").json()['released_hints'])==3
    assert 'SELECT' in client.post(f"/api/sessions/{s['id']}/solution").json()['sql']
    assert client.post(f"/api/sessions/{s['id']}/attempts",json={'sql':'SELECT id FROM LAB.EMPLOYEES'}).json()['supported']
    assert client.get('/api/progress').json()[0]['state']=='supported'


def test_publish_requires_reference(client,monkeypatch):
    e,body=prepare(client)
    draft=client.post('/api/admin/exercises',json=body).json()
    def fail(*args): raise ValueError('Referenz ungültig')
    monkeypatch.setattr(main.engine,'check',fail)
    assert client.post(f"/api/admin/exercises/{draft['id']}/publish").status_code==422
    assert main.store.get('exercise',draft['id'])['status']=='draft'


def test_local_access_and_errors(client):
    assert client.get('/api/health',headers={'host':'evil.example'}).status_code==403
    assert client.post('/api/sessions',json={},headers={'origin':'https://evil.example'}).status_code==403
    assert client.post('/api/sessions',json={}).status_code==404
    assert client.get('/api/sessions/unknown/exercise').status_code==404
    assert client.post('/api/materials',files={'file':('bad.pdf',b'broken','application/pdf')}).status_code==422


def test_material_formats():
    doc=Document();doc.add_paragraph('SQL Unterricht');buffer=BytesIO();doc.save(buffer)
    assert 'SQL Unterricht' in extract('lesson.docx',buffer.getvalue())[0]['text']
    assert extract('lesson.md',b'# SQL')[0]['text']=='# SQL'
    pdf=PdfWriter();pdf.add_blank_page(width=100,height=100);buffer=BytesIO();pdf.write(buffer)
    with pytest.raises(ValueError,match='Kein verwertbarer Text'): extract('scan.pdf',buffer.getvalue())
    with pytest.raises(ValueError): extract('x.exe',b'abc')
    with pytest.raises(ValueError,match='20 MB'): extract('huge.md',b'x'*(MAX_BYTES+1))


def test_model_does_not_override_grade_or_expose_sql(client,monkeypatch):
    prepare(client);s=client.post('/api/sessions',json={}).json()
    monkeypatch.setattr(main.model,'complete',lambda *args:'```sql SELECT id FROM LAB.EMPLOYEES```')
    response=client.post(f"/api/sessions/{s['id']}/chat",json={'message':'Gib die Lösung'}).json()
    assert 'SELECT' not in response['response']
    assert not main.store.list('attempt')


def test_join_topic_requires_matching_reference(client):
    _,body=prepare(client)
    e=client.post('/api/admin/exercises',json={**body,'topic':'left'}).json()
    response=client.post(f"/api/admin/exercises/{e['id']}/publish")
    assert response.status_code==422 and 'JOIN' in response.json()['detail']
