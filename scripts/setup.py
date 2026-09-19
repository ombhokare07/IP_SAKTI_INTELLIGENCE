"""Repeatable local setup. Existing .env values are preserved unless --demo is explicit."""
import argparse
import os
from pathlib import Path
import shutil
import subprocess
import sys
import venv

ROOT=Path(__file__).resolve().parents[1]
DEMO_VALUES={'ALLOW_MOCK_DATA':'true','TK_PROVIDER':'mock','REGULATION_PROVIDER':'mock','PRIOR_ART_PROVIDER':'mock','PRIOR_ART_ALLOW_MOCK':'true'}

def configure_environment(root: Path, demo=False):
    target=root/'.env'
    if not target.exists():shutil.copyfile(root/'.env.example',target)
    if demo:
        lines=target.read_text(encoding='utf-8').splitlines()
        seen=set()
        for i,line in enumerate(lines):
            key=line.split('=',1)[0].strip()
            if key in DEMO_VALUES:
                lines[i]=f'{key}={DEMO_VALUES[key]}';seen.add(key)
        lines += [f'{key}={value}' for key,value in DEMO_VALUES.items() if key not in seen]
        target.write_text('\n'.join(lines)+'\n',encoding='utf-8')
    frontend=root/'frontend/.env.local'
    if not frontend.exists():shutil.copyfile(root/'frontend/.env.example',frontend)

def run(command,cwd=ROOT):
    subprocess.run([str(c) for c in command],cwd=cwd,check=True)

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--mode',choices=['offline','full'],default='offline')
    p.add_argument('--demo',action='store_true',help='Explicitly enable labelled synthetic fixtures; never enables production mode.')
    p.add_argument('--skip-frontend',action='store_true')
    p.add_argument('--skip-tests',action='store_true')
    args=p.parse_args(argv)
    if sys.version_info[:2] not in {(3,11),(3,12)}:
        p.error('Use Python 3.11 or 3.12 for the supplied dependency configuration.')
    npm=shutil.which('npm.cmd' if os.name=='nt' else 'npm')
    if not args.skip_frontend and not npm:p.error('Node.js 22 or 24 LTS and npm are required.')
    configure_environment(ROOT,args.demo)
    venv_path=ROOT/'.venv'
    python=venv_path/('Scripts/python.exe' if os.name=='nt' else 'bin/python')
    if not python.exists():venv.EnvBuilder(with_pip=True).create(venv_path)
    requirements='requirements.txt' if args.mode=='full' else 'requirements-offline.txt'
    run([python,'-m','pip','install','-r',requirements])
    if not args.skip_frontend:
        run([npm,'ci','--no-audit','--no-fund'],ROOT/'frontend')
        run([npm,'run','build'],ROOT/'frontend')
    if not args.skip_tests:
        run([python,'-m','pytest','-q'])
        if not args.skip_frontend:run([npm,'test'],ROOT/'frontend')
    print('Setup complete. Provider credentials were not requested or generated.')
    print('Backend: .venv Python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload')
    print('Frontend (separate terminal): cd frontend; npm run dev')
    return 0

if __name__=='__main__':raise SystemExit(main())
