FROM pickleball-enforce:latest

RUN apt-get update && apt-get install -y git

#RUN pip install packaging wheel
#RUN pip install FlagEmbedding peft
RUN git clone https://github.com/FlagOpen/FlagEmbedding.git
WORKDIR FlagEmbedding
RUN pip install .

COPY modeling_utils.patch /root/modeling_utils.patch
#RUN cd /root && patch -p1 < /root/modeling_utils.patch
