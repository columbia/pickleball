FROM pickleball-enforce:latest

RUN pip3 install -U sentence-transformers
COPY modeling_utils.patch /root/modeling_utils.patch
RUN cd /root && patch -p1 < /root/modeling_utils.patch
