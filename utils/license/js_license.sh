#!/bin/bash
git clone https://github.com/stackforge/fuel-web /tmp/fuel-web

output_type="rst"
func="$1"
shift

function output {
  style="$1"
  text="$2"
  if [[ "$output_type" != "rst" ]]; then
    echo -e "$text"
    return
  fi
  case $style in
    header)     echo
                echo -e "$text"
                echo -e "$text" | tr '[:print:]' '='
                echo
                ;;
    subheader)  echo
                echo -e "$text"
                echo -e "$text" | tr '[:print:]' '-'
                echo
                ;;
    list)       list "$text"
                ;;
    normal)     echo -e "$text"
                ;;
    quote)      echo -e "\n::\n"
                indent "$text"
                echo
                ;;
  esac
}

function indent {
  echo -e "$@" | sed 's/^/  /'
}
function list {
  echo -e "$@" | sed 's/^/* /'
}

output "normal" ".. contents:: Table of Contents"
output "normal" ""
declare -a pkgorder
declare -A licenses
declare -A descriptions
declare -A copyrights

pkglist=$(./js_license_helper.py -L)
pkglist+=$(echo;ls /tmp/fuel-web/nailgun/static/js/libs/custom| cut -d\. -f1|cut -d\- -f1,2|sort -u)

for package in $(echo $pkglist); do
    pkgname=$(echo $package|cut -d/ -f1)
    pkgorder+=("$pkgname")
    licenses[$pkgname]=$(./js_license_helper.py -l $package)
    descriptions[$pkgname]=$(./js_license_helper.py -d $package)
    copyrights[$pkgname]=$(./js_license_helper.py -c $package)
done

licenses["active-x-obfuscator"]="MIT"
licenses["assert-plus"]="MIT"
licenses["dateformat"]="MIT"
licenses["asn1"]="MIT"
licenses["aws-sign"]="Apache-2.0"
licenses["aws-sign2"]="Apache-2.0"
licenses["base62"]="MIT"
licenses["backbone-deep-model"]="MIT"
licenses["base64id"]="MIT"
licenses["batch"]="MIT"
licenses["buffer-crc32"]="MIT"
licenses["buffers"]="MIT"
licenses["bytes"]="MIT"
licenses["cli-color"]="MIT"
licenses["colors"]="MIT"
licenses["combined-stream"]="MIT"
licenses["commander"]="MIT"
licenses["config-chain"]="MIT"
licenses["coccyx"]="GPL-3.0"
licenses["cookie"]="MIT"
licenses["cookie-jar"]="MIT"
licenses["cookie-signature"]="MIT"
licenses["ctype"]="MIT"
licenses["debug"]="MIT"
licenses["delayed-stream"]="MIT"
licenses["domelementtype"]="BSD-3-Clause"
licenses["domhandler"]="BSD-3-Clause"
licenses["domutils"]="BSD-3-Clause"
licenses["i18next"]="MIT"
licenses["ini"]="MIT"
licenses["install"]="MIT"
licenses["jison-lex"]="MIT"
licenses["jison"]="MIT"
licenses["jquery-cookie"]="MIT"
licenses["json"]="Public Domain"
licenses["gex"]="MIT"
licenses["fresh"]="MIT"
licenses["forever-agent"]="Apache-2.0"
licenses["event-emitter"]="MIT"
licenses["es5-ext"]="MIT"
licenses["http-signature"]="MIT"
licenses["logmagic"]="Apache-2.0"
licenses["magic-templates"]="MIT"
licenses["mime"]="MIT"
licenses["node-inspector"]="BSD-3-Clause"
licenses["node-uuid"]="MIT"
licenses["nomnom"]="MIT"
licenses["oauth-sign"]="Apache-2.0"
licenses["options"]="MIT"
licenses["pause"]="MIT"
licenses["qs"]="MIT"
licenses["rc"]="MIT"
licenses["require-css"]="MIT"
licenses["requirejs-plugins"]="MIT"
licenses["requirejs-text"]="MIT"
licenses["which"]="MIT"
licenses["JSONSelect"]="MIT"
licenses["redis"]="MIT"
licenses["retry"]="MIT"
licenses["send"]="MIT"
licenses["simplesets"]="MIT"
licenses["socket.io"]="MIT"
licenses["socket.io-client"]="MIT"
licenses["truncate"]="MIT"
licenses["touch"]="ISC"
licenses["tinycolor"]="MIT"
licenses["tunnel-agent"]="Apache-2.0"
licenses["uglify-js"]="BSD"
licenses["uid2"]="MIT"
licenses["uuid"]="MIT"
licenses["ws"]="MIT"
licenses["zeparser"]="MIT"

for pkgname in "${pkgorder[@]}"; do
    description=${descriptions[$pkgname]}
    copyright=${copyrights[$pkgname]}
    license=${licenses[$pkgname]}
    output "subheader" "Package: $pkgname"
    output "normal" ""
    output "normal" "Description:"
    output "quote" "$description"
    output "normal" "License: $license"
    output "normal" ""
    if [ -n "$copyright" ]; then
      output "normal" "Copyright text:"
      output "quote" "$copyright"
    else
      output "normal" "Copyright text: Unavailable for this package."
    fi
    output "normal" ""
done

rm -rf /tmp/fuel-web