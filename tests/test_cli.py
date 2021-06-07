"""Module for testing various CLI functionalities"""
import json
import os
import unittest
from typing import Dict, Any, Optional

import yaml
from ansible_specdoc.cli import SpecDocModule
from tests.test_modules import module_1

test_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'test_modules')


class TestDocs(unittest.TestCase):
    """Docs generation tests"""

    @staticmethod
    def assert_docs_dict_valid(original_spec: Dict[str, Any], new_spec: Dict[str, Any]):
        """Assert that the two specs are matching"""

        assert new_spec.get('description') == original_spec.get('description')
        assert new_spec.get('requirements') == original_spec.get('requirements')
        assert new_spec.get('author') == original_spec.get('author')

        def assert_spec_recursive(yaml_spec: Dict[str, Any], module_spec: Dict[str, Any]):
            """Recursively assert that spec options match"""

            for key, value in yaml_spec.items():
                assert value.get('type') == module_spec.get(key).get('type')
                assert value.get('required') == (module_spec.get(key).get('required') or False)
                assert value.get('description') == module_spec.get(key).get('description')

                options: Optional[Dict[str, Any]] = value.get('options')
                if options is not None:
                    assert_spec_recursive(options, module_spec.get('options'))

        assert_spec_recursive(new_spec.get('options'), original_spec.get('spec'))

    @staticmethod
    def test_docs_yaml_module_override():
        """Test that module names can be overridden"""
        module = SpecDocModule()

        module.load_file(os.path.join(test_dir, 'module_1.py'), 'really_cool_mod')

        assert yaml.safe_load(module.generate_yaml()).get('module') == 'really_cool_mod'

    def test_docs_file_yaml(self):
        """Test that the YAML output is valid"""
        module = SpecDocModule()

        module.load_file(os.path.join(test_dir, 'module_1.py'))

        output_yaml = yaml.safe_load(module.generate_yaml())

        assert output_yaml.get('module') == 'module_1'

        self.assert_docs_dict_valid(module_1.specdoc_meta, output_yaml)

    def test_docs_file_json(self):
        """Test that the JSON output is valid"""
        module = SpecDocModule()

        module.load_file(os.path.join(test_dir, 'module_1.py'))

        output_json = json.loads(module.generate_json())

        assert output_json.get('module') == 'module_1'

        self.assert_docs_dict_valid(module_1.specdoc_meta, output_json)
