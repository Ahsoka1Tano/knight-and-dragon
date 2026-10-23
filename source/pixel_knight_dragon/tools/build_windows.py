"""Create a portable Windows submission containing both games and review sources."""
import hashlib
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import zipfile

ROOT=Path(__file__).resolve().parents[1]
PROJECT=ROOT.parent
ORIGINAL=PROJECT/'knight and dragon.py'
EXPECTED='26e69e591d06e0e0959ebbe3310f2adb4b1354c45f4c89abb60885a2f841151e'
BUILD=ROOT/'build'
PACKAGE=PROJECT/'Для_преподавателя'


def verify_original():
    actual=hashlib.sha256(ORIGINAL.read_bytes()).hexdigest()
    if actual!=EXPECTED:
        raise RuntimeError('Original file differs from the recorded original. Build stopped.')


def run(args):
    subprocess.run([sys.executable,'-m','PyInstaller','--noconfirm','--clean',*args],
                   cwd=PROJECT,check=True)


def main():
    verify_original()
    BUILD.mkdir(exist_ok=True)
    # Construct an ICO with a PNG payload from our own raster knight.
    import os
    os.environ.setdefault('SDL_VIDEODRIVER','dummy')
    os.environ.setdefault('SDL_AUDIODRIVER','dummy')
    import pygame
    pygame.init()
    sheet=pygame.image.load(str(ROOT/'assets/knight_idle.png'))
    icon=pygame.transform.scale(sheet.subsurface((25,14,48,77)),(64,64))
    png=BUILD/'icon.png'
    pygame.image.save(icon,str(png))
    data=png.read_bytes()
    ico=BUILD/'knight.ico'
    ico.write_bytes(struct.pack('<HHH',0,1,1)+struct.pack('<BBBBHHII',64,64,0,0,1,32,len(data),22)+data)
    pygame.quit()
    common=['--onedir','--distpath',str(BUILD/'frozen'),'--specpath',str(BUILD)]
    run([*common,'--windowed','--name','KnightDragon','--icon',str(ico),
         '--workpath',str(BUILD/'work-game'),'--paths',str(PROJECT),
         '--add-data',f'{ROOT / "assets"};pixel_knight_dragon/assets',
         '--exclude-module','tkinter',str(ROOT/'run_game.py')])
    # Pygame's hook collects an unused default font; this game uses PT Sans.
    # Remove that generated-build asset so the delivery has just the chosen font.
    for unused in (BUILD/'frozen/KnightDragon').rglob('freesansbold.ttf'):
        unused.unlink()
    # This executable is built DIRECTLY from the student's unmodified source.
    run([*common,'--console','--name','OriginalConsole','--icon',str(ico),
         '--workpath',str(BUILD/'work-console'),str(ORIGINAL)])
    assemble()


def assemble():
    verify_original()
    PACKAGE.mkdir(exist_ok=True)
    shutil.copytree(BUILD/'frozen/KnightDragon',PACKAGE/'Game',dirs_exist_ok=True)
    shutil.copytree(BUILD/'frozen/OriginalConsole',PACKAGE/'ConsoleOriginal',dirs_exist_ok=True)
    shutil.copy2(ORIGINAL,PACKAGE/ORIGINAL.name)
    assert (PACKAGE/ORIGINAL.name).read_bytes()==ORIGINAL.read_bytes()
    # Only reviewable project files, never virtual environments or build caches.
    source=PACKAGE/'source/pixel_knight_dragon'
    shutil.copytree(ROOT,source,dirs_exist_ok=True,ignore=shutil.ignore_patterns(
        '.venv','.tmp','build','__pycache__','*.pyc','screenshots'))
    shutil.copy2(ORIGINAL,PACKAGE/'source'/ORIGINAL.name)
    shutil.copytree(ROOT/'licenses',PACKAGE/'licenses',dirs_exist_ok=True)
    shutil.copytree(ROOT/'screenshots',PACKAGE/'screenshots',dirs_exist_ok=True)
    (PACKAGE/'START_GAME.bat').write_bytes(b'@echo off\r\nstart "" "%~dp0Game\\KnightDragon.exe"\r\n')
    (PACKAGE/'START_ORIGINAL.bat').write_bytes(
        b'@echo off\r\nchcp 65001 >nul\r\nset PYTHONIOENCODING=utf-8\r\n"%~dp0ConsoleOriginal\\OriginalConsole.exe"\r\npause\r\n')
    readme='''РЫЦАРЬ И ДРАКОН — КОМПЛЕКТ ДЛЯ ПРЕПОДАВАТЕЛЯ

1. Распакуйте ВЕСЬ архив в обычную папку.
2. START_GAME.bat — новая пиксельная игра.
3. START_ORIGINAL.bat — первоначальная консольная работа.

Windows 11 x64. Python и библиотеки уже встроены в EXE.
Интернет, pip, установщик и права администратора для игры не нужны.
Не вынимайте EXE из папок Game и ConsoleOriginal: рядом находятся их библиотеки.

knight and dragon.py — точная, побайтовая копия первоначальной работы студента.
В первоначальном файле не исправлялись даже форматирование и формулировки.
ConsoleOriginal.exe собран непосредственно из этого файла.

source/pixel_knight_dragon — отдельная дополнительная игра и её ресурсы.
source/knight and dragon.py — ещё одна идентичная копия оригинала для проверки.
source/pixel_knight_dragon/README.md — подробности, архитектура, запуск из Python.
screenshots — реальные кадры из дополнительной игры.
licenses — лицензии свободных компонентов.
MANIFEST_SHA256.txt — контрольные суммы файлов комплекта.

Управление: A/D или стрелки — идти; Space — прыгнуть; J — меч;
K — щит на следующий удар; H — зелье; E — предложение рядом с драконом.
Идите налево к выходу, чтобы сбежать. Esc — пауза; M — звук; F11 — полный экран.
В меню: мышь или стрелки вверх/вниз и Enter. После концовки — Enter для повтора.

ВНИМАНИЕ: это законченный небольшой учебный прототип с одним боссом.
Новая пиксельная версия создана дополнительно с помощью Codex;
она не подменяет исходную университетскую работу.
'''
    (PACKAGE/'ПРОЧИТАЙ_МЕНЯ.txt').write_text(readme,encoding='utf-8-sig')
    sums=[]
    for p in sorted(PACKAGE.rglob('*')):
        if p.is_file() and p.name!='MANIFEST_SHA256.txt':
            sums.append(f'{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.relative_to(PACKAGE).as_posix()}')
    (PACKAGE/'MANIFEST_SHA256.txt').write_text('\n'.join(sums)+'\n',encoding='utf-8')
    verify_original()
    archive=PROJECT/'Для_преподавателя.zip'
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for p in sorted(PACKAGE.rglob('*')):
            if p.is_file():
                z.write(p,p.relative_to(PROJECT))
    print(f'Portable submission: {PACKAGE}')
    print(f'ZIP: {archive} ({archive.stat().st_size/1024/1024:.1f} MiB)')
    print(f'Original SHA-256 unchanged: {EXPECTED}')


if __name__=='__main__':
    if '--package-only' in sys.argv:
        assemble()
    else:
        main()
