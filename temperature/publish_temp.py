#!/usr/bin/env python

# [START iot_mqtt_includes]
# import i2c_driver
import datetime
import logging
import os
import ssl
import sys
import json 
from threading import Timer
import yaml

import jwt
import paho.mqtt.client as mqtt

logging.getLogger("googleapiclient.discovery_cache").setLevel(logging.CRITICAL)

# The initial backoff time after a disconnection occurs, in seconds.
minimum_backoff_time = 1

# The maximum backoff time before giving up, in seconds.
MAXIMUM_BACKOFF_TIME = 32

# Whether to wait with exponential backoff before publishing.
should_backoff = False

JWT_EXPIRATION_TIME_MIN = 2

REPORTING_FREQUENCY = 30.0

TEMP_DEVICE_PATH='/sys/bus/w1/devices/28-011620e0f1ee/temperature'

to_deg_f = lambda celcius : celcius * 1.8 + 32

def getTemperature():
    temp = 0.0
    with open(TEMP_DEVICE_PATH) as f:
        data = f.read()
        temp = data.strip()
    return temp

# [START iot_mqtt_jwt]
def create_jwt(project_id, private_key_file, algorithm):
    """Creates a JWT (https://jwt.io) to establish an MQTT connection.
    Args:
     project_id: The cloud project ID this device belongs to
     private_key_file: A path to a file containing either an RSA256 or
             ES256 private key.
     algorithm: The encryption algorithm to use. Either 'RS256' or 'ES256'
    Returns:
        A JWT generated from the given project_id and private key, which
        expires in 20 minutes. After 20 minutes, your client will be
        disconnected, and a new JWT will have to be generated.
    Raises:
        ValueError: If the private_key_file does not contain a known key.
    """

    token = {
        # The time that the token was issued at
        "iat": datetime.datetime.now(tz=datetime.timezone.utc),
        # The time the token expires.
        "exp": datetime.datetime.now(tz=datetime.timezone.utc) + datetime.timedelta(minutes=JWT_EXPIRATION_TIME_MIN),
        # The audience field should always be set to the GCP project id.
        "aud": project_id,
    }

    # Read the private key file.
    with open(private_key_file, "r") as f:
        private_key = f.read()

    print(
        "Creating JWT using {} from private key file {}".format(
            algorithm, private_key_file
        )
    )

    return jwt.encode(token, private_key, algorithm=algorithm)


# [END iot_mqtt_jwt]


# [START iot_mqtt_config]
def error_str(rc):
    """Convert a Paho error to a human readable string."""
    return "{}: {}".format(rc, mqtt.error_string(rc))


def on_connect(unused_client, unused_userdata, unused_flags, rc):
    """Callback for when a device connects."""
    print("on_connect", mqtt.connack_string(rc))

    # After a successful connect, reset backoff time and stop backing off.
    global should_backoff
    global minimum_backoff_time
    should_backoff = False
    minimum_backoff_time = 1


def on_disconnect(unused_client, unused_userdata, rc):
    """Paho callback for when a device disconnects."""
    print("on_disconnect", error_str(rc))

    # Since a disconnect occurred, the next loop iteration will wait with
    # exponential backoff.
    global should_backoff
    should_backoff = True


def on_publish(unused_client, unused_userdata, unused_mid):
    """Paho callback when a message is sent to the broker."""
    print("on_publish")


def on_message(unused_client, unused_userdata, message):
    """Callback when the device receives a message on a subscription."""
    payload = str(message.payload.decode("utf-8"))
    print(
        "Received message '{}' on topic '{}' with Qos {}".format(
            payload, message.topic, str(message.qos)
        )
    )

    if 'commands' in message.topic:
        try:
            message = json.loads(payload)
            if 'reporting_frequency_seconds' in message:
                print('Changing reporting frequency')
                global REPORTING_FREQUENCY
                REPORTING_FREQUENCY = message['reporting_frequency_seconds']
        except Exception as e:
            print(e)

