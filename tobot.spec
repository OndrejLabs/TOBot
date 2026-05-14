# tobot.spec
import sys
import os
import platform
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None
current_os = platform.system()

if current_os == 'Darwin':
    # Mac needs .icns embedded into the .app bundle
    app_icon = os.path.join(SPECPATH, 'assets', 'icon.icns')
    app = BUNDLE(
        coll,
        name='TOBot.app',
        icon=app_icon,
        bundle_identifier='com.tobot.app',
        info_plist={
            'NSPrincipalClass': 'NSApplication',
            'NSAppleScriptEnabled': False,
            'NSHighResolutionCapable': 'True' # Ensures the GUI doesn't look blurry on Retina displays
        },
    )
elif current_os == 'Windows':
    # Windows needs .ico embedded into the .exe
    app_icon = os.path.join(SPECPATH, 'assets', 'icon.ico')
else:
    # PyInstaller actually ignores the icon flag entirely on Linux binaries.
    # Linux desktop icons are handled by .desktop files created by the user,
    # but we can pass the png just to satisfy the variable.
    app_icon = os.path.join(SPECPATH, 'assets', 'icon.png')

# Collect all asset files that customtkinter needs
ctk_datas = collect_data_files("customtkinter")

# Collect docling data files (models config, etc.)
#docling_datas = collect_data_files("docling")

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        *ctk_datas,
        (os.path.join(SPECPATH, 'config.example.toml'), 'app_data'),
        (os.path.join(SPECPATH, 'prompt.txt'), 'app_data'),
        (os.path.join(SPECPATH, 'mapping.csv'), 'app_data'),
        (os.path.join(SPECPATH, 'assets', 'icon.ico'), 'assets'),
        (os.path.join(SPECPATH, 'assets', 'icon.icns'), 'assets'),
        (os.path.join(SPECPATH, 'assets', 'icon.png'), 'assets'),
    ],
    hiddenimports=[
        'customtkinter',
        'PIL._tkinter_finder',
        # Docling pulls these in dynamically:
        #'docling.document_converter',
        #'docling.pipeline.standard_pdf_pipeline',
        # Pydantic v2 internals:
        'pydantic.deprecated.class_validators',
        'pydantic_core',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Exclude things you don't need to cut size:
        'matplotlib', 'scipy', 'IPython', 'notebook',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='TOBot',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,   # ← False = no black console window on Windows (GUI mode)
    #console=True   # ← Use True if you want CLI output visible
    icon='assets/icon.ico',  # add your icon here
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='TOBot',
)