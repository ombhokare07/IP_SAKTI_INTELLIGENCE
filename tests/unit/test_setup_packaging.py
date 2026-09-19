from pathlib import Path
from scripts.setup import configure_environment
from scripts.package_project import include

def test_setup_preserves_existing_credentials_and_only_enables_explicit_demo(tmp_path):
 (tmp_path/'frontend').mkdir()
 (tmp_path/'.env.example').write_text('GEMINI_API_KEY=\nALLOW_MOCK_DATA=false\n')
 (tmp_path/'.env').write_text('GEMINI_API_KEY=PRIVATE_TEST_VALUE\nALLOW_MOCK_DATA=false\n')
 (tmp_path/'frontend/.env.example').write_text('NEXT_PUBLIC_API_BASE_URL=http://localhost:8000\n')
 configure_environment(tmp_path)
 assert (tmp_path/'.env').read_text()=='GEMINI_API_KEY=PRIVATE_TEST_VALUE\nALLOW_MOCK_DATA=false\n'
 configure_environment(tmp_path,True)
 result=(tmp_path/'.env').read_text()
 assert 'GEMINI_API_KEY=PRIVATE_TEST_VALUE' in result and 'ALLOW_MOCK_DATA=true' in result and 'TK_PROVIDER=mock' in result

def test_package_excludes_credentials_and_runtime_but_keeps_examples():
 for p in ['.env','frontend/.env.local','frontend/node_modules/a.js','.venv/a.py','.git/config','frontend/.next/output','chroma_db/a','data/runtime/secret.txt','a/__pycache__/b.pyc','.pytest_tmp/a','.codex-test-temp-status/a']:
  assert not include(Path(p)),p
 for p in ['.env.example','frontend/.env.example','backend/main.py','tests/unit/test_tk_risk.py','data/raw/india/patents/ayush_patent_guidelines_2025.pdf']:
  assert include(Path(p)),p
