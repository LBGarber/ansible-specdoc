import unittest
from typing import Dict, Any, Optional

import yaml
import json

from cli import SpecDocModule
from test_modules import module_1


class TestDocs(unittest.TestCase):
    @staticmethod
    def assert_docs_dict_valid(original_spec: Dict[str, Any], new_spec: Dict[str, Any]):
        assert new_spec.get('description') == original_spec.get('description')
        assert new_spec.get('requirements') == original_spec.get('requirements')
        assert new_spec.get('author') == original_spec.get('author')

        def assert_spec_recursive(yaml_spec: Dict[str, Any], module_spec: Dict[str, Any]):
            for k, v in yaml_spec.items():
                assert v.get('type') == module_spec.get(k).get('type')
                assert v.get('required') == (module_spec.get(k).get('required') or False)
                assert v.get('description') == module_spec.get(k).get('description')

                options: Optional[Dict[str, Any]] = v.get('options')
                if options is not None:
                    assert_spec_recursive(options, module_spec.get('options'))

        assert_spec_recursive(new_spec.get('options'), original_spec.get('spec'))

    def test_docs_yaml_module_override(self):
        m = SpecDocModule()

        m.load_file('test_modules/module_1.py', 'really_cool_mod')

        assert yaml.safe_load(m.generate_yaml()).get('module') == 'really_cool_mod'

    def test_docs_file_yaml(self):
        m = SpecDocModule()

        m.load_file('test_modules/module_1.py')

        output_yaml = yaml.safe_load(m.generate_yaml())

        assert output_yaml.get('module') == 'module_1'

        self.assert_docs_dict_valid(module_1.specdoc_meta, output_yaml)

    def test_docs_file_json(self):
        m = SpecDocModule()

        m.load_file('test_modules/module_1.py')

        output_json = json.loads(m.generate_json())

        assert output_json.get('module') == 'module_1'

        self.assert_docs_dict_valid(module_1.specdoc_meta, output_json)
