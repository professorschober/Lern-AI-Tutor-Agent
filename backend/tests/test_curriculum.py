import pytest
from .fixtures import CASES, TABLES, FixtureEngine


@pytest.mark.parametrize('topic,title,reference,wrong', CASES, ids=[c[1] for c in CASES])
def test_twenty_exercises(topic,title,reference,wrong):
    engine=FixtureEngine()
    exercise=dict(reference_sql=reference,order_matters='ORDER BY' in reference,aliases_matter=title=='Alias')
    assert engine.evaluate(reference,exercise,TABLES)['verdict']=='correct'
    assert engine.evaluate(wrong,exercise,TABLES)['verdict']=='incorrect'
    # A second data variant guards boundary and accidental equality cases.
    engine.db.execute("INSERT INTO LAB.EMPLOYEES VALUES (7,'Gina',3000,NULL)")
    assert engine.evaluate(reference,exercise,TABLES)['verdict']=='correct'
    assert engine.evaluate(wrong,exercise,TABLES)['verdict']=='incorrect'


def test_versions_do_not_count_as_distinct_objectives(tmp_path):
    from app.store import Store
    store=Store(tmp_path)
    for id in ['v1','v2']:
        store.put('attempt',dict(topic='select',result={'verdict':'correct'},exercise_id=id,lineage='same',supported=False))
    assert store.progress()[0]['state']=='independent'
    store.put('attempt',dict(topic='select',result={'verdict':'correct'},exercise_id='different',lineage='different',supported=False))
    assert store.progress()[0]['state']=='consolidated'
