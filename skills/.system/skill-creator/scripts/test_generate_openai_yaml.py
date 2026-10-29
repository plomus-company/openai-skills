"""Round-trip tests for generated interface YAML, without API calls."""
import contextlib
import io
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import yaml
from generate_openai_yaml import write_openai_yaml, yaml_quote


class YamlQuotingTests(unittest.TestCase):
    def test_control_characters_round_trip(self):
        for value in ['before\rafter', 'before\x85after', 'before\0after',
                      'before\x07after', 'before\x1bafter']:
            with self.subTest(value=repr(value)):
                self.assertEqual(yaml.safe_load(yaml_quote(value)), value)

    def test_existing_string_cases_round_trip(self):
        for value in ['', 'yes', '123', '한국어 😀', 'a"b\\c\nd',
                      'one\ttwo', 'one\u2028two\u2029three', 'long text ' * 40]:
            with self.subTest(value=repr(value)):
                quoted = yaml_quote(value)
                self.assertTrue(quoted.startswith('"') and quoted.endswith('"'))
                self.assertEqual(yaml.safe_load(quoted), value)

    def test_generated_document_preserves_prompt(self):
        with tempfile.TemporaryDirectory() as root, contextlib.redirect_stdout(io.StringIO()):
            prompt = 'Use $sample: first\r\nsecond\x85third\0end'
            result = write_openai_yaml(root, 'sample', ['default_prompt=' + prompt])
            parsed = yaml.safe_load(result.read_text())
            self.assertEqual(parsed['interface']['default_prompt'], prompt)
            self.assertEqual(parsed['interface']['display_name'], 'Sample')

    def test_cli_preserves_carriage_return(self):
        with tempfile.TemporaryDirectory() as root:
            prompt = 'Use $sample: first\rsecond'
            result = subprocess.run([sys.executable, str(Path(__file__).with_name('generate_openai_yaml.py')),
                                     root, '--name', 'sample', '--interface', 'default_prompt=' + prompt],
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            parsed = yaml.safe_load((Path(root) / 'agents/openai.yaml').read_text())
            self.assertEqual(parsed['interface']['default_prompt'], prompt)


if __name__ == '__main__':
    unittest.main()
