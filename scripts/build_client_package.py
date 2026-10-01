"""Build a source plugin or self-contained Windows client from pinned inputs."""
import argparse
import hashlib
from pathlib import Path
import zipfile

from client_manifests import encoded, manifests
from client_package_inputs import entries, hashes, inputs, qualify as qualify_root, unchanged

ROOT = Path(__file__).resolve().parents[1]


def qualify(mode):
    return qualify_root(ROOT, mode)


def archive(files, target):
    files = dict(files)
    files['PAYLOAD-SHA256SUMS'] = ''.join(f'{digest}  {name}\n'
        for name, digest in sorted(hashes(files).items())).encode()
    with zipfile.ZipFile(target, 'x', compression=zipfile.ZIP_STORED) as output:
        for name, data in sorted(files.items()):
            info = zipfile.ZipInfo(name, (1980, 1, 1, 0, 0, 0))
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            output.writestr(info, data)


def build(output, native=False, mode='dev'):
    version, head = qualify(mode)
    output = Path(output).absolute()
    if output.exists():
        raise FileExistsError('output must be a new directory')
    original = inputs(ROOT, mode)
    files = {name.removeprefix('client-plugin/'): data for name, data in original.items()
             if name.startswith('client-plugin/')}
    files.update(manifests(version, native))
    files['LICENSE'] = original['LICENSE']
    receipt = {'status': 'DEVELOPMENT_CANDIDATE' if mode == 'dev' else 'RELEASE_CANDIDATE',
        'version': version, 'head': head, 'source_sha256': hashes(original),
        'does_not_prove': ['installed client acceptance', 'marketplace admission', 'clean OS compatibility']}
    output.mkdir(parents=True)
    if native:
        from native_client_build import freeze
        payload, details = freeze(ROOT, output, version, head)
        files.pop('server/serve.py')
        files.update(payload)
        receipt.update(details)
    else:
        files.update({'server/' + name: data for name, data in original.items() if name.startswith('src/canon/')})
    unchanged(ROOT, original, mode, head)
    files['QUALIFICATION.json'] = encoded(receipt)
    label = '-dev' if mode == 'dev' else ''
    name = f'canon-{version}{label}-' + ('win-x64' if native else 'source-plugin')
    artifacts = [output / (name + suffix) for suffix in (('.zip', '.mcpb') if native else ('.zip',))]
    for target in artifacts:
        archive(files, target)
    (output / 'SHA256SUMS').write_text(''.join(f'{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.name}\n' for p in artifacts))
    (output / 'build-receipt.json').write_bytes(encoded(receipt))
    return artifacts


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output')
    parser.add_argument('--native', action='store_true')
    parser.add_argument('--mode', choices=('dev', 'release'), default='dev')
    args = parser.parse_args()
    for item in build(args.output, args.native, args.mode):
        print(item)
