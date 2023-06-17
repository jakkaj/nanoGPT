FROM mcr.microsoft.com/devcontainers/python:0-3.10

RUN sed -i 's/archive\.ubuntu\.com/au.archive.ubuntu.com/g' /etc/apt/sources.list

# eog is a great way to get x11 deps on
RUN apt-get update && export DEBIAN_FRONTEND=noninteractive && \
    apt-get install python3-opencv eog -y && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt /tmp/pip-tmp/

RUN /usr/local/bin/python3 -m pip --disable-pip-version-check --no-cache-dir install -r /tmp/pip-tmp/requirements.txt \
    && rm -rf /tmp/pip-tmp

