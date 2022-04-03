FROM gcr.io/google.com/cloudsdktool/cloud-sdk:latest

ENV PYTHONUNBUFFERED True
COPY requirements.txt ./

RUN pip install -r requirements.txt

ENV APP_HOME /app
WORKDIR $APP_HOME
COPY . ./

CMD exec gunicorn --bind :$PORT --workers 1 --worker-class uvicorn.workers.UvicornWorker  --threads 8 main:app