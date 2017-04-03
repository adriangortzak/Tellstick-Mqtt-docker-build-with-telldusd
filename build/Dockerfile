FROM ubuntu:14.04

RUN apt-get update -y
RUN apt-get dist-upgrade -y
RUN sh -c 'echo "deb http://download.telldus.com/debian/ stable main" >> /etc/apt/sources.list'
RUN apt-key adv --fetch-keys http://download.telldus.se/debian/telldus-public.key
RUN apt-get update -y
RUN apt-get install -y telldus-core libftdi1
RUN /etc/init.d/telldusd start

RUN apt-get update -y
RUN apt-get install -y zip 
RUN apt-get install -y wget
RUN wget https://github.com/juppinet/jstick/raw/master/target/jstick-api-1.7.jar
RUN wget https://maven.java.net/content/repositories/releases/net/java/dev/jna/jna/4.1.0/jna-4.1.0.jar
RUN wget http://apache.mirrors.spacedump.net//commons/logging/binaries/commons-logging-1.2-bin.zip
RUN unzip commons-logging-1.2-bin.zip;mv commons-logging-1.2/commons-logging-1.2.jar .;rm -rf commons-logging-1.2 commons-logging-1.2-bin.zip

RUN apt-get update -y
RUN apt-get install python-pip python-dev build-essential -y
RUN pip install --upgrade pip
RUN pip install --upgrade virtualenv
RUN pip install tellcore-py


RUN pip install paho-mqtt



COPY tellstickCallback.py /tellstick/tellstickCallback.py
COPY startScript.sh /tellstick/startScript.sh
COPY tellstick.conf /etc/tellstick.conf
# Clean up
RUN apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*




CMD ["/tellstick/startScript.sh"]
