import sys
import os
import yaml
import json
import pulumi
import pulumi_gcp as gcp
import base64

from datetime import datetime, timedelta
from pulumi_gcp import storage, bigquery, cloudscheduler
from pulumi import automation as auto
from croniter import croniter
from cerberus import Validator


# Function to validate the cron expression for jobs
def validate_cron(cron_str: str):
    base = datetime(2001, 1, 1, 0, 00)
    iter = croniter(cron_str, base)
    t1 = iter.get_next(datetime)
    t2 = iter.get_next(datetime)
    diff_min = int((t2 - t1) / timedelta(minutes=1))
    print(diff_min)
    if diff_min < 15:
        raise ValueError('Invalid cron, the job interval musb be > 15 minutes')


# Function to validate the schema of the resource yaml
def validate_manifest(manifest: str, schema_path: str):
    schema = eval(open(schema_path).read())
    validator = Validator(schema)
    if validator.validate(manifest):
        print('#### Schema Validation Successful for {kind} - {resource}'.format(
            kind=manifest['kind'], resource=manifest['resource_name'].lower()))
        return
    else:
        print('#### Schema Validation Failed for {kind} - {resource}'.format(
            kind=manifest['kind'], resource=manifest['resource_name'].lower()))
        print(json.dumps(validator.errors, indent=2))
        raise ValueError('Schema mismatch')


# Function to validate if the manifest is null
def validate_manifest_null(manifest: str, file: str):
    if manifest is None:
        raise ValueError(
            "YAML resource definition: {} is incomplete or does not exist".format(file))


# Function to get the list of yaml configuration files
def list_manifests(root: str):
    yml_list = []
    for path, subdirs, files in os.walk(root):
        for name in files:
            if name.endswith('.yaml') or name.endswith('.yml'):
                yml_list.append(path + '/' + name)
    return yml_list


# Function to get the py files in the job folder
def get_file(chemin: str):
    up_folder = os.path.dirname(os.path.abspath(chemin))
    print('root folder: {}'.format(up_folder))
    for path, subdirs, files in os.walk(up_folder):
        for name in files:
            if name.endswith('.py'):
                print(name)
                patho = os.path.dirname(path + '/' + name)
                print(patho)
                patho2 = os.path.basename(patho)
                out = str(patho2) + '/' + str(name)
                print('output: {}'.format(out))
                return out

# Function to get the py files in the vertex folder


def get_file_vertex(chemin: str):
    up_folder = os.path.dirname(os.path.abspath(chemin))
    print('root folder: {}'.format(up_folder))
    for path, subdirs, files in os.walk(up_folder):
        for name in files:
            if name.endswith('.py'):
                print(name)
                patho2 = up_folder.replace(
                    '/workspace/resources/vertex_pipelines/', '')
                out = str(patho2) + '/' + str(name)
                print('output: {}'.format(out))
                return out
    return out

# Function to get the py files in the spark folder


def get_file_spark(chemin: str):
    up_folder = os.path.dirname(os.path.abspath(chemin))
    print('root folder: {}'.format(up_folder))
    for path, subdirs, files in os.walk(up_folder):
        for name in files:
            if name.endswith('.py'):
                print(name)
                patho2 = up_folder.replace(
                    '/workspace/resources/spark_jobs/', '')
                out = str(patho2) + '/' + str(name)
                print('output: {}'.format(out))
                return out
    return out

# Function to get the expiration datetime (epoch) of the table obejects based on the project type.


def get_expiration(p_type, expiration_datetime_staging, expiration_datetime_serving):
    if p_type == 'bi-stg':
        return int(eval(expiration_datetime_staging).timestamp())*1000
    elif p_type == 'bi-srv':
        if expiration_datetime_serving:
            return int(eval(expiration_datetime_serving).timestamp())*1000
        else:
            return None
            # Return int((datetime.now()+timedelta(seconds=3)).timestamp())*1000
    else:
        raise ValueError('project type invalid')


# Function to return the expiration datetime depending the project type
def define_expiry(p_type, expiration_datetime_staging, expiration_datetime_serving):
    if p_type == 'bi-stg':
        return expiration_datetime_staging
    elif p_type == 'bi-srv':
        if expiration_datetime_serving:
            return expiration_datetime_serving
        else:
            return 'datetime(2050,1,1)'
    else:
        raise ValueError('project type invalid')


# Function to get the iam binding list based on the comparaison of the expiry to the build datetime
def get_binding_list(list_user, kind):
    iam_binding_list = []

    if kind == 'subscribers':
        if list_user['users']['subscribers'] is None and list_user['service_accounts']['subscribers'] is None:
            return []
        else:
            if list_user['users']['subscribers'] is not None:
                for d in list_user['users']['subscribers']:
                    if d['expiry'] is None:
                        iam_binding_list.append(d['principal'])
                    else:
                        if eval(d['expiry']) >= datetime.now():
                            iam_binding_list.append(d['principal'])
            if list_user['service_accounts']['subscribers'] is not None:
                for p in list_user['service_accounts']['subscribers']:
                    iam_binding_list.append(p['principal'])
    elif kind == 'publishers':
        if list_user['users']['publishers'] is None and list_user['service_accounts']['publishers'] is None:
            return []
        else:
            if list_user['users']['publishers'] is not None:
                for d in list_user['users']['publishers']:
                    if d['expiry'] is None:
                        iam_binding_list.append(d['principal'])
                    else:
                        if eval(d['expiry']) >= datetime.now():
                            iam_binding_list.append(d['principal'])
            if list_user['service_accounts']['publishers'] is not None:
                for p in list_user['service_accounts']['publishers']:
                    iam_binding_list.append(p['principal'])

    print(iam_binding_list)
    return iam_binding_list


