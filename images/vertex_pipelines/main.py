from urllib import response
from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel
from base64 import b64decode
from datetime import datetime
import subprocess
import ast
import os
import uuid

app = FastAPI()


class Message(BaseModel):
    data: str
    messageId: str
    message_id: str
    publishTime: str
    publish_time: str


class PubsubModel(BaseModel):
    message: Message
    subscription: str


class Item(BaseModel):
    name: Message
    price: float
    is_offer: bool = None


def gcloud_run(message):

    # setting the uuid

    ref_id = str(uuid.uuid4().hex)
    print('process starts')
    parameter = ast.literal_eval(str(message))
    print(parameter)
    # Fetch the input parameters
    ref_file_path = parameter['ref_file_path']
    PROJECT_ID = parameter['PROJECT_ID']
    BUCKET_NAME = parameter['BUCKET_NAME']
    base = os.path.basename(ref_file_path)
    ref_name = os.path.splitext(base)[0]
    dir_name = os.path.dirname(ref_file_path)
    mapping = parameter['mapping']

    # run gsutil cp to get all the pipelines files into a temp pipelines folder
    p = subprocess.run(
        ['/bin/bash', 'gcloud_run.sh', PROJECT_ID, ref_id],
        stdin=None,
        stdout=None,
        stderr=None)
    print(p.returncode)

    # print(listdir())

    import sys
    import importlib

    print('validate if the pipeline ref exists')
    print(os.listdir('./pipelines{}/{}/'.format(ref_id, dir_name)))

    sys.path.insert(1, './pipelines{}/{}/'.format(ref_id, dir_name))
    ref = importlib.import_module("{}".format(ref_name))

    from datetime import datetime
    import google.cloud.aiplatform as aip
    from kfp.v2 import compiler  # noqa: F811

    PIPELINE_ROOT = "{}".format(BUCKET_NAME)
    TIMESTAMP = datetime.now().strftime("%Y%m%d%H%M%S")
    aip.init(project=PROJECT_ID, staging_bucket=BUCKET_NAME)

    pipe_ref = str(ref_name) + ref_id
    compiler.Compiler().compile(
        pipeline_func=ref.main(mapping),
        package_path="{}.json".format(pipe_ref),
    )

    DISPLAY_NAME = str(ref_name) + TIMESTAMP

    job = aip.PipelineJob(
        display_name=DISPLAY_NAME,
        template_path="{}.json".format(pipe_ref),
        # job_id=str(ref_name).replace('_','-') + TIMESTAMP,
        pipeline_root=PIPELINE_ROOT,
        enable_caching=False,
        location="northamerica-northeast1"
    )

    tmp_folder = 'pipelines' + ref_id
    # delete the temp pipelines folder
    d = subprocess.run(
        ['/bin/bash', 'gcloud_rm.sh', PROJECT_ID, ref_id],
        stdin=None,
        stdout=None,
        stderr=None)

    print(d.returncode)

    result = job.run()
    return result


@app.post("/",  status_code=201)
def create_item(model: PubsubModel, background_tasks: BackgroundTasks):
    print(b64decode(model.message.data).decode("utf-8"))
    message = b64decode(model.message.data).decode("utf-8")
    background_tasks.add_task(gcloud_run, message)
    return "", 201
