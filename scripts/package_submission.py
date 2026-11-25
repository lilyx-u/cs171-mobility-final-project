#!/usr/bin/env python3
"""Zip everything the final submission asks for into one file.

Includes: all source code (without node_modules, build output or caches), the
data files and DATA.md, the process book PDF plus its Markdown source and
images, and the README. Run after build_process_book.py.

    python scripts/package_submission.py            -> submission/cs1710_final_YYYY-MM-DD.zip
    python scripts/package_submission.py --name final_v2
"""
import argparse, datetime, os, zipfile

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
SKIP_DIRS = {'node_modules', '.svelte-kit', 'build', '.output', '.vercel', '.netlify', 'submission',
             '.git', '__pycache__', '.claude', '.vscode'}
# The Google Doc export is skipped because the built process book already contains it.
# package-lock.json is kept: it pins the exact library versions the site was built with.
SKIP_FILES = {'.DS_Store', 'Thumbs.db', 'GoogleDoc_export_through_Milestone11.pdf'}

ap = argparse.ArgumentParser()
ap.add_argument('--name', default='final')
a = ap.parse_args()

out_dir = os.path.join(ROOT, 'submission')
os.makedirs(out_dir, exist_ok=True)
stamp = datetime.date.today().isoformat()
out = os.path.join(out_dir, f'cs1710_{a.name}_{stamp}.zip')

n = 0
with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as z:
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fn in filenames:
            if fn in SKIP_FILES or fn.endswith(('.zip', '.pyc')):
                continue
            full = os.path.join(dirpath, fn)
            rel = os.path.relpath(full, ROOT)
            z.write(full, os.path.join('cs171_final_project', rel))
            n += 1
print(f'wrote {out}  ({n} files, {os.path.getsize(out)/1e6:.1f} MB)')
pb = os.path.join(ROOT, 'process-book', 'CS1710_Process_Book_Final.pdf')
if not os.path.exists(pb):
    print('warning: process book PDF not found; run process-book/build_process_book.py first')
