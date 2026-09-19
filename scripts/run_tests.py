"""Run the complete backend and frontend automated suites with honest exit status."""
from pathlib import Path
import os
import shutil
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[1]
def main():
    subprocess.run([sys.executable,'-m','pytest','-q'],cwd=ROOT,check=True)
    npm=shutil.which('npm.cmd' if os.name=='nt' else 'npm')
    if not npm:raise RuntimeError('npm is required for the frontend suite.')
    subprocess.run([npm,'test'],cwd=ROOT/'frontend',check=True)
    subprocess.run([npm,'run','typecheck'],cwd=ROOT/'frontend',check=True)
    return 0
if __name__=='__main__':raise SystemExit(main())
