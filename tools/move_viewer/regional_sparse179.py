"""Convert the regional mod's full-sector LBA179 overlay into a 2-byte overlay."""
import hashlib
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import tools.move_viewer.swap_mod as s  # noqa: E402

cfg = s.load_config(repo_root=s.ROOT)
disc, = s.require_paths(cfg, ('inputs.bag2_disc',))
stock = s.read_user(disc, 179, 1)[100:102]
OLD = ('offset = 366592\nfile = "payload/003_0000179.bin"\n'
       'sha256 = "9f3fa1984dada7e1dbea7560a94f29945f78702ba40fce1b3bcd8845dabb9b38"\n'
       'expected_sha256 = "fa66eef68e26a72f9884b174ad25ba36cd0ef66449b3e76b6cc3cb809f8cde75"')
roots = [Path('mods-src/bag2jp.localization.regional/1.0.0')]
exp_install = cfg.get('paths', {}).get('experimental_install')
if exp_install:
    roots.append(Path(exp_install) / 'mods/installed/bag2jp.localization.regional/1.0.0')
for root in roots:
    m = root / 'manifest.toml'
    raw = m.read_bytes()
    crlf = b'\r\n' in raw
    text = raw.decode('utf-8').replace('\r\n', '\n')
    assert text.count(OLD) == 1, root
    full = (root / 'payload/003_0000179.bin').read_bytes()
    assert hashlib.sha256(full).hexdigest().startswith('9f3fa198')
    new = full[100:102]
    shutil.copy2(m, str(m) + '.bak-20261119-sparse179')
    (root / 'payload/003_0000179_logo.bin').write_bytes(new)
    text = text.replace(OLD, f'offset = 366692\nfile = "payload/003_0000179_logo.bin"\n'
                        f'sha256 = "{hashlib.sha256(new).hexdigest()}"\n'
                        f'expected_sha256 = "{hashlib.sha256(stock).hexdigest()}"')
    if crlf:
        text = text.replace('\n', '\r\n')
    m.write_bytes(text.encode('utf-8'))
    print(root, new.hex(), stock.hex())
