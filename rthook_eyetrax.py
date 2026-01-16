# Runtime hook to ensure eyetrax/models exists inside PyInstaller's _MEIPASS
# This runs before normal imports when the frozen app starts.
import sys
import os
import shutil

def _ensure_eyetrax_models():
    if not getattr(sys, 'frozen', False):
        return
    meipass = getattr(sys, '_MEIPASS', None)
    if not meipass:
        return

    dest = os.path.join(meipass, 'eyetrax', 'models')
    try:
        os.makedirs(dest, exist_ok=True)
    except Exception:
        return

    # candidate source locations inside the bundle where datas may have been placed
    src_alts = [
        os.path.join(meipass, 'eyetrax', 'models'),  # ideal
        os.path.join(meipass, 'models'),              # if placed at top-level
    ]

    for src in src_alts:
        if not os.path.isdir(src):
            continue
        for name in os.listdir(src):
            s = os.path.join(src, name)
            d = os.path.join(dest, name)
            if os.path.exists(d):
                continue
            try:
                if os.path.isdir(s):
                    shutil.copytree(s, d)
                else:
                    shutil.copy2(s, d)
            except Exception:
                # ignore copy errors; the presence of dest dir is the main requirement
                pass

_ensure_eyetrax_models()

