"""CLI Tool for generating Ansible collection documentation from module spec"""

import argparse
import importlib
import importlib.machinery
import importlib.util
import json
import os
import pathlib
import sys
from types import ModuleType
from typing import Optional, Dict, Any

import yaml

SPECDOC_META_VAR = 'specdoc_meta'


class SpecDocModule:
    """Class for processing Ansible modules"""

    def __init__(self) -> None:
        self._module_file: Optional[str] = None
        self._module_name: str = ''

        self._module_spec: Optional[importlib.machinery.ModuleSpec] = None
        self._module: Optional[ModuleType] = None

        self._metadata: Dict[str, Any] = {}

    def load_file(self, file: str, module_name: str = None) -> None:
        """Loads the given Ansible module file"""

        self._module_name = module_name or os.path.splitext(os.path.basename(file))[0]
        self._module_file = file

        self._module_spec = importlib.util.spec_from_file_location(
            self._module_name, self._module_file)
        self._module = importlib.util.module_from_spec(self._module_spec)
        self._module_spec.loader.exec_module(self._module)

        if not hasattr(self._module, SPECDOC_META_VAR):
            raise Exception('failed to parse module file {0}: specdoc_meta is not defined'
                            .format(self._module_file))

        self._metadata = getattr(self._module, SPECDOC_META_VAR)

    def load_str(self, content: str, module_name: str) -> None:
        """Loads the given Ansible module string"""

        self._module_name = module_name

        self._module_spec = importlib.util.spec_from_loader(self._module_name, loader=None)
        self._module = importlib.util.module_from_spec(self._module_spec)
        exec(content, self._module.__dict__)

        if not hasattr(self._module, SPECDOC_META_VAR):
            raise Exception('failed to parse module string {0}: specdoc_meta is not defined'
                            .format(self._module_name))

        self._metadata = getattr(self._module, SPECDOC_META_VAR)

    @staticmethod
    def __spec_to_doc(spec: Dict[str, Dict]) -> Dict[str, Any]:
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
                param_dict['suboptions'] = SpecDocModule.__spec_to_doc(param.get('options'))

            result[key] = param_dict

        return result

    def __generate_doc_dict(self) -> Dict[str, Any]:
        return {
            'module': self._module_name,
            'description': self._metadata.get('description'),
            'requirements': self._metadata.get('requirements'),
            'author': self._metadata.get('author'),
            'options': self.__spec_to_doc(self._metadata.get('spec'))
        }

    def generate_yaml(self) -> str:
        """Generates a YAML documentation string"""
        return yaml.dump(self.__generate_doc_dict())

    def generate_json(self) -> str:
        """Generates a JSON documentation string"""
        return json.dumps(self.__generate_doc_dict())


def get_ansible_root(base_dir: str) -> Optional[str]:
    """Gets the Ansible root directory for correctly importing Ansible collections"""

    path = pathlib.Path(base_dir)

    # Ensure path is a directory
    if not path.is_dir():
        path = path.parent

    # Check if ansible_collections is contained in base directory
    if 'ansible_collections' in os.listdir(str(path)):
        return str(path.absolute())

    # Check if base directory is a child of ansible_collections
    while path.name != 'ansible_collections':
        if path.name == '':
            return None

        path = path.parent

    return str(path.parent.absolute())


def main():
    """Entrypoint for CLI"""

    parser = argparse.ArgumentParser(description='Generate Ansible Module documentation from spec.')

    parser.add_argument('-s', '--stdin',
                        help='Read the module from stdin.', action='store_true')
    parser.add_argument('-n', '--module-name',
                        type=str, help='The name of the module (required for stdin)')

    parser.add_argument('-i', '--input_file',
                        type=str, help='The module to generate documentation from.')
    parser.add_argument('-o', '--output_file',
                        type=str, help='The file to output the documentation to.')
    parser.add_argument('-f', '--output_format',
                        type=str, default='yaml', choices=['yaml', 'json'],
                        help='The output format of the documentation.')
    args, _ = parser.parse_known_args()

    mod = SpecDocModule()

    # Add the Ansible collection directory to the path
    target_path = os.getcwd()
    if args.input_file is not None:
        target_path = str(pathlib.Path(args.input_file).absolute())

    ansible_root = get_ansible_root(target_path)

    if ansible_root is not None:
        sys.path.append(ansible_root)
    else:
        print('WARNING: The current directory is not at or '
              'below an Ansible collection: {...}/ansible_collections/{'
              'namespace}/{collection}/')

    # Load the module
    if args.stdin:
        if not args.module_name:
            parser.error('Module name must be specified for stdin input.')

        mod.load_str('\n'.join(sys.stdin), args.module_name)
    elif args.input_file is not None:
        mod.load_file(args.input_file, args.module_name)
    else:
        parser.error('No input source specified.')

    # Generate the output in the correct format
    output = ''
    if args.output_format == 'yaml':
        output = mod.generate_yaml()
    elif args.output_format == 'json':
        output = mod.generate_json()
    else:
        parser.error('Invalid format specified.')

    if args.output_file is not None:
        with open(args.output_file, 'w') as file:
            file.write(output)
    else:
        sys.stdout.write(output)


if __name__ == '__main__':
    main()
