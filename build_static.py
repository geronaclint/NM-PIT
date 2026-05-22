"""Copy static/ into public/static/ before Vercel deploy (keeps both folders in sync)."""
import os
import shutil

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ROOT, 'static')
DST = os.path.join(ROOT, 'public', 'static')

for sub in ('css', 'js'):
    os.makedirs(os.path.join(DST, sub), exist_ok=True)
    src_dir = os.path.join(SRC, sub)
    dst_dir = os.path.join(DST, sub)
    if os.path.isdir(src_dir):
        for name in os.listdir(src_dir):
            shutil.copy2(os.path.join(src_dir, name), os.path.join(dst_dir, name))

print('Synced static/ -> public/static/')
