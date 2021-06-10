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

import jinja2
import yaml
from redbaron import RedBaron

SPECDOC_META_VAR = 'specdoc_meta'


class SpecDocModule:
    """Class for processing Ansible modules"""

    def __init__(self) -> None:
        self._module_file: Optional[str] = None
        self._module_name: str = ''
        self._module_str: str = ''

        self._module_spec: Optional[importlib.machinery.ModuleSpec] = None
        self._module: Optional[ModuleType] = None

        self._metadata: Dict[str, Any] = {}

    def load_file(self, file: str, module_name: str = None) -> None:
        """Loads the given Ansible module file"""

        self._module_name = module_name or os.path.splitext(os.path.basename(file))[0]
        self._module_file = file
        with open(file, 'r') as module_file:
            self._module_str = module_file.read()

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
        self._module_str = content

        exec(content, self._module.__dict__)

        if not hasattr(self._module, SPECDOC_META_VAR):
            raise Exception('failed to parse module string {0}: specdoc_meta is not defined'
                            .format(self._module_name))

        self._metadata = getattr(self._module, SPECDOC_META_VAR)

    @staticmethod
    def __spec_to_doc(spec: Dict[str, Dict]) -> Dict[str, Any]:
        result = {}

        for key, param in spec.items():
            if param.get('doc_hide'):
                continue

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

    def generate_jinja2(self, tmpl_str: str) -> str:
        """Generates a text output from the given Jinja2 template"""
        env = jinja2.Environment(
            trim_blocks=True
        )

        template = env.from_string(tmpl_str)

        return template.render(self.__generate_doc_dict())


class CLI:
    """Class for handling all CLI functionality of ansible-specdoc"""

    def __init__(self):
        self._parser = argparse.ArgumentParser(
            description='Generate Ansible Module documentation from spec.')

        self._parser.add_argument('-s', '--stdin',
                                  help='Read the module from stdin.', action='store_true')
        self._parser.add_argument('-n', '--module-name',
                                  type=str, help='The name of the module (required for stdin)')

        self._parser.add_argument('-i', '--input_file',
                                  type=str, help='The module to generate documentation from.')

        self._parser.add_argument('-o', '--output_file',
                                  type=str, help='The file to output the documentation to.')
        self._parser.add_argument('-f', '--output_format',
                                  type=str, default='yaml',
                                  choices=['yaml', 'json', 'jinja2'],
                                  help='The output format of the documentation.')

        self._parser.add_argument('-j', '--inject',
                                  help='Inject the output documentation into the `DOCUMENTATION` '
                                       'field of input module.',
                                  action='store_true')

        self._parser.add_argument('-t', '--template_file',
                                  type=str,
                                  help='The file to use as the template for templated formats.')

        self._args, _ = self._parser.parse_known_args()

        self._mod = SpecDocModule()
        self._output = ''

    @staticmethod
    def _inject_docs(module_content: str, docs_content: str) -> str:
        """Injects docs_content into the DOCUMENTATION field of module_content"""

        red = RedBaron(module_content)

        doc_field = red.find('name', value='DOCUMENTATION')
        if doc_field is None or doc_field.parent is None:
            raise Exception('failed to inject documentation: '
                            'an empty DOCUMENTATION field must be specified')

        doc_field.parent.value.value = f'\'\'\'\n{docs_content}\'\'\''

        return red.dumps()

    @staticmethod
    def _get_ansible_root(base_dir: str) -> Optional[str]:
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

    def __add_ansible_collection_path(self):
        target_path = os.getcwd()
        if self._args.input_file is not None:
            target_path = str(pathlib.Path(self._args.input_file).absolute())

        ansible_root = self._get_ansible_root(target_path)

        if ansible_root is None:
            print('WARNING: The current directory is not at or '
                  'below an Ansible collection: {...}/ansible_collections/{'
                  'namespace}/{collection}/')
            return

        sys.path.append(ansible_root)

    def _load_input_source(self):
        if self._args.stdin:
            if not self._args.module_name:
                self._parser.error('Module name must be specified for stdin input')

            self._mod.load_str('\n'.join(sys.stdin), self._args.module_name)
            return

        if self._args.input_file is not None:
            self._mod.load_file(self._args.input_file, self._args.module_name)
            return

        self._parser.error('No input source specified')

    def _process_docs(self):
        if self._args.output_format == 'yaml':
            self._output = self._mod.generate_yaml()
            return

        if self._args.output_format == 'json':
            self._output = self._mod.generate_json()
            return

        if self._args.output_format == 'jinja2':
            if not self._args.template_file:
                self._parser.error('A template file must be specified for format Jinja2')

            with open(self._args.template_file) as file:
                template_str = file.read()

            self._output = self._mod.generate_jinja2(template_str)
            return

        self._parser.error('Invalid format specified.')

    def _try_inject_original_file(self):
        if self._args.inject is None:
            return

        if self._args.output_format not in {'yaml'}:
            self._parser.error(f'Format {self._args.output_format} is not supported for --inject.')

        with open(self._args.input_file, 'r+') as file:
            injected_module = self._inject_docs(file.read(), self._output)
            file.seek(0)
            file.write(injected_module)
            file.truncate()

    def _write_output(self):
        # Write the output
        if self._args.output_file is not None:
            with open(self._args.output_file, 'w') as file:
                file.write(self._output)
        else:
            sys.stdout.write(self._output)

    def execute(self):
        """Execute the CLI"""

        self.__add_ansible_collection_path()
        self._load_input_source()
        self._process_docs()
        self._try_inject_original_file()
        self._write_output()


def main():
    """Entrypoint for CLI"""

    cli = CLI()
    cli.execute()


if __name__ == '__main__':
    main()
