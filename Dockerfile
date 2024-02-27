FROM python:3.12
LABEL maintainer="s@mck.la"

RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    ntp \
    && mkdir -p /opt/email2printerftp/downloadedFiles
RUN pip install requests
ADD main.py /opt/email2printerftp/
#RUN pip3 install 
WORKDIR /opt/email2printerftp/


VOLUME ["/opt/email2printerftp"]

ENTRYPOINT python -u /opt/email2printerftp/main.py

