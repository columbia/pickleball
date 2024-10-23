FROM pickleball-enforce:latest

RUN apt-get update && apt-get install -y git

COPY ./LanguageBind /LanguageBind
WORKDIR /LanguageBind
RUN pip install -r requirements.txt
