FROM ubuntu:14.04

RUN apt-get update -y
RUN apt-get dist-upgrade -y
RUN sh -c 'echo "deb http://download.telldus.com/debian/ stable main" >> /etc/apt/sources.list'
RUN apt-key adv --fetch-keys http://download.telldus.se/debian/telldus-public.key
RUN apt-get update -y
RUN apt-get install -y telldus-core libftdi1
RUN /etc/init.d/telldusd start

RUN apt-get update -y
RUN apt-get install python-pip python-dev build-essential -y
RUN pip install --upgrade pip
RUN pip install --upgrade virtualenv
RUN pip install tellcore-py

RUN pip install paho-mqtt

COPY tellstickCallback.py /tellstick/tellstickCallback.py
COPY startScript.sh /tellstick/startScript.sh
COPY config.ini /tellstick/config.ini
COPY tellstick.conf /etc/tellstick.conf

# Clean up
RUN apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*




CMD ["/tellstick/startScript.sh"]
