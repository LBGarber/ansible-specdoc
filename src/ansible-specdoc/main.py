import ast
import json
import os
import yaml
import argparse
import sys

from types import ModuleType
from typing import Optional, Dict, Any

class SpecDocModule:
    def __init__(self) -> None:
        self._module_file: Optional[str] = None
        self._module_name: str = ''

        self._metadata: Dict[str, Any] = {}

    def load_file(self, file: str) -> None:
        self._module_name = os.path.splitext(os.path.basename(file))[0]
        self._module_file = file

        with open(file, 'r') as f:
            tree = ast.parse(f.read())

        assign_op = self._get_var_assignment(tree, 'specdoc_meta')
        if assign_op is None:
            raise Exception('failed to parse module file {0}: specdoc_meta is not defined'.format(self._module_file))

        self._metadata = self._eval_dict(tree, assign_op.value)

    def load_str(self, module_name: str, content: str) -> None:
        self._module_name = module_name

        tree = ast.parse(content)

        assign_op = self._get_var_assignment(tree, 'specdoc_meta')
        if assign_op is None:
            raise Exception('failed to parse module string {0}: specdoc_meta is not defined'.format(self._module_file))

        self._metadata = self._eval_dict(tree, assign_op.value)

    def _eval_dict(self, root: ast.AST, node: ast.Dict) -> Dict[str, Any]:
        result = {}

        for i, key_node in enumerate(node.keys):
            value = node.values[i]

            result[key_node.s] = self._eval_val(root, value)

        return result

    def _eval_val(self, root: ast.AST, node: ast.AST):
        if isinstance(node, ast.Dict):
            return self._eval_dict(root, node)

        if isinstance(node, ast.List):
            return [self._eval_val(root, v) for v in node.elts]

        if isinstance(node, ast.Name):
            assign_op = self._get_var_assignment(root, node.id)
            if isinstance(assign_op.value, ast.Dict):
                return self._eval_dict(root, assign_op.value)

            return self._eval_val(root, assign_op.value)

        return ast.literal_eval(node)

    def _get_var_assignment(self, tree: ast.AST, var_name: str) -> Optional[ast.Assign]:
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign) and node.targets[0].id == var_name:
                return node

        return None

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

    def generate_json(self, pretty_print=True) -> str:
        return json.dumps(self._generate_doc_dict(), sort_keys=True, indent=(4 if pretty_print else None))

def main():
    parser = argparse.ArgumentParser(description='Generate Ansible Module documentation from spec.')

    parser.add_argument('-s', '--stdin', help='Read the module from stdin.', action='store_true')
    parser.add_argument('-i', '--input_file', type=str, help='The module to generate documentation from.')
    parser.add_argument('-o', '--output_file', type=str, help='The file to output the documentation to.')

    parser.add_argument('-f', '--output_format', type=str, default='yaml', choices=['yaml', 'json'], help='The output format of the documentation.')
    parser.add_argument('-p', '--pretty_print', help='Make the output pretty-printed.', action='store_true')

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
        output = mod.generate_json(pretty_print=args.pretty_print)
    else:
        parser.error('Invalid format specified.')

    if args.output_file is not None:
        with open(args.output_file, 'w') as f:
            f.write(output)
    else:
        sys.stdout.write(output + '\n')


if __name__ == '__main__':
    main()