def buckets(provider):
    ################## Buckets creation ##################

    # Read all buckets yaml
    list_buckets = list_manifests(root="/workspace/resources/buckets")
    # Create an empty dataset list to store the dataset resources names
    buckets = {}
    for i in range(len(list_buckets)):

        with open(str(list_buckets[i])) as a_yaml_file:
            parameter = yaml.load(a_yaml_file, Loader=yaml.FullLoader)

        validate_manifest_null(manifest=parameter, file=str(list_buckets[i]))
        validate_manifest(manifest=parameter,
                          schema_path='/src/schemas/bucket.py')

        if 'lifecycle_age_days' in parameter:
            lifecycle_age_days = parameter['lifecycle_age_days']
        else:
            lifecycle_age_days = 365

        buckets["bucket_{}".format(parameter['resource_name'])] = storage.Bucket(
            resource_name='bucket_' + parameter['resource_name'],
            name=str(project)+'_'+parameter['resource_name'],
            force_destroy=True,
            storage_class=parameter['storage_class'],
            location=location,
            uniform_bucket_level_access=True,
            lifecycle_rules=[gcp.storage.BucketLifecycleRuleArgs(
                action=gcp.storage.BucketLifecycleRuleActionArgs(
                    type="Delete"),
                condition=gcp.storage.BucketLifecycleRuleConditionArgs(
                    age=lifecycle_age_days)
            )],
            opts=pulumi.ResourceOptions(provider=provider)
        )

        # Apply iam binding
        storage.BucketIAMBinding(
            resource_name='dataset_read_iam_'+parameter['resource_name'],
            bucket=buckets['bucket_{}'.format(
                parameter['resource_name'])].name,
            role='roles/storage.objectViewer',
            members=get_binding_list(parameter['iam_binding'], 'subscribers'),
            opts=pulumi.ResourceOptions(
                provider=provider,
                parent=buckets['bucket_{}'.format(parameter['resource_name'])])
        )
        storage.BucketIAMBinding(
            resource_name='dataset_write_iam_'+parameter['resource_name'],
            bucket=buckets['bucket_{}'.format(
                parameter['resource_name'])].name,
            role='roles/storage.objectAdmin',
            members=get_binding_list(parameter['iam_binding'], 'publishers'),
            opts=pulumi.ResourceOptions(
                provider=provider,
                parent=buckets['bucket_{}'.format(parameter['resource_name'])]
            )
        )


# Main to run the pulumi script
def pulumi_program():

    pr = gcp.Provider(
        'bilayer-provider',
        impersonate_service_account=build_sa,
        region='northamerica-northeast1',
        project=project
    )

################## Vertex Pipelines creation ##################

    # Read all jobs yaml
    list_jobs = list_manifests(root="/workspace/resources/vertex_pipelines")
    # Create an empty dataset list to store the dataset resources names
    vertex_pipelines = {}
    vertex_pipelines_buckets = {}

    for i in range(len(list_jobs)):

        print(str(list_jobs[i]))
        with open(str(list_jobs[i])) as a_yaml_file:
            parameter = yaml.load(a_yaml_file, Loader=yaml.FullLoader)

        # Manifest validation
        validate_manifest_null(manifest=parameter, file=str(list_jobs[i]))
        # to add once schema ready
        validate_manifest(manifest=parameter,
                          schema_path='/schemas/vertex_pipeline.py')

        # Validate the cron
        validate_cron(str(parameter['schedule']))

        # Format the message to send to pubsub for the vertex pipeline
        dict_send = {}
        dict_mapping = {}
        dict_send['PROJECT_ID'] = project
        dict_send['BUCKET_NAME'] = "gs://{}_{}".format(
            project, parameter['resource_name'])
        # Get the py file location
        job_file = get_file_vertex(str(list_jobs[i]))
        print(job_file)
        dict_send['ref_file_path'] = job_file
        dict_mapping['PROJECT_ID'] = project
        dict_mapping['BUCKET_NAME'] = "gs://{}_{}".format(
            project, parameter['resource_name'])
        if project_type == 'bi-stg' and parameter['input_arg_staging'] is not None:
            dict_mapping.update(parameter['input_arg_staging'])
        elif project_type == 'bi-srv' and parameter['input_arg_serving'] is not None:
            dict_mapping.update(parameter['input_arg_serving'])
        dict_send['mapping'] = dict_mapping

        # message = str.encode(str(dict_send))
        message = str(dict_send)
        message_bytes = message.encode('ascii')
        base64_bytes = base64.b64encode(message_bytes)
        base64_message = base64_bytes.decode('ascii')

        # Build the resource if the not expired and deleted the resource if expired
        if eval(
            define_expiry(
                p_type=project_type,
                expiration_datetime_staging=parameter['expiration_datetime_staging'],
                expiration_datetime_serving=parameter['expiration_datetime_serving']
            )
        ) > datetime.now():
            vertex_pipelines["vertex_pipelines_{}".format(parameter['resource_name'])] = cloudscheduler.Job(
                resource_name='vertex_pipelines_' + parameter['resource_name'],
                name='vertex_job_' + parameter['resource_name'],
                description=parameter['description'],
                schedule=parameter['schedule'],
                project=project,
                region='northamerica-northeast1',
                pubsub_target=cloudscheduler.JobPubsubTargetArgs(
                    topic_name='projects/{}/topics/vertex-topic'.format(
                        project),
                    data=base64_message,
                ),
                opts=pulumi.ResourceOptions(provider=pr)
            )

        # Build the bucket related to the vertex pipeline
        vertex_pipelines_buckets["vertex_pipelines_bucket_{}".format(parameter['resource_name'])] = storage.Bucket(
            resource_name='vertex_pipelines_bucket_' +
            parameter['resource_name'],
            name=str(project) + '_' + parameter['resource_name'],
            force_destroy=True,
            storage_class='STANDARD',
            location=location,
            uniform_bucket_level_access=True,
            opts=pulumi.ResourceOptions(provider=pr)
        )

        storage.BucketIAMBinding(
            resource_name='dataset_read_iam_'+parameter['resource_name'],
            bucket=vertex_pipelines_buckets['vertex_pipelines_bucket_{}'.format(
                parameter['resource_name'])].name,
            role='roles/storage.objectViewer',
            members=get_binding_list(parameter['iam_binding'], 'subscribers'),
            opts=pulumi.ResourceOptions(
                provider=pr,
                parent=vertex_pipelines_buckets['vertex_pipelines_bucket_{}'.format(
                    parameter['resource_name'])]
            )
        )


