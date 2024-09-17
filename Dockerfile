FROM debian:12

RUN apt update && apt install -y zlib1g-dev curl gcc expect make wget gettext zip unzip git python3

# install jdk19 sbt
RUN mkdir -p /data/App \
    && cd /data/App \
    && wget https://github.com/sbt/sbt/releases/download/v1.9.8/sbt-1.9.8.zip \
    && unzip *.zip \
    && rm *.zip \
    && mv sbt/ sbt-1.9.8/ \
    && wget https://download.oracle.com/java/19/archive/jdk-19.0.2_linux-x64_bin.tar.gz \
    && tar zxvf *.tar.gz \
    && rm *.tar.gz

RUN git clone https://github.com/wunused/joern.git
WORKDIR joern/
RUN git checkout pyinference-develop

ENV LANG=en_US.UTF-8 \
    JAVA_HOME=/data/App/jdk-19.0.2 \
    PATH=/data/App/sbt-1.9.8/bin:/data/App/jdk-19.0.2/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

RUN sbt stage
