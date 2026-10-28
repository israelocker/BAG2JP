"""Add the international 2P VS screen (option vs_screen, plugin bag2jp.vs_screen, resource vs_hd)
to bag2jp.localization.regional. Layers come from ~/work/vs/vs_hd (tools/build_vs.py)."""
import os, shutil, sys
BLOCK = '''[[option]]
feature = "regional"
id = "vs_screen"
label = "VS loading screen"
description = "2-player loading screen: name text (Japanese) or the arcade VS art with flames and portraits (international), rendered in HD."
type = "choice"
default = "international"

[[option.choice]]
value = "japanese"
label = "Japanese"

[[option.choice]]
value = "international"
label = "International (HD)"

[[resource]]
feature = "regional"
id = "vs_hd"
label = "VS screen layers"
description = "HD layers of the international VS screen (PNG), built from the US disc."
format = "directory"
default = "vs_hd"
required = false

[[plugin]]
feature = "regional"
id = "bag2jp.vs_screen"
'''
def append(pkg):
    m = open(f'{pkg}/manifest.toml').read()
    if 'id = "vs_screen"' not in m:
        i = m.index('[[plugin]]')
        m = m[:i] + BLOCK + '\n' + m[i:]
        open(f'{pkg}/manifest.toml', 'w').write(m)
    shutil.copytree(os.path.expanduser('~/work/vs/vs_hd'), f'{pkg}/vs_hd', dirs_exist_ok=True)
    return 1
if __name__ == '__main__':
    print(append(sys.argv[1]))