################## Severless Spark Jobs creation ##################

    # Read all jobs yaml
    list_jobs = list_manifests(root="/workspace/resources/spark_jobs")
    # Create an empty dataset list to store the dataset resources names
    jobs = {}
    jobs_buckets = {}

    for i in range(len(list_jobs)):

        print(str(list_jobs[i]))
        with open(str(list_jobs[i])) as a_yaml_file:
            parameter = yaml.load(a_yaml_file, Loader=yaml.FullLoader)

        # Manifest validation
        validate_manifest_null(manifest=parameter, file=str(list_jobs[i]))
        validate_manifest(manifest=parameter,
                          schema_path='/schemas/spark_job.py')

        # Validate the cron
        validate_cron(str(parameter['schedule']))

        # Format the message to send to pubsub for the spark job
        dict_send = {}
        dict_send['project'] = project
        # Get the py file location
        job_file = get_file_spark(str(list_jobs[i]))
        print(job_file)
        dict_send['job_file'] = job_file
        dict_send['bucket'] = str(
            str(project) + '_' + parameter['resource_name'])

        # get custom image path if exists
        if 'custom_image_path' in parameter:
            dict_send['custom_image_path'] = parameter['custom_image_path']
        else:
            dict_send['custom_image_path'] = 'default'

        # message = str.encode(str(dict_send))
        message = str(dict_send)
        message_bytes = message.encode('ascii')
        base64_bytes = base64.b64encode(message_bytes)
        base64_message = base64_bytes.decode('ascii')

        # Build the resource if the not expired and deleted the resource if expired
        if eval(
            define_expiry(
                p_type=project_type,
                expiration_datetime_staging=parameter['expiration_datetime_staging'],
                expiration_datetime_serving=parameter['expiration_datetime_serving']
            )
        ) > datetime.now():
            jobs["spark_job_{}".format(parameter['resource_name'])] = cloudscheduler.Job(
                resource_name='spark_job_' + parameter['resource_name'],
                name='spark_job_' + parameter['resource_name'],
                description=parameter['description'],
                schedule=parameter['schedule'],
                project=project,
                region='northamerica-northeast1',
                pubsub_target=cloudscheduler.JobPubsubTargetArgs(
                    topic_name='projects/{}/topics/spark-topic'.format(
                        project),
                    data=base64_message,
                ),
                opts=pulumi.ResourceOptions(provider=pr)
            )

        # Build the bucket related to the spark job
        jobs_buckets["jobs_bucket_{}".format(parameter['resource_name'])] = storage.Bucket(
            resource_name='jobs_bucket_' + parameter['resource_name'],
            name=str(project) + '_' + parameter['resource_name'],
            force_destroy=True,
            storage_class='STANDARD',
            location=location,
            uniform_bucket_level_access=True,
            opts=pulumi.ResourceOptions(provider=pr)
        )

        storage.BucketIAMBinding(
            resource_name='dataset_read_iam_'+parameter['resource_name'],
            bucket=jobs_buckets['jobs_bucket_{}'.format(
                parameter['resource_name'])].name,
            role='roles/storage.objectViewer',
            members=get_binding_list(parameter['iam_binding'], 'subscribers'),
            opts=pulumi.ResourceOptions(
                provider=pr,
                parent=jobs_buckets['jobs_bucket_{}'.format(
                    parameter['resource_name'])]
            )
        )

    buckets(provider=pr)
# ################## Buckets creation ##################

#     # Read all buckets yaml
#     list_buckets = list_manifests(root="/workspace/resources/buckets")
#     # Create an empty dataset list to store the dataset resources names
#     buckets = {}
#     for i in range(len(list_buckets)):

#         with open(str(list_buckets[i])) as a_yaml_file:
#             parameter = yaml.load(a_yaml_file, Loader=yaml.FullLoader)

#         validate_manifest_null(manifest=parameter, file=str(list_buckets[i]))
#         validate_manifest(manifest=parameter, schema_path='/schemas/bucket.py')

#         if 'lifecycle_age_days' in parameter:
#             lifecycle_age_days = parameter['lifecycle_age_days']
#         else:
#             lifecycle_age_days = 365

#         buckets["bucket_{}".format(parameter['resource_name'])] = storage.Bucket(
#             resource_name='bucket_' + parameter['resource_name'],
#             name=str(project)+'_'+parameter['resource_name'],
#             force_destroy=True,
#             storage_class=parameter['storage_class'],
#             location=location,
#             uniform_bucket_level_access=True,
#             lifecycle_rules=[gcp.storage.BucketLifecycleRuleArgs(
#                 action=gcp.storage.BucketLifecycleRuleActionArgs(
#                     type="Delete"),
#                 condition=gcp.storage.BucketLifecycleRuleConditionArgs(
#                     age=lifecycle_age_days)
#             )],
#             opts=pulumi.ResourceOptions(provider=pr)
#         )

#         # Apply iam binding
#         storage.BucketIAMBinding(
#             resource_name='dataset_read_iam_'+parameter['resource_name'],
#             bucket=buckets['bucket_{}'.format(
#                 parameter['resource_name'])].name,
#             role='roles/storage.objectViewer',
#             members=get_binding_list(parameter['iam_binding'], 'subscribers'),
#             opts=pulumi.ResourceOptions(
#                 provider=pr,
#                 parent=buckets['bucket_{}'.format(parameter['resource_name'])])
#         )
#         storage.BucketIAMBinding(
#             resource_name='dataset_write_iam_'+parameter['resource_name'],
#             bucket=buckets['bucket_{}'.format(
#                 parameter['resource_name'])].name,
#             role='roles/storage.objectAdmin',
#             members=get_binding_list(parameter['iam_binding'], 'publishers'),
#             opts=pulumi.ResourceOptions(
#                 provider=pr,
#                 parent=buckets['bucket_{}'.format(parameter['resource_name'])]
#             )
#         )

