FROM python

COPY . .

RUN curl -L https://get.pulumi.com/ | bash
RUN pip3 install --upgrade pulumi==3.18.1
RUN pip3 install --upgrade pulumi-gcp
RUN pip3 install --upgrade Cerberus==1.3.4
RUN pip3 install --upgrade google-cloud-build
RUN pip3 install --upgrade google-cloud-storage
RUN pip3 install --upgrade croniter==1.2.0

ENV PULUMI_SKIP_UPDATE_CHECK=false
ENV PATH=$PATH:/root/.pulumi/bin

RUN pulumi plugin install resource gcp v6.2.0

ENTRYPOINT [ "pulumi", "version" ]