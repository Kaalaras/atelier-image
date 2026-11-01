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
        self.assertEqual(saved['forge_preset'], 'klein')
        self.assertEqual(saved['sd_model_checkpoint'], 'flux-2-klein-4b-fp8.safetensors')
        self.assertEqual(saved['klein_t2i_step'], 4)
        self.assertEqual(saved['outdir_txt2img_samples'], '../../images')


if __name__ == '__main__':
    unittest.main()
