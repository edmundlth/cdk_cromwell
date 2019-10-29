FROM ubuntu:18.04

RUN apt-get clean && \
    apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y wget \
                       openjdk-11-jre-headless && \
    apt-get clean && \
    apt-get purge && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*


# Cromwell
RUN wget https://github.com/broadinstitute/cromwell/releases/download/45.1/cromwell-45.1.jar && \
    wget https://github.com/broadinstitute/cromwell/releases/download/45.1/womtool-45.1.jar && \
    ln cromwell-45.1.jar cromwell.jar  && \
    ln womtool-45.1.jar womtool.jar
COPY cromwell_awsbatch_with_efs.conf ./cromwell.conf
COPY run_cromwell_server.sh ./