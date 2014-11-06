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

pkglist=$(./js_license_helper.py -list)
pkglist+=$(echo;ls /tmp/fuel-web/nailgun/static/js/libs/custom| cut -d\. -f1|cut -d\- -f1,2|sort -u)

for package in $(echo $pkglist); do
    pkgname=$(echo $package|cut -d/ -f1)
    pkgorder+=("$pkgname")
    licenses[$pkgname]=$(./js_license_helper.py -license $package)
    descriptions[$pkgname]=$(./js_license_helper.py -description $package)
    copyrights[$pkgname]=$(./js_license_helper.py -copyright $package)
done

licenses["active-x-obfuscator"]="MIT"
licenses["asn1"]="MIT"
licenses["aws-sign"]="Apache"
licenses["aws-sing2"]="Apache"
licenses["base62"]="MIT"
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