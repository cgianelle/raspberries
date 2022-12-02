#!/bin/bash

ZONE=$1

echo $ZONE

openssl req -x509 -newkey rsa:2048 -keyout rsa_${ZONE}_private.pem -nodes -out rsa_${ZONE}_cert.pem -subj "/CN=unused"