################## Datasets creation ##################

    # Read all datatset yaml
    list_datasets = list_manifests(root="/workspace/resources/datasets")
    # Create an empty dataset list to store the dataset resources names
    datasets = {}

    for i in range(len(list_datasets)):

        with open(str(list_datasets[i])) as a_yaml_file:
            parameter = yaml.load(a_yaml_file, Loader=yaml.FullLoader)

        validate_manifest_null(manifest=parameter, file=str(list_datasets[i]))
        validate_manifest(manifest=parameter,
                          schema_path='/schemas/dataset.py')

        datasets["dataset_{}".format(parameter['resource_name'])] = bigquery.Dataset(
            resource_name='dataset_' + parameter['resource_name'],
            dataset_id=parameter['resource_name'],
            description=parameter['description'],
            delete_contents_on_destroy=False,
            location=location,
            default_partition_expiration_ms=parameter['partition_expiration_ms'],
            default_table_expiration_ms=parameter['table_expiration_ms'],
            opts=pulumi.ResourceOptions(provider=pr)
        )

        # Apply iam binding
        bigquery.DatasetIamBinding(
            resource_name='dataset_read_iam_'+parameter['resource_name'],
            project=project,
            dataset_id=datasets['dataset_{}'.format(
                parameter['resource_name'])].dataset_id,
            role='roles/bigquery.dataViewer',
            members=get_binding_list(parameter['iam_binding'], 'subscribers'),
            opts=pulumi.ResourceOptions(
                provider=pr,
                parent=datasets['dataset_{}'.format(
                    parameter['resource_name'])]
            )
        )

################## Tables creation ##################

    list_tables = list_manifests(root="/workspace/resources/tables")
    tables = {}

    for i in range(len(list_tables)):

        with open(str(list_tables[i])) as a_yaml_file:
            parameter = yaml.load(a_yaml_file, Loader=yaml.FullLoader)

        validate_manifest_null(manifest=parameter, file=str(list_tables[i]))
        validate_manifest(manifest=parameter, schema_path='/schemas/table.py')

        if 'clusterings' in parameter:
            cluster = parameter['clusterings']
        else:
            cluster = None

        if eval(
            define_expiry(
                p_type=project_type,
                expiration_datetime_staging=parameter['expiration_datetime_staging'],
                expiration_datetime_serving=parameter['expiration_datetime_serving']
            )
        ) > datetime.now():
            if 'time_partitioning' not in parameter:
                tables["table_{}".format(parameter['resource_name'])] = bigquery.Table(
                    resource_name='table_' + parameter['resource_name'],
                    table_id=parameter['resource_name'],
                    dataset_id=datasets['dataset_{}'.format(
                        parameter['dataset_id'])].dataset_id,
                    deletion_protection=False,
                    description=parameter['description'],
                    expiration_time=get_expiration(p_type=project_type, expiration_datetime_staging=parameter[
                                                   'expiration_datetime_staging'], expiration_datetime_serving=parameter['expiration_datetime_serving']),
                    schema=parameter['schema'],
                    clusterings=cluster,
                    opts=pulumi.ResourceOptions(
                        provider=pr,
                        parent=datasets['dataset_{}'.format(
                            parameter['dataset_id'])]
                    )
                )
            else:
                tables["table_{}".format(parameter['resource_name'])] = bigquery.Table(
                    resource_name='table_' + parameter['resource_name'],
                    table_id=parameter['resource_name'],
                    dataset_id=datasets['dataset_{}'.format(
                        parameter['dataset_id'])].dataset_id,
                    deletion_protection=False,
                    description=parameter['description'],
                    expiration_time=get_expiration(
                        p_type=project_type,
                        expiration_datetime_staging=parameter['expiration_datetime_staging'],
                        expiration_datetime_serving=parameter['expiration_datetime_serving']
                    ),
                    schema=parameter['schema'],
                    clusterings=cluster,
                    time_partitioning=bigquery.TableTimePartitioningArgs(
                        type=parameter['time_partitioning']['type'],
                        expiration_ms=parameter['time_partitioning']['expiration_ms'],
                        field=parameter['time_partitioning']['field'],
                        require_partition_filter=parameter['time_partitioning']['require_partition_filter'],
                    ),
                    opts=pulumi.ResourceOptions(
                        provider=pr,
                        parent=datasets['dataset_{}'.format(
                            parameter['dataset_id'])]
                    )
                )

            # Apply iam binding
            bigquery.IamBinding(
                resource_name='table_read_iam_'+parameter['resource_name'],
                project=project,
                dataset_id=datasets['dataset_{}'.format(
                    parameter['dataset_id'])].dataset_id,
                table_id=tables['table_{}'.format(
                    parameter['resource_name'])].table_id,
                role='roles/bigquery.dataViewer',
                members=get_binding_list(
                    parameter['iam_binding'], 'subscribers'),
                opts=pulumi.ResourceOptions(
                    provider=pr,
                    parent=tables['table_{}'.format(
                        parameter['resource_name'])]
                )
            )
            bigquery.IamBinding(
                resource_name='table_write_iam_'+parameter['resource_name'],
                project=project,
                dataset_id=datasets['dataset_{}'.format(
                    parameter['dataset_id'])].dataset_id,
                table_id=tables['table_{}'.format(
                    parameter['resource_name'])].table_id,
                role='roles/bigquery.dataOwner',
                members=get_binding_list(
                    parameter['iam_binding'], 'publishers'),
                opts=pulumi.ResourceOptions(
                    provider=pr,
                    parent=tables['table_{}'.format(
                        parameter['resource_name'])]
                )
            )
