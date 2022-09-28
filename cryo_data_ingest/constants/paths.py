from pathlib import Path


PACKAGE_DIR = Path(__file__).parent.parent
PROJECT_DIR = PACKAGE_DIR.parent
SCRIPTS_DIR = PROJECT_DIR / 'scripts'

JSON_STORAGE_DIR = Path('/tmp/cryo-data-ingest')
