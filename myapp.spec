# myapp.spec - PyInstaller spec file to collect mediapipe/eyetrax data and bundle gaze_model.pkl
# Run: pyinstaller myapp.spec --onefile

from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# Collect package data (this will include mediapipe/modules/*.binarypb etc.)
datas = []
try:
    datas += collect_data_files('mediapipe')
except Exception:
    # If mediapipe isn't installed in the environment used to build, this will fail.
    pass

# eyetrax may include package data; collect it if present
try:
    datas += collect_data_files('eyetrax')
except Exception:
    pass

# Also include the eyetrax/models directory from the venv site-packages so eyetrax can discover models at runtime
# Adjust the source path if your venv is located elsewhere. Destination places it under eyetrax/models inside the bundle.
try:
    import os
    import importlib
    eyetrax = importlib.import_module('eyetrax')
    model_dir = os.path.join(os.path.dirname(eyetrax.__file__), 'models')
    if os.path.isdir(model_dir):
        datas += [(model_dir, 'eyetrax/models')]
except Exception:
    pass

# Include your local model file (relative to the spec file location) and the whole img folder
datas += [ ('gaze_model.pkl', '.'), ('img', 'img') ]
datas += [ ('img/icon.png', '.') ]

# Hidden imports - collect submodules to avoid missing imports inside packages
hiddenimports = []
try:
    hiddenimports += collect_submodules('mediapipe')
except Exception:
    pass
try:
    hiddenimports += collect_submodules('eyetrax')
except Exception:
    pass
# Common additional hidden imports
hiddenimports += ['cv2']

a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=['rthook_eyetrax.py'],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='GazeMagnifierTest',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
)
