"""Synthetic schema and twenty exercises. Used only in tests, never loaded by production."""
import sqlite3
from app.sql_engine import validate, compare

TABLES = ['LAB.EMPLOYEES', 'LAB.DEPARTMENTS']
SCHEMA = [
    dict(name=TABLES[0], columns=[dict(name=n,type=t) for n,t in [('ID','NUMBER'),('NAME','VARCHAR2'),('SALARY','NUMBER'),('DEPARTMENT_ID','NUMBER')]],
         relationships=[dict(column='DEPARTMENT_ID',target=TABLES[1],target_column='ID')]),
    dict(name=TABLES[1], columns=[dict(name='ID',type='NUMBER'),dict(name='NAME',type='VARCHAR2')],relationships=[]),
]

CASES = [
    ('select','Alle Namen','SELECT name FROM LAB.EMPLOYEES','SELECT salary FROM LAB.EMPLOYEES'),
    ('select','IDs und Namen','SELECT id,name FROM LAB.EMPLOYEES','SELECT name,id FROM LAB.EMPLOYEES'),
    ('select','Alias','SELECT name AS mitarbeiter FROM LAB.EMPLOYEES','SELECT name AS x FROM LAB.EMPLOYEES'),
    ('where','Über 3000','SELECT name,salary FROM LAB.EMPLOYEES WHERE salary>3000','SELECT name,salary FROM LAB.EMPLOYEES WHERE salary>=3000'),
    ('where','Mindestens 3000','SELECT name FROM LAB.EMPLOYEES WHERE salary>=3000','SELECT name FROM LAB.EMPLOYEES WHERE salary>3000'),
    ('where','Zwei Bedingungen','SELECT name FROM LAB.EMPLOYEES WHERE salary>3000 AND department_id=1','SELECT name FROM LAB.EMPLOYEES WHERE salary>3000 OR department_id=1'),
    ('where','Alternative Bedingungen','SELECT name FROM LAB.EMPLOYEES WHERE salary=3000 OR salary=5000','SELECT name FROM LAB.EMPLOYEES WHERE salary=3000 AND salary=5000'),
    ('null','Ohne Abteilung','SELECT name FROM LAB.EMPLOYEES WHERE department_id IS NULL','SELECT name FROM LAB.EMPLOYEES WHERE department_id = NULL'),
    ('null','Mit Abteilung','SELECT name FROM LAB.EMPLOYEES WHERE department_id IS NOT NULL','SELECT name FROM LAB.EMPLOYEES WHERE department_id IS NULL'),
    ('distinct','Eindeutige Gehälter','SELECT DISTINCT salary FROM LAB.EMPLOYEES','SELECT salary FROM LAB.EMPLOYEES'),
    ('order','Gehälter aufsteigend','SELECT salary,name FROM LAB.EMPLOYEES ORDER BY salary','SELECT salary,name FROM LAB.EMPLOYEES ORDER BY salary DESC'),
    ('order','Namen absteigend','SELECT name FROM LAB.EMPLOYEES ORDER BY name DESC','SELECT name FROM LAB.EMPLOYEES ORDER BY name'),
    ('inner','Namen und Abteilungen','SELECT e.name,d.name FROM LAB.EMPLOYEES e INNER JOIN LAB.DEPARTMENTS d ON e.department_id=d.id','SELECT e.name,d.name FROM LAB.EMPLOYEES e LEFT JOIN LAB.DEPARTMENTS d ON e.department_id=d.id'),
    ('inner','Nur IT','SELECT e.name FROM LAB.EMPLOYEES e INNER JOIN LAB.DEPARTMENTS d ON e.department_id=d.id WHERE d.name=\'IT\'','SELECT e.name FROM LAB.EMPLOYEES e INNER JOIN LAB.DEPARTMENTS d ON e.department_id=d.id'),
    ('inner','Abteilungen ohne Duplikate','SELECT DISTINCT d.name FROM LAB.EMPLOYEES e INNER JOIN LAB.DEPARTMENTS d ON e.department_id=d.id','SELECT d.name FROM LAB.EMPLOYEES e INNER JOIN LAB.DEPARTMENTS d ON e.department_id=d.id'),
    ('inner','Verknüpfung und Gehalt','SELECT e.name,d.name FROM LAB.EMPLOYEES e INNER JOIN LAB.DEPARTMENTS d ON e.department_id=d.id WHERE e.salary>=3000','SELECT e.name,d.name FROM LAB.EMPLOYEES e INNER JOIN LAB.DEPARTMENTS d ON e.department_id=d.id WHERE e.salary>3000'),
    ('left','Alle Mitarbeiter','SELECT e.name,d.name FROM LAB.EMPLOYEES e LEFT JOIN LAB.DEPARTMENTS d ON e.department_id=d.id','SELECT e.name,d.name FROM LAB.EMPLOYEES e INNER JOIN LAB.DEPARTMENTS d ON e.department_id=d.id'),
    ('left','Ohne Zuordnung','SELECT e.name FROM LAB.EMPLOYEES e LEFT JOIN LAB.DEPARTMENTS d ON e.department_id=d.id WHERE d.id IS NULL','SELECT e.name FROM LAB.EMPLOYEES e LEFT JOIN LAB.DEPARTMENTS d ON e.department_id=d.id WHERE d.id IS NOT NULL'),
    ('left','Leere Abteilungen','SELECT d.name FROM LAB.DEPARTMENTS d LEFT JOIN LAB.EMPLOYEES e ON d.id=e.department_id WHERE e.id IS NULL','SELECT d.name FROM LAB.DEPARTMENTS d LEFT JOIN LAB.EMPLOYEES e ON d.id=e.department_id WHERE e.id IS NOT NULL'),
    ('left','Sortierte Verknüpfung','SELECT e.name,d.name FROM LAB.EMPLOYEES e LEFT JOIN LAB.DEPARTMENTS d ON e.department_id=d.id ORDER BY e.name','SELECT e.name,d.name FROM LAB.EMPLOYEES e LEFT JOIN LAB.DEPARTMENTS d ON e.department_id=d.id ORDER BY e.name DESC'),
]


