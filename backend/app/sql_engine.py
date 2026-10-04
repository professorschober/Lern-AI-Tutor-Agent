from collections import Counter
from datetime import date, datetime
from decimal import Decimal
from threading import Lock, Timer
import re
import oracledb
import sqlglot
from sqlglot import exp

EXECUTION_LOCK = Lock()


def identifier(node):
    return node.name if node.args.get('quoted') else node.name.upper()


def table_name(table):
    return '.'.join(identifier(x) for x in [table.args.get('db'), table.this] if x)


def validate(sql, allowed):
    if '@' in sql or len(sql) > 10000:
        raise ValueError('Datenbanklinks oder zu lange Abfrage sind nicht erlaubt.')
    try:
        statements = [s for s in sqlglot.parse(sql, read='oracle') if s is not None]
    except sqlglot.errors.ParseError as exc:
        raise ValueError('Die SQL-Struktur ist ungültig. Prüfe Syntax und Klammern.') from exc
    if len(statements) != 1 or not isinstance(statements[0], exp.Select):
        raise ValueError('Genau eine SELECT-Abfrage ist erlaubt.')
    tree = statements[0]
    allowed_nodes = {
        'Select', 'From', 'Table', 'Identifier', 'Column', 'Star', 'Alias', 'Distinct',
        'Where', 'And', 'Or', 'Not', 'Paren', 'EQ', 'NEQ', 'GT', 'GTE', 'LT', 'LTE',
        'Is', 'Null', 'Literal', 'Boolean', 'Order', 'Ordered', 'Join', 'TableAlias',
        'In', 'Between', 'Like', 'Neg',
    }
    for node in tree.walk():
        if type(node).__name__ not in allowed_nodes:
            raise ValueError(f'Dieses Kapitel unterstützt {type(node).__name__} nicht.')
        if isinstance(node, exp.Identifier) and not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_$#]*', node.name):
            raise ValueError('Nicht unterstützter Bezeichner.')
    tables = list(tree.find_all(exp.Table))
    if not 1 <= len(tables) <= 2 or any(table_name(t) not in allowed for t in tables):
        raise ValueError('Verwende eine oder zwei freigegebene Übungstabellen.')
    for join in tree.find_all(exp.Join):
        if join.side not in ('', 'LEFT') or join.kind not in ('', 'INNER', 'OUTER') or not join.args.get('on'):
            raise ValueError('Nur INNER JOIN und LEFT JOIN mit ON sind erlaubt.')
        conditions = join.args['on']
        for part in conditions.flatten() if isinstance(conditions, exp.And) else [conditions]:
            if not isinstance(part, exp.EQ) or not isinstance(part.left, exp.Column) or not isinstance(part.right, exp.Column):
                raise ValueError('JOIN-Verknüpfungen müssen Spalten mit = verbinden.')
    if len(tables) == 2 and not tree.args.get('joins'):
        raise ValueError('Verwende einen expliziten JOIN.')
    return tree


def cell_key(value):
    if value is None:
        return ('null', '')
    if isinstance(value, (int, float, Decimal)) and not isinstance(value, bool):
        return ('number', Decimal(str(value)))
    if isinstance(value, (date, datetime)):
        return ('date', value.isoformat())
    if isinstance(value, str):
        return ('text', value)
    raise ValueError('Nicht unterstützter Ergebnisdatentyp.')


def row_key(row):
    return tuple(cell_key(v) for v in row)


def sort_indices(tree):
    indices = []
    for ordered in tree.args['order'].expressions:
        item = ordered.this
        if isinstance(item, exp.Literal) and not item.is_string:
            index = int(item.this) - 1
        else:
            index = next((i for i, projection in enumerate(tree.expressions)
                          if item.sql(dialect='oracle').upper() in
                          {projection.alias_or_name.upper(), projection.unalias().sql(dialect='oracle').upper()}), -1)
        if index < 0 or index >= len(tree.expressions):
            raise ValueError('Sortierspalten müssen explizit im SELECT-Ergebnis enthalten sein.')
        indices.append(index)
    return indices


def compare(student, reference, reference_tree, student_tree, order_matters=False, aliases_matter=False):
    sc, sr = student
    rc, rr = reference
    if len(sc) != len(rc):
        return False, 'column_count'
    if aliases_matter and sc != rc:
        return False, 'column_aliases'
    if Counter(map(row_key, sr)) != Counter(map(row_key, rr)):
        return False, 'rows_differ'
    if order_matters:
        if not student_tree.args.get('order'):
            return False, 'missing_order'
        indices = sort_indices(reference_tree)
        # Compare reference sort-key sequence: arbitrary order within equal keys is accepted.
        keys = lambda rows: [tuple(row_key(r)[i] for i in indices) for r in rows]
        if keys(sr) != keys(rr):
            return False, 'order_differs'
    return True, 'correct'