def get_client(
    project_id,
    cloud_region,
    registry_id,
    device_id,
    private_key_file,
    algorithm,
    ca_certs,
    mqtt_bridge_hostname,
    mqtt_bridge_port,
):
    """Create our MQTT client. The client_id is a unique string that identifies
    this device. For Google Cloud IoT Core, it must be in the format below."""
    client_id = "projects/{}/locations/{}/registries/{}/devices/{}".format(
        project_id, cloud_region, registry_id, device_id
    )
    print("Device client_id is '{}'".format(client_id))

    client = mqtt.Client(client_id=client_id)

    # With Google Cloud IoT Core, the username field is ignored, and the
    # password field is used to transmit a JWT to authorize the device.
    client.username_pw_set(
        username="unused", password=create_jwt(project_id, private_key_file, algorithm)
    )

    # Enable SSL/TLS support.
    client.tls_set(ca_certs=ca_certs, tls_version=ssl.PROTOCOL_TLSv1_2)

    # Register message callbacks. https://eclipse.org/paho/clients/python/docs/
    # describes additional callbacks that Paho supports. In this example, the
    # callbacks just print to standard out.
    client.on_connect = on_connect
    client.on_publish = on_publish
    client.on_disconnect = on_disconnect
    client.on_message = on_message

    # Connect to the Google MQTT bridge.
    client.connect(mqtt_bridge_hostname, mqtt_bridge_port)

    # This is the topic that the device will receive configuration updates on.
    mqtt_config_topic = "/devices/{}/config".format(device_id)

    # Subscribe to the config topic.
    client.subscribe(mqtt_config_topic, qos=1)

    # The topic that the device will receive commands on.
    mqtt_command_topic = "/devices/{}/commands/#".format(device_id)

    # Subscribe to the commands topic, QoS 1 enables message acknowledgement.
    print("Subscribing to {}".format(mqtt_command_topic))
    client.subscribe(mqtt_command_topic, qos=0)

    return client

def mqtt_device_demo(config):
    # Publish to the events or state topic based on the flag.
    sub_topic = "events" if config['message_type'] == "event" else "state"

    mqtt_topic = "/devices/{}/{}".format(config['gcp_iot']['device_id'], sub_topic)

    print('mqtt_topic: {0}'.format(mqtt_topic))

    jwt_iat = datetime.datetime.now(tz=datetime.timezone.utc)

    client = get_client(
        config['gcp_iot']['project_id'],
        config['gcp_iot']['cloud_region'],
        config['gcp_iot']['registry_id'],
        config['gcp_iot']['device_id'],
        config['certs']['private_key_file'],
        config['certs']['algorithm'],
        config['certs']['ca_certs_file'],
        config['gcp_iot']['mqtt']['mqtt_bridge_hostname'],
        config['gcp_iot']['mqtt']['mqtt_bridge_port'],
    )

    client.loop_start()

    def send_telemetry_data(client):
        now = datetime.datetime.now()
        time = now.strftime('%m/%d/%Y %H:%M:%S')
        
        # payload = {"zone":config['zone_location'], "time": time, "temp": getTemperature()}
        payload = {"zone":config['zone_location'], "time": time, "temp": 12345}
        print("Publishing message: '{}'".format(payload))
        payload = json.dumps(payload)
        client.publish(mqtt_topic, payload, qos=1)

    # def refresh_token(client, jwt_iat):
    #     seconds_since_issue = (datetime.datetime.now(tz=datetime.timezone.utc) - jwt_iat).seconds
    #     if seconds_since_issue > 60 * JWT_EXPIRATION_TIME_MIN:
    #         print("Refreshing token after {}s".format(seconds_since_issue))
    #         logging.debug("Refreshing token after {}s".format(seconds_since_issue))
    #         client.disconnect()
    #         client.loop_stop()
            
    #         jwt_iat = datetime.datetime.now(tz=datetime.timezone.utc)
    #         client = get_client(
    #             config['gcp_iot']['project_id'],
    #             config['gcp_iot']['cloud_region'],
    #             config['gcp_iot']['registry_id'],
    #             config['gcp_iot']['device_id'],
    #             config['certs']['private_key_file'],
    #             config['certs']['algorithm'],
    #             config['certs']['ca_certs_file'],
    #             config['gcp_iot']['mqtt']['mqtt_bridge_hostname'],
    #             config['gcp_iot']['mqtt']['mqtt_bridge_port'],
    #         )
    #         client.loop_start()

    #     send_telemetry_data(client)
    #     Timer(REPORTING_FREQUENCY, refresh_token, [client, jwt_iat]).start()

    try:
        # refresh_token(client, jwt_iat)
        send_telemetry_data(client)
        client.loop_stop()
        client.disconnect()
    except:
        e = sys.exc_info()[0]
        logging.critical(e)


def main():
    stream = open("config.yml", 'r')
    configuration = yaml.safe_load(stream)

    global REPORTING_FREQUENCY
    REPORTING_FREQUENCY = configuration['reporting_frequency_seconds'] if 'reporting_frequency_seconds' in configuration else 30.0
    try:
        mqtt_device_demo(configuration)
    except:
        e = sys.exc_info()[0]
        logging.critical(e)



if __name__ == "__main__":
    main()
