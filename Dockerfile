FROM dnxsolutions/aws:1.22.48

WORKDIR /work

COPY blue_green_assets .


ENV PYTHONUNBUFFERED=1
RUN apk add --update --no-cache python3 && ln -sf python3 /usr/bin/python
RUN python3 -m ensurepip
RUN pip3 install --no-cache --upgrade pip setuptools
RUN pip3 install -r ./requirements.txt

ENTRYPOINT [ "python" ]
CMD [ "/work/main.py"]