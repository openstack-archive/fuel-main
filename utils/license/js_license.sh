#!/bin/bash

output_type="rst"
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
    normal)     echo -e "$text" | fmt
                ;;
    quote)      echo -e "\n::\n"
                indent "$text"
                echo
                ;;
  esac
}

function indent {
  echo -e "$@" | sed 's/^/  /' | fmt
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

if [ -f js_override ]; then
    . js_override
else
    echo "No JS libs info file found, exiting"
    exit 1
fi

for lib in $(echo $js_libs); do
    pkgname=$lib
    pkgorder+=("$pkgname")
done

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