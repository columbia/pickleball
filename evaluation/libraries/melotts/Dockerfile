FROM pickleball-enforce:latest

WORKDIR /melotts
RUN apt-get update && apt-get install git -y
RUN git clone https://github.com/myshell-ai/MeloTTS.git

WORKDIR /melotts/MeloTTS
RUN pip install -e .
RUN python -m unidic download

WORKDIR /load-model
