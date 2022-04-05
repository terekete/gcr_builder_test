{
    'kind': {
        'required': True,
        'type': 'string',
        'nullable': False,
        'regex': '^ext_table$'
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
    'source_format': {
        'required': True,
        'type': 'string',
        'nullable': False,
        'allowed': ["CSV", "NEWLINE_DELIMITED_JSON", "AVRO", "PARQUET", "ORC"]
    },
    'autodetect': {
        'required': True,
        'type': 'boolean',
        'nullable': False,
    },
    'source_uris_staging': {
        'required': True,
        'type': 'list',
        'nullable': False,
    },
    'source_uris_serving': {
        'required': True,
        'type': 'list',
        'nullable': False,
    },
    'schema': {
        'required': True,
        'type': 'string',
        'nullable': True
    },
    'csv_options': {
        'required': True,
        'type': 'dict',
        'schema': {
            "quote": {'required': True, 'type': 'string', 'nullable': True},
            "allow_jagged_rows": {'required': True, 'type': 'boolean', 'nullable': True},
            "allow_quoted_newlines": {'required': True, 'type': 'boolean', 'nullable': True},
            "encoding": {'required': True, 'type': 'string', 'nullable': True},
            "field_delimiter": {'required': True, 'type': 'string', 'nullable': True},
            "skip_leading_rows": {'required': True, 'type': 'integer', 'nullable': True},
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
