"""Prepare an isolated CI merge with current main; never push or alter owner branches."""
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def git(*args, check=True):
    return subprocess.run(['git', '-C', str(ROOT), *args], check=check,
                          text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def prepare():
    if git('status', '--porcelain').stdout.strip():
        raise SystemExit('Integration requires a clean disposable checkout.')
    git('fetch', '--no-tags', 'origin', 'main')
    main = git('rev-parse', 'origin/main').stdout.strip()
    base = git('merge-base', 'HEAD', 'origin/main').stdout.strip()
    original = git('show', f'{base}:README.md').stdout
    ours = (ROOT / 'README.md').read_text()
    theirs = git('show', 'origin/main:README.md').stdout
    merged = git('-c', 'user.name=RMS CI', '-c', 'user.email=ci@example.invalid',
                 'merge', '--no-commit', '--no-ff', 'origin/main', check=False)
    if merged.returncode:
        conflicts = git('diff', '--name-only', '--diff-filter=U').stdout.splitlines()
        # The current two branches only append separate README sections. Preserve both.
        # Every code conflict or non-append document edit fails for human resolution.
        if conflicts != ['README.md'] or not (ours.startswith(original) and theirs.startswith(original)):
            raise SystemExit('Integration conflict requires owner resolution: ' + ', '.join(conflicts))
        (ROOT / 'README.md').write_text(original + ours[len(original):] + theirs[len(original):])
        git('add', 'README.md')
        print('Resolved append-only README conflict in disposable checkout; retained both sections.')
    print('Integrated main:', main)
    print('Tested index tree:', git('write-tree').stdout.strip())


if __name__ == '__main__':
    prepare()
