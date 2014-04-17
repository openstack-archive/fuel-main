#!/bin/bash
puppet apply -v /root/site.pp
/usr/bin/supervisord -n
