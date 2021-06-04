import importlib.util
import importlib.machinery
import os
import yaml

from types import ModuleType
from typing import Optional, Dict, Any, Tuple


class SpecDocModule:
    def __init__(self, module_file: str) -> None:
        self._module_file = module_file
        self._module_name = os.path.splitext(os.path.basename(self._module_file))[0]

        self._module_spec: Optional[importlib.machinery.ModuleSpec] = None
        self._module: Optional[ModuleType] = None

        self._metadata: Dict[str, Any] = {}

    def parse_file(self) -> None:
        self._module_spec = importlib.util.spec_from_file_location('my_module', self._module_file)
        self._module = importlib.util.module_from_spec(self._module_spec)
        self._module_spec.loader.exec_module(self._module)

        if not hasattr(self._module, 'specdoc_meta'):
            raise Exception('failed to parse module file {0}: specdoc_meta is not defined'.format(self._module_file))

        self._metadata = getattr(self._module, 'specdoc_meta')

    @staticmethod
    def _spec_to_doc(spec: Dict[str, Dict]) -> Dict[str, Any]:
        result = {}

        for key, param in spec.items():
            param_dict = {
                'type': param.get('type'),
                'required': param.get('required') or False,
                'description': param.get('description') or []
            }

            if 'choices' in param:
                param_dict['choices'] = param.get('choices')

            if 'default' in param:
                param_dict['default'] = param.get('default')

            if 'elements' in param:
                param_dict['elements'] = param.get('elements')

            if 'options' in param:
                param_dict['suboptions'] = SpecDocModule._spec_to_doc(param.get('options'))

            result[key] = param_dict

        return result

    def _generate_doc_dict(self) -> Dict[str, Any]:
        return {
            'module': self._module_name,
            'description': self._metadata.get('description'),
            'requirements': self._metadata.get('requirements'),
            'author': self._metadata.get('author'),
            'options': self._spec_to_doc(self._metadata.get('spec'))
        }

    def generate_yaml(self) -> str:
        return yaml.dump(self._generate_doc_dict())


def main():
    mod = SpecDocModule('example/my_module.py')
    mod.parse_file()
    print(mod.generate_yaml())

if __name__ == '__main__':
    main()