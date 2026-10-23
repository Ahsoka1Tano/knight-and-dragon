"""Test the ZIP delivery in a fresh folder without Python in child PATH."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import zipfile

ROOT=Path(__file__).resolve().parents[1]
PROJECT=ROOT.parent


def main():
    archive=PROJECT/'Для_преподавателя.zip'
    base=ROOT/'.tmp'
    base.mkdir(exist_ok=True)
    destination=Path(tempfile.mkdtemp(prefix='portable-',dir=base))
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        z.extractall(destination)
    package=destination/'Для_преподавателя'
    checked=0
    for entry in (package/'MANIFEST_SHA256.txt').read_text(encoding='utf-8').splitlines():
        expected,name=entry.split('  ',1)
        assert hashlib.sha256((package/name).read_bytes()).hexdigest()==expected,name
        checked+=1
    original=PROJECT/'knight and dragon.py'
    assert original.read_bytes()==(package/original.name).read_bytes()
    assert original.read_bytes()==(package/'source'/original.name).read_bytes()
    env=os.environ.copy()
    for name in ('PYTHONHOME','PYTHONPATH','VIRTUAL_ENV'):
        env.pop(name,None)
    env['PATH']=str(Path(env.get('SystemRoot','C:/Windows'))/'System32')
    env['PYTHONIOENCODING']='utf-8'
    env['SDL_VIDEODRIVER']='dummy'
    env['SDL_AUDIODRIVER']='dummy'
    captures=destination/'captures'
    game=package/'Game/KnightDragon.exe'
    result=subprocess.run([str(game),'--smoke','--capture-dir',str(captures)],cwd=destination,
                          env=env,timeout=45,capture_output=True)
    assert result.returncode==0,(result.returncode,result.stderr)
    assert len(list(captures.glob('*.png')))==13,'Not all screens captured'
    # A real Windows window as well as SDL dummy rendering.
    env.pop('SDL_VIDEODRIVER')
    env.pop('SDL_AUDIODRIVER')
    result=subprocess.run([str(game),'--frames','120'],cwd=destination,env=env,
                          timeout=20,capture_output=True)
    assert result.returncode==0,(result.returncode,result.stderr)
    console=package/'ConsoleOriginal/OriginalConsole.exe'
    result=subprocess.run([str(console)],input=b'5\n',cwd=destination,env=env,
                          timeout=20,capture_output=True)
    assert result.returncode==0,result.stderr
    # A frozen Python interpreter uses the Windows ANSI code page for pipes,
    # whereas its attached console writes Unicode through WindowsConsoleIO.
    expected='КОНЦОВКА: ТРУСЛИВЫЙ ПИКМИ'
    assert any(expected in result.stdout.decode(encoding,errors='replace')
               for encoding in ('utf-8','cp1251','cp866')),repr(result.stdout)
    report={'manifest_files_verified':checked,'zip_crc':'PASS','original_bytes':'PASS',
            'runtime_python_path':'ABSENT','frozen_graphical_smoke':'PASS',
            'rendered_screens':13,'frozen_windows_window':'PASS',
            'frozen_original_console':'PASS','network_required':False,
            'extraction_folder':str(destination)}
    (ROOT/'build/portable-verification.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report,indent=2))


if __name__=='__main__':
    main()