class OracleEngine:
    def __init__(self, settings):
        self.settings = settings
        if settings.oracle_client_dir:
            oracledb.init_oracle_client(lib_dir=settings.oracle_client_dir)
        oracledb.defaults.fetch_decimals = True

    def connect(self):
        if not all([self.settings.oracle_dsn, self.settings.oracle_user, self.settings.oracle_password]):
            raise ValueError('Oracle ist noch nicht konfiguriert. Ergänze backend/.env.')
        return oracledb.connect(user=self.settings.oracle_user, password=self.settings.oracle_password,
                                dsn=self.settings.oracle_dsn, tcp_connect_timeout=5)

    @staticmethod
    def fetch(connection, sql):
        timed_out = []
        def cancel():
            timed_out.append(True)
            try:
                connection.cancel()
            except oracledb.Error:
                pass
        timer = Timer(10, cancel)
        timer.start()
        try:
            connection.call_timeout = 10000
            with connection.cursor() as cursor:
                cursor.execute(sql)
                columns = [d[0] for d in cursor.description]
                rows = cursor.fetchmany(1001)
                if timed_out:
                    raise ValueError('Zeitlimit überschritten.')
                if len(rows) > 1000:
                    raise ValueError('Mehr als 1.000 Ergebniszeilen; nicht bewertbar.')
                for row in rows:
                    row_key(row)
                return columns, rows
        finally:
            timer.cancel()
            timer.join()

    def check(self, sql, allowed, order_matters=False):
        tree = validate(sql, allowed)
        if order_matters:
            if not tree.args.get('order'):
                raise ValueError('Eine Sortieraufgabe benötigt ORDER BY.')
            sort_indices(tree)
        with EXECUTION_LOCK, self.connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute('SET TRANSACTION READ ONLY')
            return self.fetch(connection, tree.sql(dialect='oracle'))

    def evaluate(self, sql, exercise, allowed):
        result = dict(execution='error', verdict='ungradable', columns=[], rows=[], feedback_code='execution_error')
        try:
            st = validate(sql, allowed)
            rt = validate(exercise['reference_sql'], allowed)
            with EXECUTION_LOCK, self.connect() as connection:
                with connection.cursor() as cursor:
                    cursor.execute('SET TRANSACTION READ ONLY')
                student = self.fetch(connection, st.sql(dialect='oracle'))
                reference = self.fetch(connection, rt.sql(dialect='oracle'))
            correct, code = compare(student, reference, rt, st, exercise['order_matters'], exercise['aliases_matter'])
            result.update(execution='success', verdict='correct' if correct else 'incorrect',
                          columns=student[0], rows=student[1], feedback_code=code)
        except ValueError as exc:
            result['message'] = str(exc)
        except oracledb.Error as exc:
            # Only the error code; Oracle messages may contain schema/connection details.
            code = getattr(exc.args[0], 'full_code', 'ORACLE_ERROR')
            result['message'] = f'Oracle meldet {code}. Prüfe SQL, Verbindung und Freigaben.'
        return result

    def schema(self):
        with EXECUTION_LOCK, self.connect() as connection, connection.cursor() as cursor:
            connection.call_timeout = 10000
            cursor.execute('''SELECT c.owner, c.table_name, c.column_name, c.data_type
                FROM all_tab_columns c JOIN all_tables t ON t.owner=c.owner AND t.table_name=c.table_name
                WHERE c.owner NOT IN ('SYS','SYSTEM') ORDER BY c.owner,c.table_name,c.column_id''')
            result = {}
            for owner, table, column, datatype in cursor.fetchmany(10000):
                name = f'{owner}.{table}'
                result.setdefault(name, dict(name=name, columns=[], relationships=[]))['columns'].append(dict(name=column, type=datatype))
            cursor.execute('''SELECT a.owner,a.table_name,ac.column_name,b.owner,b.table_name,bc.column_name
                FROM all_constraints a JOIN all_cons_columns ac ON a.owner=ac.owner AND a.constraint_name=ac.constraint_name
                JOIN all_constraints b ON a.r_owner=b.owner AND a.r_constraint_name=b.constraint_name
                JOIN all_cons_columns bc ON b.owner=bc.owner AND b.constraint_name=bc.constraint_name AND ac.position=bc.position
                WHERE a.constraint_type='R' ''')
            for owner, table, col, target_owner, target, target_col in cursor.fetchmany(10000):
                if f'{owner}.{table}' in result:
                    result[f'{owner}.{table}']['relationships'].append(dict(column=col, target=f'{target_owner}.{target}', target_column=target_col))
            return list(result.values())
