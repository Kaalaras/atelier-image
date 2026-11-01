import hashlib
import io
import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import manage


class Response(io.BytesIO):
    def __init__(self, data, status=200):
        super().__init__(data)
        self.status = status
        self.headers = {}


class InstallerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='atelier espace é ')
        self.root = Path(self.temp.name)
        self.addCleanup(self.temp.cleanup)
        self.body = b'a verified model file'
        self.sha = hashlib.sha256(self.body).hexdigest()

    def test_valid_cache_never_connects(self):
        target = self.root / 'modèle.bin'
        target.write_bytes(self.body)
        with patch('manage.urllib.request.urlopen', side_effect=AssertionError('network')):
            manage.download_verified('https://example.test/model', target, self.sha)
        self.assertEqual(target.read_bytes(), self.body)

    def test_bad_download_does_not_replace_existing_file(self):
        target = self.root / 'model.bin'
        target.write_bytes(b'previous file')
        with patch('manage.urllib.request.urlopen', return_value=Response(b'corrupted')):
            with self.assertRaisesRegex(ValueError, 'SHA-256'):
                manage.download_verified('https://example.test/model', target, self.sha)
        self.assertEqual(target.read_bytes(), b'previous file')

    def test_resume_ignored_by_server_restarts_without_appending(self):
        target = self.root / 'model.bin'
        target.with_suffix('.bin.part').write_bytes(b'a verified')
        with patch('manage.urllib.request.urlopen', return_value=Response(self.body)):
            manage.download_verified('https://example.test/model', target, self.sha)
        self.assertEqual(target.read_bytes(), self.body)

    def test_range_response_resumes_from_correct_offset(self):
        target = self.root / 'model.bin'
        target.with_suffix('.bin.part').write_bytes(self.body[:5])
        response = Response(self.body[5:], 206)
        response.headers['Content-Range'] = f'bytes 5-{len(self.body)-1}/{len(self.body)}'
        with patch('manage.urllib.request.urlopen', return_value=response) as opened:
            manage.download_verified('https://example.test/model', target, self.sha)
        self.assertEqual(opened.call_args.args[0].get_header('Range'), 'bytes=5-')
        self.assertEqual(target.read_bytes(), self.body)

    def test_zip_traversal_rejected_before_any_extraction(self):
        archive = self.root / 'bad.zip'
        with zipfile.ZipFile(archive, 'w') as z:
            z.writestr('safe.txt', 'safe')
            z.writestr('../escaped.txt', 'unsafe')
        with self.assertRaises(ValueError):
            manage.extract_zip(archive, self.root / 'extracted')
        self.assertFalse((self.root / 'escaped.txt').exists())
        self.assertFalse((self.root / 'extracted' / 'safe.txt').exists())

    def test_safe_zip_supports_unicode_and_spaces(self):
        archive = self.root / 'safe.zip'
        with zipfile.ZipFile(archive, 'w') as z:
            z.writestr('répertoire espace/file.txt', 'ok')
        manage.extract_zip(archive, self.root / 'extracted')
        self.assertEqual((self.root / 'extracted/répertoire espace/file.txt').read_text(), 'ok')

    def test_defaults_preserve_existing_user_configuration(self):
        config = self.root / 'config.json'
        config.write_text('{"custom": 42}', encoding='utf-8')
        manage.write_defaults(config, self.root / 'models')
        self.assertEqual(json.loads(config.read_text()), {'custom': 42})

    def test_first_config_selects_model_and_visible_images_folder(self):
        config = self.root / 'config.json'
        manage.write_defaults(config, self.root / 'models')
        saved = json.loads(config.read_text())
        self.assertEqual(saved['VERSION_UID'], 'PY313')
        self.assertEqual(saved['forge_preset'], 'klein')
        self.assertEqual(saved['sd_model_checkpoint'], 'flux-2-klein-4b-fp8.safetensors')
        self.assertEqual(saved['klein_t2i_step'], 4)
        self.assertEqual(saved['outdir_txt2img_samples'], '../../images')

    def test_interrupted_source_copy_can_be_retried(self):
        source = self.root / 'source'
        source.mkdir()
        (source / 'launch.py').write_text('# complete source')
        engine = self.root / 'engine'

        def interrupt(*args, **kwargs):
            engine.mkdir(exist_ok=True)
            (engine / 'launch.py').write_text('# incomplete')
            raise OSError('simulated interruption')

        with patch('manage.shutil.copytree', side_effect=interrupt):
            with self.assertRaises(OSError):
                manage.install_source(source, engine, 'revision123')
        manage.install_source(source, engine, 'revision123')
        self.assertEqual((engine / 'launch.py').read_text(), '# complete source')
        self.assertEqual((engine / '.atelier-revision').read_text(), 'revision123')

    def test_concurrent_lifecycle_operation_is_rejected(self):
        lock = self.root / 'operation.lock'
        with manage.operation_lock(lock):
            with self.assertRaisesRegex(RuntimeError, 'opération'):
                with manage.operation_lock(lock):
                    self.fail('second operation entered')
        with manage.operation_lock(lock):
            pass

    def test_setup_configures_defaults_before_engine_creates_its_config(self):
        engine = self.root / 'app/forge'
        runtime = self.root / '.runtime'
        for path in [engine / 'launch.py', runtime / 'git/cmd/git.exe', runtime / 'venv/Scripts/python.exe']:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.touch()
        (engine / '.atelier-revision').write_text('test-revision')
        (engine / 'requirements.txt').write_text('Pillow==13.0.0\n')
        (self.root / 'versions.json').write_text(json.dumps({
            'release': 'test', 'python': '3.13.15', 'compatibility': {'Pillow': '10.4.0'},
            'forge': {'revision': 'test-revision'}, 'models': []}))

        def external_command(arguments, **kwargs):
            if 'launch.py' in arguments and not (engine / 'config.json').exists():
                (engine / 'config.json').write_text('{"VERSION_UID":"PY313"}')

        with patch.multiple(manage, ROOT=self.root, RUNTIME=runtime, ENGINE=engine):
            with patch('manage.run', side_effect=external_command):
                manage.setup()
        self.assertEqual(json.loads((engine / 'config.json').read_text())['forge_preset'], 'klein')


if __name__ == '__main__':
    unittest.main()
