FROM debian:12

RUN apt update && apt install -y python3-dev python3-pip python3-venv vim

#COPY load.py /root
#COPY load_torch.py /root
#COPY pickles /root/pickles

WORKDIR /root

ENV VIRTUAL_ENV=/root/pickle-venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

RUN pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
RUN pip3 install flair

# Replace system pickle with our own
COPY enforce.py /usr/lib/python3.11/pickle.py
