# ansible-specdoc

This is an experimental repo used to test the viability of static Ansible docs generation.

## Usage

```sh
usage: ansible-specdoc [-h] [-s] [-n MODULE_NAME] [-i INPUT_FILE] [-o OUTPUT_FILE] [-f {yaml,json,jinja2}] [-j] [-t TEMPLATE_FILE]

Generate Ansible Module documentation from spec.

optional arguments:
  -h, --help            show this help message and exit
  -s, --stdin           Read the module from stdin.
  -n MODULE_NAME, --module-name MODULE_NAME
                        The name of the module (required for stdin)
  -i INPUT_FILE, --input_file INPUT_FILE
                        The module to generate documentation from.
  -o OUTPUT_FILE, --output_file OUTPUT_FILE
                        The file to output the documentation to.
  -f {yaml,json,jinja2}, --output_format {yaml,json,jinja2}
                        The output format of the documentation.
  -j, --inject          Inject the output documentation into the `DOCUMENTATION` field of input module.
  -t TEMPLATE_FILE, --template_file TEMPLATE_FILE
                        The file to use as the template for templated formats.
```
