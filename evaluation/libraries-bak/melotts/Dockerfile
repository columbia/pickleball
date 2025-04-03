FROM pickleball-enforce:latest

WORKDIR /melotts
RUN apt-get update && apt-get install git -y
RUN git clone https://github.com/myshell-ai/MeloTTS.git

WORKDIR /melotts/MeloTTS
RUN pip install -e .
RUN python -m unidic download
RUN python -c "import nltk; nltk.download('averaged_perceptron_tagger_eng')"

WORKDIR /load-model