class FixtureEngine:
    def __init__(self):
        self.db=sqlite3.connect(':memory:',check_same_thread=False)
        self.db.execute("ATTACH DATABASE ':memory:' AS LAB")
        self.db.executescript('''CREATE TABLE LAB.EMPLOYEES (ID INTEGER,NAME TEXT,SALARY NUMERIC,DEPARTMENT_ID INTEGER);
          CREATE TABLE LAB.DEPARTMENTS (ID INTEGER,NAME TEXT);
          INSERT INTO LAB.DEPARTMENTS VALUES (1,'IT'),(2,'HR'),(3,'Leer');
          INSERT INTO LAB.EMPLOYEES VALUES (1,'Ada',3000,1),(2,'Ben',5000,1),
          (3,'Cara',3000,2),(4,'Dora',2500,NULL),(5,'Emil',4500,99),(6,'Fay',5000,1);''')

    def schema(self): return SCHEMA

    def check(self,sql,allowed,order_matters=False):
        tree=validate(sql,allowed)
        cursor=self.db.execute(tree.sql(dialect='sqlite'))
        return [d[0].upper() for d in cursor.description],cursor.fetchall()

    def evaluate(self,sql,e,allowed):
        try:
            st=validate(sql,allowed);rt=validate(e['reference_sql'],allowed)
            student=self.check(sql,allowed);reference=self.check(e['reference_sql'],allowed)
            correct,code=compare(student,reference,rt,st,e['order_matters'],e['aliases_matter'])
            return dict(execution='success',verdict='correct' if correct else 'incorrect',columns=student[0],rows=student[1],feedback_code=code)
        except (ValueError,sqlite3.Error) as exc:
            return dict(execution='error',verdict='ungradable',columns=[],rows=[],feedback_code='execution_error',message=str(exc))
