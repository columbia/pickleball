FROM debian:12

RUN apt update && apt install -y python3-dev python3-pip python3-venv vim

WORKDIR /root

ENV VIRTUAL_ENV=/root/pickle-venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

COPY enforce.py /usr/lib/python3.11/pickle.py
RUN pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

RUN mkdir -p /root/policies
WORKDIR /load-model