################## External table creation ##################

    list_ext_tables = list_manifests(
        root="/workspace/resources/external_tables")
    ext_tables = {}
    for i in range(len(list_ext_tables)):

        with open(str(list_ext_tables[i])) as a_yaml_file:
            parameter = yaml.load(a_yaml_file, Loader=yaml.FullLoader)

        validate_manifest_null(
            manifest=parameter, file=str(list_ext_tables[i]))
        validate_manifest(manifest=parameter,
                          schema_path='/schemas/ext_table.py')

        source = parameter['source_format']

        if project_type == 'bi-stg':
            source_uris = parameter['source_uris_staging']
        elif project_type == 'bi-srv':
            source_uris = parameter['source_uris_serving']

        # Define the ext table data configuration

        if source == "CSV":
            options = bigquery.TableExternalDataConfigurationCsvOptionsArgs(
                # The value that is used to quote data sections in a CSV file.
                # If your data does not contain quoted sections, set the property value to an empty string. If your data contains quoted newline characters, you must also set the allow_quoted_newlines property to true. The API-side default is ", specified in the provider escaped as \". Due to limitations with default values, this value is required to be explicitly set.
                quote=parameter['csv_options']['quote'],
                # Indicates if BigQuery should accept rows that are missing trailing optional columns.
                allow_jagged_rows=parameter['csv_options']['allow_jagged_rows'],
                # Indicates if BigQuery should allow quoted data sections that contain newline characters in a CSV file. The default value is false.
                allow_quoted_newlines=parameter['csv_options']['allow_quoted_newlines'],
                # The character encoding of the data. The supported values are UTF-8 or ISO-8859-1.
                encoding=parameter['csv_options']['encoding'],
                # The separator for fields in a CSV file.
                field_delimiter=parameter['csv_options']['field_delimiter'],
                # The number of rows at the top of the sheet that BigQuery will skip when reading the data. At least one of range or skip_leading_rows must be set.
                skip_leading_rows=parameter['csv_options']['skip_leading_rows'],
            )
        # elif source == "GOOGLE_SHEETS":
            # options = bigquery.TableExternalDataConfigurationGoogleSheetsOptionsArgs(
            # # Information required to partition based on ranges. Structure is documented below.
            # range="",
            # # The number of rows at the top of the sheet that BigQuery will skip when reading the data. At least one of range or skip_leading_rows must be set.
            # skip_leading_rows = 1,
            # )
        # elif source in ["NEWLINE_DELIMITED_JSON", "AVRO", "PARQUET"]:
            # options=bigquery.TableExternalDataConfigurationHivePartitioningOptionsArgs(
            # # When set, what mode of hive partitioning to use when reading data. The following modes are supported.
            # # AUTO: automatically infer partition key name(s) and type(s).
            # # STRINGS: automatically infer partition key name(s). All types are Not all storage formats support hive partitioning. Requesting hive partitioning on an unsupported format will lead to an error. Currently supported formats are: JSON, CSV, ORC, Avro and Parquet.
            # # CUSTOM: when set to CUSTOM, you must encode the partition key schema within the source_uri_prefix by setting source_uri_prefix to gs://bucket/path_to_table/{key1:TYPE1}/{key2:TYPE2}/{key3:TYPE3}.
            # mode="AUTO",
            # # If set to true, queries over this table require a partition filter that can be used for partition elimination to be specified.
            # require_partition_filter=False,
            # # When hive partition detection is requested, a common for all source uris must be required. The prefix must end immediately before the partition key encoding begins. For example, consider files following this data layout. gs://bucket/path_to_table/dt=2019-06-01/country=USA/id=7/file.avro gs://bucket/path_to_table/dt=2019-05-31/country=CA/id=3/file.avro When hive partitioning is requested with either AUTO or STRINGS detection, the common prefix can be either of gs://bucket/path_to_table or gs://bucket/path_to_table/. Note that when mode is set to CUSTOM, you must encode the partition key schema within the source_uri_prefix by setting source_uri_prefix to gs://bucket/path_to_table/{key1:TYPE1}/{key2:TYPE2}/{key3:TYPE3}.
            # source_uri_prefix="gs://dse-cicd-test-lab-4c0841-jobs-scripts/userdata1.avro",
            # )

        if eval(
            define_expiry(
                p_type=project_type,
                expiration_datetime_staging=parameter['expiration_datetime_staging'],
                expiration_datetime_serving=parameter['expiration_datetime_serving']
            )
        ) > datetime.now():
            if source == "CSV":
                ext_tables["ext_table_{}".format(parameter['resource_name'])] = bigquery.Table(
                    resource_name='ext_table_' + parameter['resource_name'],
                    table_id=parameter['resource_name'],
                    dataset_id=datasets['dataset_{}'.format(
                        parameter['dataset_id'])].dataset_id,
                    deletion_protection=False,
                    description=parameter['description'],
                    expiration_time=get_expiration(
                        p_type=project_type,
                        expiration_datetime_staging=parameter['expiration_datetime_staging'],
                        expiration_datetime_serving=parameter['expiration_datetime_serving']
                    ),
                    external_data_configuration=gcp.bigquery.TableExternalDataConfigurationArgs(
                        autodetect=parameter['autodetect'],
                        source_format=source,
                        csv_options=options,
                        source_uris=source_uris,
                        schema=parameter['schema'],
                    ),
                    opts=pulumi.ResourceOptions(
                        provider=pr, parent=datasets['dataset_{}'.format(parameter['dataset_id'])])
                )
            # elif source == "GOOGLE_SHEETS":
                # ext_tables["ext_table_{}".format(parameter['resource_name'])] = bigquery.Table(
                # resource_name='ext_table_' + parameter['resource_name'],
                # table_id=parameter['resource_name'],
                # dataset_id=datasets['dataset_{}'.format(
                # parameter['dataset_id'])].dataset_id,
                # deletion_protection=False,
                # description=parameter['description'],
                # expiration_time=get_expiration(
                # p_type=project_type,
                # expiration_datetime_staging=parameter['expiration_datetime_staging'],
                # expiration_datetime_serving=parameter['expiration_datetime_serving']
                # ),
                # external_data_configuration=gcp.bigquery.TableExternalDataConfigurationArgs(
                # autodetect=True,
                # source_format="GOOGLE_SHEETS",
                # google_sheets_options=options,
                # source_uris=source_uris,
                # schema=""
                # ),
                # opts=pulumi.ResourceOptions(provider=pr,parent=datasets['dataset_{}'.format(parameter['dataset_id'])])
                # )
            elif source in ["NEWLINE_DELIMITED_JSON", "AVRO", "PARQUET", "ORC"]:
                ext_tables["ext_table_{}".format(parameter['resource_name'])] = bigquery.Table(
                    resource_name='ext_table_' + parameter['resource_name'],
                    table_id=parameter['resource_name'],
                    dataset_id=datasets['dataset_{}'.format(
                        parameter['dataset_id'])].dataset_id,
                    deletion_protection=False,
                    description=parameter['description'],
                    expiration_time=get_expiration(
                        p_type=project_type,
                        expiration_datetime_staging=parameter['expiration_datetime_staging'],
                        expiration_datetime_serving=parameter['expiration_datetime_serving']
                    ),
                    external_data_configuration=gcp.bigquery.TableExternalDataConfigurationArgs(
                        autodetect=parameter['autodetect'],
                        source_format=source,
                        source_uris=source_uris,
                        schema=parameter['schema'],
                    ),
                    opts=pulumi.ResourceOptions(
                        provider=pr, parent=datasets['dataset_{}'.format(parameter['dataset_id'])])
                )
            # apply iam binding
            bigquery.IamBinding(
                resource_name='ext_table_read_iam_'+parameter['resource_name'],
                project=project,
                dataset_id=datasets['dataset_{}'.format(
                    parameter['dataset_id'])].dataset_id,
                table_id=ext_tables['ext_table_{}'.format(
                    parameter['resource_name'])].table_id,
                role='roles/bigquery.dataViewer',
                members=get_binding_list(
                    parameter['iam_binding'], 'subscribers'),
                opts=pulumi.ResourceOptions(
                    provider=pr,
                    parent=ext_tables['ext_table_{}'.format(
                        parameter['resource_name'])]
                )
            )

