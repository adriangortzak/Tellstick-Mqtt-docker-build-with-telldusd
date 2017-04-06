FROM ubuntu:14.04

RUN apt-get update -y && \
    apt-get dist-upgrade -y && \
    sh -c 'echo "deb http://download.telldus.com/debian/ stable main" >> /etc/apt/sources.list' && \
    apt-key adv --fetch-keys http://download.telldus.se/debian/telldus-public.key && \
    apt-get update -y && \
    apt-get install -y telldus-core libftdi1

RUN apt-get update -y && \
    apt-get install python-pip python-dev build-essential -y

RUN pip install --upgrade pip && \
    pip install --upgrade virtualenv && \
    pip install tellcore-py && \
    pip install paho-mqtt && \
    pip install pylibftdi && \
    pip install crcmod

RUN apt-get install libyaml-dev -y && \
    pip install ruamel.yaml

COPY tellstickService.py /tellstick/tellstickService.py
COPY config.yaml /tellstick/config.yaml
COPY rf433 /tellstick/rf433


# Clean up
RUN apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

CMD python -u /tellstick/tellstickService.py
