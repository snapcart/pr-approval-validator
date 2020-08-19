FROM python:3.7-slim-stretch

RUN pip install requests jq

COPY . /

RUN chmod +x /entrypoint.sh
ENTRYPOINT [ "/entrypoint.sh" ]
