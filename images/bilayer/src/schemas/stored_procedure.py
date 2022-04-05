{
    'kind': {
        'required': True,
        'type': 'string',
        'nullable': False,
        'regex': '^stored_procedure$'
    },
    'version': {
        'required': True,
        'type': 'string',
        'nullable': False,
        'regex': 'v(\d{1})',
    },
    'metadata': {
        'required': True,
        'type': 'dict',
        'schema': {
            'dep': {
                'required': True,
                'type': 'string',
                'nullable': False
            }
        }
    },
    'description': {
        'required': True,
        'type': 'string',
        'nullable': False
    },
    'resource_name': {
        'required': True,
        'type': 'string',
        'nullable': False,
        'regex': 'bq_[a-z0-9_]+'
    },
    'dataset_id': {
        'required': True,
        'type': 'string',
        'nullable': False
    },
    'expiration_datetime_staging': {
        'required': True,
        'type': 'string',
        'nullable': False,
        'regex': 'datetime\(\d{4},([1-9]|1[0-2]),([1-9]|[12][0-9]|3[01])\)'
    },
    'expiration_datetime_serving': {
        'required': True,
        'type': 'string',
        'nullable': True,
        'regex': 'datetime\(\d{4},([1-9]|1[0-2]),([1-9]|[12][0-9]|3[01])\)'
    },
    'stored_procedure_parameters': {
        'required': False,
        'type': 'list',
        'nullable': False,
        'excludes': 'query_schedule',
        'schema': {
            'type': 'dict',
            'schema': {
                'name': {
                    'type': 'string'
                },
                'data_type': {
                    'type': 'string'
                },
                'mode': {
                    'type': 'string',
                    'allowed': ['IN', 'OUT', 'INOUT']
                },
            }
        }
    },
    'definition_body': {
        'required': True,
        'type': 'string',
        'nullable': False
    },
    'query_schedule': {
        'required': False,
        'type': 'string',
        'nullable': True,
        'excludes': 'stored_procedure_parameters'
    },
}
