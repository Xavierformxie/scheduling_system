#·-*-.mode：·python·；.coding：：utf-8·-*.
import os
import sys
from PyInstaller.utils. hooks import collect_data_files,collect_submodules

block_cipher = None

#获取当前目录下所有·Python·文件

py_files = [f for f in os.listdir('.') if f.endswith('.py')]

#递归获取所有·JSON·文件

def get_all_json_files(directory):
    json_files = []
    for root,dirs,files in os.walk(directory):
        for file in files:
            if file.endswith('.json'):
                json_files.append((os.path.join(root,file),os.path.relpath(root,directory)))

    return json_files

json_files = get_all_json_files('.')

                  
# 读取requirements.txt 并收集所有依赖模块
try:
    with open('requirements.txt','r', encoding='utf-8') as f:
        requirements = f.read().splitlines()
except UnicodeDecodeError:
    try:
        with open('requirements.txt','r', encoding="gbk") as f:
            requirements = f.read().splitlines()
    except UnicodeDecodeError:
        print("无法读取requirements.txt文件，请检查文件编码。")
        requirements = []

hidden_imports =[]
for requirement in requirements:
    hidden_imports.extend(collect_submodules(requirement.split('==')[0]))

a= Analysis(
    py_files,
    pathex=[os.path.abspath('.')],
    binaries=[],
    datas=json_files,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe=EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='悦之神器',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)