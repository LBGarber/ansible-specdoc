"""Module for testing docs generation functionality"""

DOCUMENTATION = ''

my_module_dict_spec = {
    'my-int': {
        'type': 'int',
        'required': True,
        'description': ['A really cool required int']
    },
    'my-bool': {
        'type': 'bool',
        'description': [
            'A really cool bool that does stuff',
            'Here\'s another line :)'
        ]
    }
}

my_module_spec = {
    'my-string': {
        'type': 'str',
        'required': True,
        'description': ['A really cool string that does stuff!']
    },
    'my-list': {
        'type': 'list',
        'elements': 'str',
        'description': ['A really cool list of strings']
    },
    'my-dict': {
        'type': 'dict',
        'options': my_module_dict_spec,
        'description': ['A really cool dict']
    },

}

specdoc_meta = {
    'description': [
        'My really cool Ansible module!'
    ],
    'requirements': [
        'python >= 3.8'
    ],
    'author': [
        'Lena Garber'
    ],
    'spec': my_module_spec
}
