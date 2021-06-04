import importlib.util
import importlib.machinery
import json
import os
import yaml
import importlib
import argparse
import sys

from types import ModuleType
from typing import Optional, Dict, Any


class SpecDocModule:
    def __init__(self) -> None:
        self._module_file: Optional[str] = None
        self._module_name: str = ''

        self._module_spec: Optional[importlib.machinery.ModuleSpec] = None
        self._module: Optional[ModuleType] = None

        self._metadata: Dict[str, Any] = {}

    def load_file(self, file: str) -> None:
        self._module_name = os.path.splitext(os.path.basename(file))[0]
        self._module_file = file

        self._module_spec = importlib.util.spec_from_file_location(self._module_name, self._module_file)
        self._module = importlib.util.module_from_spec(self._module_spec)
        self._module_spec.loader.exec_module(self._module)

        if not hasattr(self._module, 'specdoc_meta'):
            raise Exception('failed to parse module file {0}: specdoc_meta is not defined'.format(self._module_file))

        self._metadata = getattr(self._module, 'specdoc_meta')

    def load_str(self, module_name: str, content: str) -> None:
        self._module_name = module_name

        self._module_spec = importlib.util.spec_from_loader(self._module_name, loader=None)
        self._module = importlib.util.module_from_spec(self._module_spec)
        exec(content, self._module.__dict__)

        if not hasattr(self._module, 'specdoc_meta'):
            raise Exception('failed to parse module string {0}: specdoc_meta is not defined'.format(self._module_name))

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

    def generate_json(self) -> str:
        return json.dump(self._generate_doc_dict())

def main():
    parser = argparse.ArgumentParser(description='Generate Ansible Module documentation from spec.')

    parser.add_argument('-s', '--stdin', help='Read the module from stdin.', action='store_true')
    parser.add_argument('-i', '--input_file', type=str, help='The module to generate documentation from.')
    parser.add_argument('-o', '--output_file', type=str, help='The file to output the documentation to.')
    parser.add_argument('-f', '--output_format', type=str, default='yaml', choices=['yaml', 'json'], help='The output format of the documentation.')
    args, leftovers = parser.parse_known_args()

    mod = SpecDocModule()

    if args.stdin:
        mod.load_str('my-module', '\n'.join(sys.stdin))
    elif args.input_file is not None:
        mod.load_file(args.input_file)
    else:
        parser.error('No input source specified.')

    output = ''
    if args.output_format == 'yaml':
        output = mod.generate_yaml()
    elif args.output_format == 'json':
        output = mod.generate_json()
    else:
        parser.error('Invalid format specified.')

    if args.output_file is not None:
        with open(args.output_file, 'w') as f:
            f.write(output)
    else:
        sys.stdout.write(output)

if __name__ == '__main__':
    main()