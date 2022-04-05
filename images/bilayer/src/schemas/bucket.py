{
    'kind': {
        'required': True,
        'type': 'string',
        'nullable': False,
        'regex': '^bucket$'
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
            },
        }
    },
    'resource_name': {
        'required': True,
        'type': 'string',
        'nullable': False,
        'regex': '([a-z])([a-z0-9_])+'
    },
    'storage_class': {
        'required': True,
        'type': 'string',
        'nullable': False,
        'allowed': ['STANDARD', 'ARCHIVE', 'NEARLINE']
    },
    # 'force_destroy': {
    # 'required': True,
    # 'type': 'boolean',
    # 'nullable': False,
    # },
    # 'uniform_bucket_level_access': {
    # 'required': True,
    # 'type': 'boolean',
    # 'nullable': False,
    # },
    # 'lifecycle_type': {
    # 'required': True,
    # 'type': 'string',
    # 'nullable': False,
    # },
    'lifecycle_age_days': {
        'required': True,
        'type': 'integer',
        'nullable': True
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
                                    'type': 'string', 'regex': '^(user:)([a-zA-Z0-9_.+-]+)@([a-zA-Z0-9-]+)\.([a-zA-Z0-9-.]+)$'
                                },
                                'expiry': {
                                    'type': 'string',
                                    'regex': 'datetime\(\d{4},([1-9]|1[0-2]),([1-9]|[12][0-9]|3[01])\)'
                                }
                            }
                        }
                    },
                    'publishers': {
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
                    },
                    'publishers': {
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
                    },
                }
            }
        }
    }
}
