#!/bin/sh
PATH='/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin'

ps axuwww | grep -v grep | grep -q " acpid "
if [ $? -gt 0 ]; then
  return 0
else
  return 1
fi
