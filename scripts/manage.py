"""Installation Windows locale. Aucune collecte, aucun changement système."""
import hashlib
from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path, PureWindowsPath
import shutil
import socket
import stat
import subprocess
import sys
import time
import urllib.error
import urllib.request
import zipfile
import webbrowser

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / '.runtime'
ENGINE = ROOT / 'app' / 'forge'


def sha256(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def download_verified(url, target, expected):
    target = Path(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.is_file() and sha256(target) == expected:
        print(f'Déjà vérifié : {target.name}', flush=True)
        return
    partial = target.with_suffix(target.suffix + '.part')
    offset = partial.stat().st_size if partial.exists() else 0
    if offset and sha256(partial) == expected:
        partial.replace(target)
        return
    request = urllib.request.Request(url, headers={'User-Agent': 'Atelier-Image/1.0'})
    if offset:
        request.add_header('Range', f'bytes={offset}-')
    print(f'Téléchargement : {target.name}', flush=True)
    try:
        response = urllib.request.urlopen(request, timeout=60)
    except urllib.error.HTTPError as error:
        if error.code == 416:
            partial.unlink(missing_ok=True)
        raise
    with response:
        resumed = response.status == 206
        if resumed and not response.headers.get('Content-Range', '').startswith(f'bytes {offset}-'):
            raise ValueError('Reprise HTTP incohérente ; fichier partiel conservé.')
        written = offset if resumed else 0
        last_progress = time.monotonic()
        with partial.open('ab' if resumed else 'wb') as output:
            while chunk := response.read(8 * 1024 * 1024):
                output.write(chunk)
                written += len(chunk)
                if time.monotonic() - last_progress > 10:
                    print(f'  {target.name} : {written / 1e9:.2f} Go reçus', flush=True)
                    last_progress = time.monotonic()
    if sha256(partial) != expected:
        partial.unlink(missing_ok=True)
        raise ValueError(f'SHA-256 incorrect : {target.name}. Relancez Installer.bat.')
    partial.replace(target)


def extract_zip(archive, destination):
    destination = Path(destination).resolve()
    with zipfile.ZipFile(archive) as package:
        # Validate every entry before writing even the first file.
        for member in package.infolist():
            relative = member.filename.replace('\\', '/')
            resolved = (destination / relative).resolve()
            if (not resolved.is_relative_to(destination)
                    or PureWindowsPath(relative).drive
                    or ':' in relative
                    or stat.S_ISLNK(member.external_attr >> 16)):
                raise ValueError(f'Archive refusée : {member.filename}')
        package.extractall(destination)


def environment():
    env = os.environ.copy()
    env.update({
        'UV_PYTHON_INSTALL_DIR': str(RUNTIME / 'python'),
        'UV_CACHE_DIR': str(RUNTIME / 'cache'),
        'UV_PYTHON_PREFERENCE': 'only-managed',
        'GRADIO_ANALYTICS_ENABLED': 'False',
        'HF_HUB_DISABLE_TELEMETRY': '1',
        'DO_NOT_TRACK': '1',
        'PYTHONUTF8': '1',
        'PYTHONUNBUFFERED': '1',
        'GIT_PYTHON_GIT_EXECUTABLE': str(RUNTIME / 'git/cmd/git.exe'),
    })
    env['PATH'] = os.pathsep.join([str(RUNTIME / 'uv'), str(RUNTIME / 'git/cmd'), env.get('PATH', '')])
    return env


def run(arguments, **kwargs):
    subprocess.run([str(x) for x in arguments], env=environment(), check=True, **kwargs)


def write_defaults(config, models):
    if config.exists():
        return
    modules = [str((models / name).resolve()) for name in
               ['text_encoder/qwen_3_4b.safetensors', 'VAE/flux2-vae.safetensors']]
    settings = {
        'forge_preset': 'klein',
        'sd_model_checkpoint': 'flux-2-klein-4b-fp8.safetensors',
        'forge_checkpoint_klein': 'flux-2-klein-4b-fp8.safetensors',
        'forge_additional_modules': modules,
        'forge_additional_modules_klein': modules,
        'klein_t2i_step': 4, 'klein_t2i_cfg': 1.0,
        'klein_t2i_sampler': 'Euler', 'klein_t2i_scheduler': 'Beta',
        'klein_t2i_width': 1024, 'klein_t2i_height': 1024,
        'outdir_txt2img_samples': '../../images',
        'outdir_img2img_samples': '../../images',
        'outdir_grids': '../../images',
        'outdir_save': '../../images/favorites',
        'samples_save': True,
    }
    config.parent.mkdir(parents=True, exist_ok=True)
    config.write_text(json.dumps(settings, indent=2), encoding='utf-8')


def setup():
    if sys.platform != 'win32':
        raise RuntimeError('Ce paquet est conçu pour Windows x64 avec une carte NVIDIA 16 Go.')
    print('Installation locale — prévoir 70 Go libres et un pilote NVIDIA 580 ou plus récent.', flush=True)
    print('Aucun inventaire du PC ni envoi de données. Internet requis pour les téléchargements.', flush=True)
    manifest = json.loads((ROOT / 'versions.json').read_text(encoding='utf-8'))
    downloads = RUNTIME / 'downloads'
    marker = ENGINE / '.atelier-revision'
    if (ENGINE / 'launch.py').exists() and (not marker.exists() or marker.read_text() != manifest['forge']['revision']):
        raise RuntimeError('Moteur existant différent. Installez cette version dans un nouveau dossier.')
    if not marker.exists():
        archive = downloads / 'forge.zip'
        download_verified(manifest['forge']['url'], archive, manifest['forge']['sha256'])
        extracted = RUNTIME / 'source'
        extract_zip(archive, extracted)
        source = extracted / ('sd-webui-forge-classic-' + manifest['forge']['revision'])
        shutil.copytree(source, ENGINE, dirs_exist_ok=True)
        marker.write_text(manifest['forge']['revision'])
    if not (RUNTIME / 'git/cmd/git.exe').exists():
        archive = downloads / 'git.zip'
        download_verified(manifest['git']['url'], archive, manifest['git']['sha256'])
        extract_zip(archive, RUNTIME / 'git')
    uv = RUNTIME / 'uv/uv.exe'
    python = RUNTIME / 'venv/Scripts/python.exe'
    if not python.exists():
        run([uv, 'venv', '--python', manifest['python'], '--seed', RUNTIME / 'venv'])
    # Model downloads do not mutate the Python environment and can overlap with it.
    with ThreadPoolExecutor(max_workers=3) as pool:
        futures = [pool.submit(download_verified, model['url'], ENGINE / 'models' / model['path'], model['sha256'])
                   for model in manifest['models']]
        run([uv, 'pip', 'install', '--python', python,
             '--index', 'https://download.pytorch.org/whl/cu130',
             'torch==' + manifest['torch'], 'torchvision==' + manifest['torchvision']])
        run([uv, 'pip', 'install', '--python', python, '-r', ENGINE / 'requirements.txt',
             'gradio==4.40.0', 'gradio_rangeslider==0.0.8'])
        run([python, 'launch.py', '--exit', '--uv'], cwd=ENGINE)
        run([uv, 'pip', 'check', '--python', python])
        for future in futures:
            future.result()
    write_defaults(ENGINE / 'config.json', ENGINE / 'models')
    (ROOT / 'images').mkdir(exist_ok=True)
    print('\nInstallation terminée. Double-cliquez sur Lancer.bat.', flush=True)


def port_is_open():
    with socket.socket() as connection:
        connection.settimeout(1)
        return connection.connect_ex(('127.0.0.1', 7860)) == 0


def start():
    python = RUNTIME / 'venv/Scripts/python.exe'
    if not python.exists() or not (ENGINE / 'config.json').exists():
        raise RuntimeError('Lancez Installer.bat avant Lancer.bat.')
    if port_is_open():
        raise RuntimeError('Le port 7860 est déjà utilisé. Arrêtez votre ancienne interface puis relancez Lancer.bat.')
    logs = ROOT / 'logs'
    logs.mkdir(exist_ok=True)
    logfile = logs / 'forge.log'
    command = [str(python), str(ENGINE / 'launch.py'), '--api', '--port', '7860',
               '--cuda-stream', '--cuda-malloc', '--skip-prepare-environment']
    with logfile.open('a', encoding='utf-8') as log:
        process = subprocess.Popen(command, cwd=ENGINE, env=environment(), stdout=log,
                                   stderr=subprocess.STDOUT, creationflags=subprocess.CREATE_NO_WINDOW)
    (RUNTIME / 'server.pid').write_text(str(process.pid))
    print('Démarrage... Le premier chargement peut prendre quelques minutes.', flush=True)
    for _ in range(180):
        if process.poll() is not None:
            raise RuntimeError(f'Le moteur s’est arrêté. Consultez {logfile}')
        if port_is_open():
            print('Interface : http://127.0.0.1:7860 — pour arrêter : Arreter.bat', flush=True)
            webbrowser.open('http://127.0.0.1:7860')
            return
        time.sleep(2)
    raise RuntimeError(f'Démarrage encore en cours. Consultez {logfile}, ou utilisez Arreter.bat.')


def stop():
    pidfile = RUNTIME / 'server.pid'
    if not pidfile.exists():
        print('Aucune session lancée par ce paquet.')
        return
    # Check exact executable arguments before touching a PID that Windows may have reused.
    code = '''
import psutil, sys
pid, launch = int(sys.argv[1]), sys.argv[2]
try:
    p = psutil.Process(pid)
    if launch not in p.cmdline():
        raise SystemExit('Arrêt refusé : ce processus ne correspond pas à Atelier Image.')
    for child in p.children(recursive=True):
        child.terminate()
    p.terminate()
except psutil.NoSuchProcess:
    pass
'''
    run([RUNTIME / 'venv/Scripts/python.exe', '-c', code, pidfile.read_text(), ENGINE / 'launch.py'])
    pidfile.unlink(missing_ok=True)
    print('Atelier Image arrêté. Vos images sont conservées.')


if __name__ == '__main__':
    try:
        actions = {'setup': setup, 'start': start, 'stop': stop}
        actions[sys.argv[1]]()
    except (KeyError, IndexError):
        raise SystemExit('Utilisation : manage.py setup|start|stop')
    except (Exception, KeyboardInterrupt) as error:
        print(f'\nERREUR : {error}\nRelancez Installer.bat si nécessaire. Les images sont conservées.', file=sys.stderr)
        raise SystemExit(1)
