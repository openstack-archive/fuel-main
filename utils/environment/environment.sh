#!/bin/bash 

env_name="$2"

case "$1" in
"" | "-h" | "--help") echo -e "NO PARAMETERS\n""USAGE:     $0 <zip/unzip> <ENV_NAME>\n<ENV_NAME> - common name's part of all virtual machines\n"; exit 65;;

zip*) ./lib/zip.sh $env_name;; 

unzip*) ./lib/unzip.sh $env_name;;  

* ) echo "Wrong argument";;     
esac
