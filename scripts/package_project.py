"""Package source with reproducible ordering; exclude credentials, runtime data and caches."""
from pathlib import Path
import argparse
import zipfile
ROOT=Path(__file__).resolve().parents[1]
EXCLUDED={
    '.venv','venv','.git','node_modules','.next','__pycache__','.pytest_cache',
    '.pytest_tmp','chroma_db','runtime','htmlcov','.mypy_cache','.ruff_cache',
    '_stabilization','_tooling','_clean_venv311','_clean_venv311_full',
    '_pytest_runs','_npm_cache','_hf_cache','_ingestion_audit','_final_audit',
    '_smoke','coverage'
}

def include(path: Path):
    parts=path.parts
    if any(p in EXCLUDED or p.startswith(('.codex-test-temp','.pytest','pytest-of-')) for p in parts):return False
    name=path.name
    if name.startswith('.env') and not name.endswith('.example'):return False
    if name.endswith(('.pyc','.pyo','.tsbuildinfo','.log','.sqlite3','.sqlite3-shm','.sqlite3-wal')) or name in {'.DS_Store','Thumbs.db','.coverage'}:return False
    return True

def package(output: Path):
    output=output.resolve()
    output.parent.mkdir(parents=True,exist_ok=True)
    count=0
    with zipfile.ZipFile(output,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as archive:
        for path in sorted(ROOT.rglob('*')):
            relative=path.relative_to(ROOT)
            # Empty package markers are intentional. Other zero-byte files are
            # legacy scaffolding, not usable source/configuration artifacts.
            nonempty_or_package_marker = path.stat().st_size > 0 or path.name == '__init__.py'
            if (path.is_file() and path.resolve()!=output and include(relative)
                    and nonempty_or_package_marker):
                archive.write(path,Path('IP-SAKTI-Intelligence')/relative)
                count+=1
    return count
if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('output',nargs='?',type=Path,default=ROOT.parent/'IP-SAKTI-Intelligence-FINAL.zip')
    args=parser.parse_args()
    print(f'Packaged {package(args.output)} files into {args.output.name}')
