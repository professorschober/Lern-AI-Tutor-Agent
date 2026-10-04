from datetime import datetime
from decimal import Decimal
import pytest
from app.sql_engine import validate, compare, cell_key, OracleEngine

ALLOWED = ['LAB.EMPLOYEES', 'LAB.DEPARTMENTS']


@pytest.mark.parametrize('sql', [
    'SELECT last_name FROM LAB.EMPLOYEES',
    'SELECT DISTINCT department_id FROM LAB.EMPLOYEES WHERE salary >= 3000 AND department_id IS NOT NULL',
    'SELECT e.last_name, d.name FROM LAB.EMPLOYEES e INNER JOIN LAB.DEPARTMENTS d ON e.department_id = d.id',
    'SELECT e.last_name, d.name FROM LAB.EMPLOYEES e LEFT JOIN LAB.DEPARTMENTS d ON e.department_id = d.id',
    'SELECT last_name AS name FROM LAB.EMPLOYEES ORDER BY name DESC',
])
def test_allowed(sql):
    validate(sql, ALLOWED)


@pytest.mark.parametrize('sql', [
    'DELETE FROM LAB.EMPLOYEES', 'CREATE TABLE x (id NUMBER)',
    'SELECT * FROM LAB.EMPLOYEES; SELECT * FROM LAB.EMPLOYEES',
    'SELECT * FROM SYS.USERS', 'SELECT * FROM LAB.EMPLOYEES@remote',
    'SELECT * FROM (SELECT * FROM LAB.EMPLOYEES)',
    'SELECT COUNT(*) FROM LAB.EMPLOYEES',
    "SELECT evil(secret) FROM LAB.EMPLOYEES",
    'SELECT * FROM LAB.EMPLOYEES FOR UPDATE',
    'WITH x AS (SELECT * FROM LAB.EMPLOYEES) SELECT * FROM x',
    'SELECT * FROM LAB.EMPLOYEES UNION SELECT * FROM LAB.DEPARTMENTS',
    'SELECT * FROM LAB.EMPLOYEES e CROSS JOIN LAB.DEPARTMENTS d',
    'SELECT * FROM LAB.EMPLOYEES e RIGHT JOIN LAB.DEPARTMENTS d ON e.id=d.id',
    'SELECT * FROM LAB.EMPLOYEES e LEFT JOIN LAB.DEPARTMENTS d ON 1=1',
    'SELECT * FROM LAB.EMPLOYEES, LAB.DEPARTMENTS',
    'SELECT * FROM LAB.EMPLOYEES FETCH FIRST 1 ROW ONLY',
])
def test_blocked(sql):
    with pytest.raises(ValueError):
        validate(sql, ALLOWED)


def test_multiset_duplicates_types_null():
    tree = validate('SELECT salary FROM LAB.EMPLOYEES', ALLOWED)
    assert compare((['A'], [(None,), (Decimal('3.00'),), (3,)]), (['B'], [(3,), (None,), (Decimal('3'),)]), tree, tree)[0]
    assert not compare((['A'], [(3,)]), (['A'], [(3,), (3,)]), tree, tree)[0]
    assert not compare((['A'], [('3',)]), (['A'], [(3,)]), tree, tree)[0]
    assert cell_key(datetime(2024,1,1))[0] == 'date'


def test_order_ties_and_aliases():
    rt = validate('SELECT salary, last_name FROM LAB.EMPLOYEES ORDER BY salary', ALLOWED)
    st = validate('SELECT salary, last_name FROM LAB.EMPLOYEES ORDER BY salary', ALLOWED)
    ref = (['SALARY','LAST_NAME'], [(1,'A'), (1,'B'), (2,'C')])
    assert compare((ref[0],[(1,'B'),(1,'A'),(2,'C')]),ref,rt,st,True)[0]
    assert not compare((ref[0],[(2,'C'),(1,'A'),(1,'B')]),ref,rt,st,True)[0]
    assert not compare(ref,ref,rt,validate('SELECT salary,last_name FROM LAB.EMPLOYEES',ALLOWED),True)[0]
    assert not compare((['X','Y'],ref[1]),ref,rt,st,False,True)[0]


def test_execution_failure_ungradable():
    class Settings:
        oracle_client_dir=''
        oracle_dsn=''
        oracle_user=''
        oracle_password=''
    engine=OracleEngine(Settings())
    exercise=dict(reference_sql='SELECT salary FROM LAB.EMPLOYEES',order_matters=False,aliases_matter=False)
    assert engine.evaluate('DELETE FROM LAB.EMPLOYEES',exercise,ALLOWED)['verdict']=='ungradable'
    assert engine.evaluate('SELECT salary FROM LAB.EMPLOYEES',exercise,ALLOWED)['verdict']=='ungradable'


def test_row_limit():
    class Cursor:
        description=[('X',)]
        def __enter__(self): return self
        def __exit__(self,*args): pass
        def execute(self,sql): pass
        def fetchmany(self,size): return [(1,)] * size
    class Connection:
        def cursor(self): return Cursor()
    with pytest.raises(ValueError,match='1.000'):
        OracleEngine.fetch(Connection(),'SELECT x FROM lab.employees')
