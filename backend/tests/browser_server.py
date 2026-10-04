"""Isolated browser-test backend; never use this as an Oracle replacement in production."""
import os
import tempfile
os.environ['DATA_DIR']=tempfile.mkdtemp(prefix='tutor-browser-test-')
os.environ['ORACLE_DSN']=''
os.environ['ORACLE_PASSWORD']=''
os.environ['ORACLE_CLIENT_DIR']=''
os.environ['LLM_API_KEY']=''
from app import main
from .fixtures import FixtureEngine
main.engine=FixtureEngine()
app=main.app
