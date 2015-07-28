#!/bin/bash

SYSLOG_SERVER_IP=$(grep -oPz '(?<=\bip=)(\d+\.?){4}:\K(\d+\.?){4}' /proc/cmdline)
DEPLOYMENT_ID=$(grep -ioP '(?<=\bdeployment_id=)([0-9a-z-]+)\b' /proc/cmdline)

sed -i /etc/rsyslog.d/00-remote.conf -re "s/@SYSLOG_SERVER_IP@/$SYSLOG_SERVER_IP/"
sed -i /etc/rsyslog.d/00-remote.conf -re "s/@DEPLOYMENT_ID@/$DEPLOYMENT_ID/"

service rsyslog restart
