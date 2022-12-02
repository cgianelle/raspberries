# Temperature Sensor

## Install Linux Modules
~~~~
# sudo nano /boot/config.txt
# dtoverlay=w1-gpio,gpiopin=4
# sudo reboot
...After Rebooting...
# sudo modprobe w1-gpio
# sudo modprobe w1-therm
~~~~

## Create Device Keys
Use the Google CA root certificate
~~~~
# openssl req -x509 -newkey rsa:2048 -keyout rsa_${ZONE}_private.pem -nodes -out rsa_${ZONE}_cert.pem -subj "/CN=unused"
~~~~

## Install Python Packages
Rust needs to be installed first for libcst
~~~~
# curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
~~~~

Restart Terminal and then Install packages
~~~~
pip3 install -r requirements.txt 
~~~~

## Setup Cronjob
Install postfix for internal status
~~~~
# sudo apt-get install postfix
~~~~

Setup Cron
~~~~
# crontab -e
*/1 * * * * cd <to where directory where script is>; python3 publish_temp.py
~~~~

To check status
~~~~
cat /var/mail/pi
~~~~

## Running Sensor
python3 publish_temp.py  --registry_id=home_1086_NLW_registry     --cloud_region=us-central1     --project_id=newliberty-iot-sandbox     --device_id=raspberrypi_3b_temp_basement     --algorithm=RS256     --private_key_file=./rpi_basement_private.pem  --ca_certs=./ca_cert.pem 