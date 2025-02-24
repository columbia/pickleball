FROM debian:12

RUN apt update && apt install -y python3-dev python3-pip python3-venv vim

WORKDIR /root

ENV VIRTUAL_ENV=/root/pickle-venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Back up original pickle.py
RUN cp /usr/lib/python3.11/pickle.py /root/pickle-bak.py

COPY enforce-strict.py /usr/lib/python3.11/pickle.py
COPY pklballcheck.py /usr/lib/python3.11/pklballcheck.py
RUN pip3 install torch==2.5.0+cpu torchvision==0.20.0 torchaudio==2.5.0 --index-url https://download.pytorch.org/whl/cpu
RUN pip3 install transformers==4.46.1

RUN mkdir -p /root/policies
WORKDIR /load-model
