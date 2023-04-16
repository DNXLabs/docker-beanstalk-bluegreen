FROM dnxsolutions/aws-v2:2.4.29-dnx1

WORKDIR /work

COPY src/requirements.txt .

ENV PYTHONUNBUFFERED=1
RUN apk add --update --no-cache python3 && ln -sf python3 /usr/bin/python && python3 -m ensurepip && pip3 install --no-cache-dir  --upgrade -r ./requirements.txt


COPY src .
COPY testing_env .

ENTRYPOINT [ "python", "/work/main.py" ]
#ENTRYPOINT [ "python", "/work/test.py" ]