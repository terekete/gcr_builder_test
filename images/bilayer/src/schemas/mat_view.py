{
    'kind': {
        'required': True,
        'type': 'string',
        'nullable': False,
        'regex': '^materialized_view$'
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
        'regex': 'bq_[a-z0-9_]+_view'
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
    'params': {
        'required': True,
        'type': 'dict',
        'schema': {
            'query': {
                'required': True,
                'type': 'string',
                'nullable': False
            },
            'refresh': {
                'required': True,
                'type': 'boolean',
                'nullable': False
            },
            'refresh_ms': {
                'required': True,
                'type': 'number',
                'nullable': False
            }
        }
    },
    'iam_binding': {
        'required': True,
        'type': 'dict',
        'schema': {
            'users': {
                'required': True,
                'type': 'dict',
                'schema': {
                    'subscribers': {
                        'required': True,
                        'type': 'list',
                        'nullable': True,
                        'schema': {
                            'type': 'dict',
                            'schema': {
                                'principal': {
                                    'type': 'string',
                                    'regex': '^(user:)([a-zA-Z0-9_.+-]+)@([a-zA-Z0-9-]+)\.([a-zA-Z0-9-.]+)$'
                                },
                                'expiry': {
                                    'type': 'string',
                                    'regex': 'datetime\(\d{4},([1-9]|1[0-2]),([1-9]|[12][0-9]|3[01])\)'
                                }
                            }
                        }
                    }
                }
            },
            'service_accounts': {
                'required': True,
                'type': 'dict',
                'schema': {
                    'subscribers': {
                        'required': True,
                        'type': 'list',
                        'nullable': True,
                        'schema': {
                            'type': 'dict',
                            'schema': {
                                'principal': {
                                    'type': 'string',
                                    'regex': '^(serviceAccount:)([a-zA-Z0-9_.+-]+)@([a-zA-Z0-9-]+)\.([a-zA-Z0-9-.]+)$'
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}
