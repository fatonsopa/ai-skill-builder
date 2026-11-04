"""Package command validation distinguishes bundled scripts from user inputs."""
from copy import deepcopy
from pathlib import Path
import json
import sys
import tempfile
import unittest
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
from runtime.readme import check, render
from fixtures import PRODUCE

class ReadmeInputTests(unittest.TestCase):
    def package(self, root, argv):
        (root/'scripts').mkdir()
        (root/'scripts/normalize.py').write_text('import argparse\np=argparse.ArgumentParser();p.add_argument("--requirements");p.parse_args()\n')
        (root/'scripts/evaluate.py').write_text('# Bundled verification entry point.\n')
        (root/'SKILL.md').write_text('---\nname: normalize-customers\ndescription: Normalize supplied records.\n---\nRead supplied inputs.\n')
        (root/'config').mkdir()
        documentation = deepcopy(PRODUCE['documentation'])
        documentation['scenarios'][0]['command'] = {'argv': argv}
        data = {'schema_version':1,'name':'normalize-customers','documentation':documentation}
        (root/'config/documentation.json').write_text(json.dumps(data))
        (root/'README.md').write_text(render(data['name'], documentation))

    def test_external_requirement_input_is_not_a_bundled_package_file(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);self.package(root,['python3','scripts/normalize.py','--requirements','/absolute/requirements.txt'])
            result=check(root)
            self.assertTrue(result['passed'],result['findings'])

    def test_missing_bundled_script_is_still_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);self.package(root,['python3','scripts/missing.py'])
            result=check(root)
            self.assertFalse(result['passed'])
            self.assertTrue(any('scripts/missing.py' in row for row in result['findings']))

    def test_external_script_prerequisite_is_not_falsely_reported_as_missing(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);self.package(root,['python3','/absolute/user-provided-helper.py'])
            result=check(root)
            self.assertTrue(result['passed'],result['findings'])

    def test_user_input_suffix_does_not_make_it_a_bundled_script(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);self.package(root,['python3','scripts/normalize.py','--requirements','supplied-policy.py'])
            result=check(root)
            self.assertTrue(result['passed'],result['findings'])

    def test_missing_script_after_interpreter_option_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);self.package(root,['python3','-I','scripts/missing.py'])
            self.assertFalse(check(root)['passed'])
