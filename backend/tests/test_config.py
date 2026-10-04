from app.config import Settings, BACKEND_DIR


def test_paths_do_not_depend_on_working_directory(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    settings = Settings(_env_file=None)
    assert settings.data_dir == BACKEND_DIR / 'data'
    assert Settings(data_dir='other', _env_file=None).data_dir == BACKEND_DIR / 'other'
    assert Settings(data_dir=tmp_path, _env_file=None).data_dir == tmp_path
    assert Settings.model_config['env_file'] == BACKEND_DIR / '.env'