################## Views creation ##################

    list_views = list_manifests(root="/workspace/resources/views")
    views = {}
    for i in range(len(list_views)):

        with open(str(list_views[i])) as a_yaml_file:
            parameter = yaml.load(a_yaml_file, Loader=yaml.FullLoader)

        validate_manifest_null(manifest=parameter, file=str(list_views[i]))
        validate_manifest(manifest=parameter, schema_path='/schemas/view.py')

        if eval(
            define_expiry(
                p_type=project_type,
                expiration_datetime_staging=parameter['expiration_datetime_staging'],
                expiration_datetime_serving=parameter['expiration_datetime_serving']
            )
        ) > datetime.now():
            views["view_{}".format(parameter['resource_name'])] = bigquery.Table(
                resource_name='view_' + parameter['resource_name'],
                table_id=parameter['resource_name'],
                dataset_id=datasets['dataset_{}'.format(
                    parameter['dataset_id'])].dataset_id,
                deletion_protection=False,
                description=parameter['description'],
                expiration_time=get_expiration(
                    p_type=project_type,
                    expiration_datetime_staging=parameter['expiration_datetime_staging'],
                    expiration_datetime_serving=parameter['expiration_datetime_serving']
                ),
                # expiration_time=None,
                view=bigquery.TableViewArgs(
                    query=parameter['query'],
                    use_legacy_sql=False
                ),
                opts=pulumi.ResourceOptions(
                    provider=pr,
                    parent=datasets['dataset_{}'.format(
                        parameter['dataset_id'])]
                )
            )

            # apply iam binding
            bigquery.IamBinding(
                resource_name='view_read_iam_'+parameter['resource_name'],
                project=project,
                dataset_id=datasets['dataset_{}'.format(
                    parameter['dataset_id'])].dataset_id,
                table_id=views['view_{}'.format(
                    parameter['resource_name'])].table_id,
                role='roles/bigquery.dataViewer',
                members=get_binding_list(
                    parameter['iam_binding'], 'subscribers'),
                opts=pulumi.ResourceOptions(
                    provider=pr,
                    parent=views['view_{}'.format(parameter['resource_name'])]
                )
            )

