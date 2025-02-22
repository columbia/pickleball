FROM pickleball-enforce:latest

RUN apt-get update && apt-get install -y git
RUN pip install pandas protobuf
RUN pip install git+https://github.com/PrithivirajDamodaran/Parrot_Paraphraser.git

# Path relative to evaluation directory
COPY ./enforcement/utils/modeling_utils.patch /root/modeling_utils.patch
RUN cd /root && patch -p1 < /root/modeling_utils.patch
