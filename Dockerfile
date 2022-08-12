FROM python:3.10

ARG USERID=1000
RUN apt -q -qq update && \
  DEBIAN_FRONTEND=noninteractive apt install -y \
    sudo \
    apt-utils \
    libasound2 \
    libasound2-dev \
    libasound2-plugins \
    alsa-utils \
    libpulse0 \
    libportaudio2 \
    portaudio19-dev \
    --no-install-recommends
RUN /usr/local/bin/python -m pip install --upgrade pip
RUN adduser --system newuser --shell /bin/bash --no-create-home --uid ${USERID} \
  && echo "newuser ALL=(ALL) NOPASSWD: ALL" > /etc/sudoers.d/newuser \
  && chmod 0440 /etc/sudoers.d/newuser

WORKDIR /app
COPY mqtt_micro_asr.py /app
COPY startclient.sh /app
COPY requirements.txt /app
RUN pip install -r requirements.txt
EXPOSE 64738
CMD ["/bin/sh", "-c", "startclient.sh"]