################## Stored Procedures creation ##################

    list_stored_procedures = list_manifests(
        root="/workspace/resources/stored_procedures")
    stored_procedures = {}
    for i in range(len(list_stored_procedures)):

        with open(str(list_stored_procedures[i])) as a_yaml_file:
            parameter = yaml.load(a_yaml_file, Loader=yaml.FullLoader)

        validate_manifest_null(
            manifest=parameter, file=str(list_stored_procedures[i]))
        validate_manifest(manifest=parameter,
                          schema_path='/schemas/stored_procedure.py')

        # Create the stored_procedure

        if eval(
            define_expiry(
                p_type=project_type,
                expiration_datetime_staging=parameter['expiration_datetime_staging'],
                expiration_datetime_serving=parameter['expiration_datetime_serving']
            )
        ) > datetime.now():

            if 'stored_procedure_parameters' in parameter:

                arg_list = []
                for iter in range(len(parameter['stored_procedure_parameters'])):
                    element = bigquery.RoutineArgumentArgs(argument_kind="FIXED_TYPE",
                                                           name=parameter['stored_procedure_parameters'][iter]['name'],
                                                           data_type="{\"typeKind\" :  \"datatype\"}".replace(
                                                               'datatype', parameter['stored_procedure_parameters'][iter]['data_type']),
                                                           mode=parameter['stored_procedure_parameters'][iter]['mode']
                                                           )
                    print(element)
                    arg_list.append(element)

                stored_procedures["stored_procedure_{}".format(parameter['resource_name'])] = bigquery.Routine(
                    resource_name=parameter['resource_name'] +
                    '_' + str(parameter['dataset_id']),
                    routine_id=parameter['resource_name'] +
                    '_' + str(parameter['dataset_id']),
                    dataset_id=datasets['dataset_{}'.format(
                        parameter['dataset_id'])].dataset_id,
                    routine_type="PROCEDURE",
                    language="SQL",
                    definition_body=parameter['definition_body'],
                    description=parameter['description'],
                    arguments=arg_list,
                    opts=pulumi.ResourceOptions(
                        provider=pr,
                        parent=datasets['dataset_{}'.format(
                            parameter['dataset_id'])]
                    )
                )
            else:
                stored_procedures["stored_procedure_{}".format(parameter['resource_name'])] = bigquery.Routine(
                    resource_name=parameter['resource_name'] +
                    '_' + str(parameter['dataset_id']),
                    routine_id=parameter['resource_name'] +
                    '_' + str(parameter['dataset_id']),
                    dataset_id=datasets['dataset_{}'.format(
                        parameter['dataset_id'])].dataset_id,
                    routine_type="PROCEDURE",
                    language="SQL",
                    definition_body=parameter['definition_body'],
                    description=parameter['description'],
                    opts=pulumi.ResourceOptions(
                        provider=pr,
                        parent=datasets['dataset_{}'.format(
                            parameter['dataset_id'])]
                    )
                )

            # Create the scheduling
            if 'query_schedule' in parameter:
                if parameter['query_schedule'] is not None:
                    bigquery.DataTransferConfig(
                        resource_name="sp_sched_" +
                        parameter['resource_name'] + '_' +
                        str(parameter['dataset_id']),
                        # display_name="sp_"+parameter['resource_name'] + '_' + str(parameter['dataset_id']),
                        display_name=parameter['resource_name'],
                        location=location,
                        data_source_id="scheduled_query",
                        schedule=parameter["query_schedule"],
                        params={
                            "query": "call {dataset}.{routine_id}()".format(dataset=parameter['dataset_id'], routine_id=parameter['resource_name'] + '_' + str(parameter['dataset_id'])),
                        },
                        opts=pulumi.ResourceOptions(
                            provider=pr,
                            parent=stored_procedures['stored_procedure_{}'.format(
                                parameter['resource_name'])]
                        )
                    )
################## Scalar Functions creation ##################

    list_scalar_functions = list_manifests(
        root="/workspace/resources/scalar_functions")
    scalar_functions = {}
    for i in range(len(list_scalar_functions)):

        with open(str(list_scalar_functions[i])) as a_yaml_file:
            parameter = yaml.load(a_yaml_file, Loader=yaml.FullLoader)

        validate_manifest_null(
            manifest=parameter, file=str(list_scalar_functions[i]))
        validate_manifest(manifest=parameter,
                          schema_path='/schemas/scalar_function.py')

        # Create the scalar_function

        arg_list = []
        for iter in range(len(parameter['input_parameters'])):
            element = bigquery.RoutineArgumentArgs(argument_kind="FIXED_TYPE",
                                                   name=parameter['input_parameters'][iter]['name'],
                                                   data_type="{\"typeKind\" :  \"datatype\"}".replace(
                                                       'datatype', parameter['input_parameters'][iter]['data_type']),
                                                   )
            print(element)
            arg_list.append(element)

        scalar_functions["scalar_function_{}".format(parameter['resource_name'])] = bigquery.Routine(
            resource_name=parameter['resource_name'] +
            '_' + str(parameter['dataset_id']),
            routine_id=parameter['resource_name'],
            dataset_id=datasets['dataset_{}'.format(
                parameter['dataset_id'])].dataset_id,
            routine_type="SCALAR_FUNCTION",
            language=parameter['language'],
            return_type="{\"typeKind\" :  \"datatype\"}".replace(
                'datatype', parameter['return_type']),
            definition_body=parameter['definition_body'],
            description=parameter['description'],
            arguments=arg_list,
            opts=pulumi.ResourceOptions(
                provider=pr,
                parent=datasets['dataset_{}'.format(
                    parameter['dataset_id'])]
            )
        )

################## Materialized Views creation ##################

    list_mat_views = list_manifests(
        root="/workspace/resources/materialized_views")
    mat_views = {}

    for i in range(len(list_mat_views)):

        with open(str(list_mat_views[i])) as a_yaml_file:
            parameter = yaml.load(a_yaml_file, Loader=yaml.FullLoader)

        validate_manifest_null(manifest=parameter, file=str(list_mat_views[i]))
        validate_manifest(manifest=parameter,
                          schema_path='/schemas/mat_view.py')
        if eval(
            define_expiry(
                p_type=project_type,
                expiration_datetime_staging=parameter['expiration_datetime_staging'],
                expiration_datetime_serving=parameter['expiration_datetime_serving']
            )
        ) > datetime.now():
            mat_views["mat_view_{}".format(parameter['resource_name'])] = bigquery.Table(
                resource_name='mat_view_' + parameter['resource_name'],
                table_id=parameter['resource_name'],
                description=parameter['description'],
                dataset_id=datasets['dataset_{}'.format(
                    parameter['dataset_id'])].dataset_id,
                deletion_protection=False,
                expiration_time=get_expiration(
                    p_type=project_type,
                    expiration_datetime_staging=parameter['expiration_datetime_staging'],
                    expiration_datetime_serving=parameter['expiration_datetime_serving']
                ),
                materialized_view=bigquery.TableMaterializedViewArgs(
                    query=parameter['params']['query'],
                    enable_refresh=parameter['params']['refresh'],
                    refresh_interval_ms=parameter['params']['refresh_ms']
                ),
                opts=pulumi.ResourceOptions(
                    provider=pr,
                    parent=datasets['dataset_{}'.format(
                        parameter['dataset_id'])]
                )
            )

            # Apply iam binding
            bigquery.IamBinding(
                resource_name='mat_view_read_iam_'+parameter['resource_name'],
                project=project,
                dataset_id=datasets['dataset_{}'.format(
                    parameter['dataset_id'])].dataset_id,
                table_id=mat_views['mat_view_{}'.format(
                    parameter['resource_name'])].table_id,
                role='roles/bigquery.dataViewer',
                members=get_binding_list(
                    parameter['iam_binding'], 'subscribers'),
                opts=pulumi.ResourceOptions(
                    provider=pr,
                    parent=mat_views['mat_view_{}'.format(
                        parameter['resource_name'])]
                )
            )

