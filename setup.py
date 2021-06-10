import os
import setuptools

setuptools.setup(
    name="ansible-specdoc",
    version="0.0.5",
    author="Lena Garber",
    author_email="lbgarber2@gmail.com",
    description=("A simple tool for generating Ansible collection documentation from module spec."),
    license="GNU General Public License v3.0",
    keywords="ansible",
    url="http://packages.python.org/ansible-specdoc",
    packages=['ansible_specdoc'],
    install_requires=[
        'PyYAML==5.4.1',
        'Jinja2==3.0.1',
        'redbaron==0.9.2'
    ],
    setup_requires=['setupext_janitor'],
    python_requires='>=3',
    entry_points={
        'console_scripts': ['ansible-specdoc=ansible_specdoc.cli:main'],
        'distutils.commands': ['clean = setupext_janitor.janitor:CleanCommand']
    }
)
