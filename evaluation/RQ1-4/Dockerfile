FROM debian:12

RUN apt update && apt install -y python3-dev python3-pip python3-venv strace git

ENV VIRTUAL_ENV=/root/pickle-venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Back up original pickle.py
COPY modeltracer /root/modeltracer

RUN pip3 install -r /root/modeltracer/requirements.txt
RUN pip3 install git+https://github.com/bmwcarit/stracepy.git

WORKDIR /root/modeltracer