################## Scheduled Queries creation ##################

    list_scheduled_queries = list_manifests(
        root="/workspace/resources/scheduled_queries")
    # Create an empty dataset list to store the dataset resources names
    scheduled_queries = {}
    query_configs = {}
    for i in range(len(list_scheduled_queries)):

        with open(str(list_scheduled_queries[i])) as a_yaml_file:
            parameter = yaml.load(a_yaml_file, Loader=yaml.FullLoader)

        validate_manifest_null(
            manifest=parameter,
            file=str(list_scheduled_queries[i])
        )
        validate_manifest(manifest=parameter,
                          schema_path='/schemas/scheduled_query.py')

        if eval(
            define_expiry(
                p_type=project_type,
                expiration_datetime_staging=parameter['expiration_datetime_staging'],
                expiration_datetime_serving=parameter['expiration_datetime_serving']
            )
        ) > datetime.now():
            # Create the table to be used for the scheduled query
            if 'time_partitioning' not in parameter:
                scheduled_queries["scheduled_query_{}".format(parameter['resource_name'])] = bigquery.Table(
                    resource_name='scheduled_query_' +
                    parameter['resource_name'],
                    table_id=parameter['resource_name'],
                    description=parameter['description'],
                    dataset_id=datasets['dataset_{}'.format(
                        parameter['dataset_id'])].dataset_id,
                    deletion_protection=False,
                    expiration_time=get_expiration(
                        p_type=project_type,
                        expiration_datetime_staging=parameter['expiration_datetime_staging'],
                        expiration_datetime_serving=parameter['expiration_datetime_serving']
                    ),
                    schema=parameter['schema'],
                    opts=pulumi.ResourceOptions(
                        provider=pr,
                        parent=datasets['dataset_{}'.format(
                            parameter['dataset_id'])]
                    )
                )
            else:
                scheduled_queries["scheduled_query_{}".format(parameter['resource_name'])] = bigquery.Table(
                    resource_name='scheduled_query_' +
                    parameter['resource_name'],
                    table_id=parameter['resource_name'],
                    description=parameter['description'],
                    dataset_id=datasets['dataset_{}'.format(
                        parameter['dataset_id'])].dataset_id,
                    deletion_protection=False,
                    expiration_time=get_expiration(
                        p_type=project_type,
                        expiration_datetime_staging=parameter['expiration_datetime_staging'],
                        expiration_datetime_serving=parameter['expiration_datetime_serving']
                    ),
                    schema=parameter['schema'],
                    time_partitioning=bigquery.TableTimePartitioningArgs(
                        type=parameter['time_partitioning']['type'],
                        expiration_ms=parameter['time_partitioning']['expiration_ms'],
                        field=parameter['time_partitioning']['field'],
                        require_partition_filter=parameter['time_partitioning']['require_partition_filter'],
                    ),
                    opts=pulumi.ResourceOptions(
                        provider=pr,
                        parent=datasets['dataset_{}'.format(
                            parameter['dataset_id'])]
                    )
                )

            # Apply iam binding
            bigquery.IamBinding(
                resource_name='scheduled_query_read_iam_' +
                parameter['resource_name'],
                project=project,
                dataset_id=datasets['dataset_{}'.format(
                    parameter['dataset_id'])].dataset_id,
                table_id=scheduled_queries['scheduled_query_{}'.format(
                    parameter['resource_name'])].table_id,
                role='roles/bigquery.dataViewer',
                members=get_binding_list(
                    parameter['iam_binding'], 'subscribers'),
                opts=pulumi.ResourceOptions(
                    provider=pr,
                    parent=scheduled_queries['scheduled_query_{}'.format(
                        parameter['resource_name'])]
                )
            )
            bigquery.IamBinding(
                resource_name='scheduled_query_write_iam_' +
                parameter['resource_name'],
                project=project,
                dataset_id=datasets['dataset_{}'.format(
                    parameter['dataset_id'])].dataset_id,
                table_id=scheduled_queries['scheduled_query_{}'.format(
                    parameter['resource_name'])].table_id,
                role='roles/bigquery.dataOwner',
                members=get_binding_list(
                    parameter['iam_binding'], 'publishers'),
                opts=pulumi.ResourceOptions(
                    provider=pr,
                    parent=scheduled_queries['scheduled_query_{}'.format(
                        parameter['resource_name'])]
                )
            )

            bigquery.DataTransferConfig(
                resource_name="queryConfig_" +
                parameter['resource_name'] + '_' + parameter['dataset_id'],
                display_name="bq_data_transfer_"+parameter['resource_name'],
                location=location,
                data_source_id="scheduled_query",
                schedule=parameter["query_schedule"],
                destination_dataset_id=datasets['dataset_{}'.format(
                    parameter['dataset_id'])].dataset_id,
                params={
                    "destination_table_name_template": scheduled_queries['scheduled_query_{}'.format(parameter['resource_name'])].table_id,
                    "write_disposition": parameter['write_disposition'],
                    "query": parameter['query'],
                },
                opts=pulumi.ResourceOptions(
                    provider=pr,
                    parent=scheduled_queries['scheduled_query_{}'.format(
                        parameter['resource_name'])]
                )
            )


if __name__ == "__main__":
    team = sys.argv[1]
    project = sys.argv[2]
    project_type = sys.argv[3]
    build_sa = sys.argv[4]

    location = 'northamerica-northeast1'
    stack = auto.create_or_select_stack(
        stack_name=team + '_sa',
        project_name=project,
        program=pulumi_program,
        work_dir='/workspace')

    print('display stack content')
    print(stack)

    stack.set_config("gpc:region", auto.ConfigValue("northamerica-northeast1"))
    stack.set_config("gcp:project", auto.ConfigValue(project))

    print("refreshing stack...")
    stack.refresh(on_output=print)
    print("refresh complete")

    preview = stack.preview()
    up = stack.up(on_output=print)
