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
    normal)     echo -e "$text" | fmt -w 80
                ;;
    quote)      echo -e "\n::\n"
                indent "$text"
                echo
                ;;
  esac
}

function indent {
  echo -e "$@" | sed 's/^/  /' | fmt -w 80
}
function list {
  echo -e "$@" | sed 's/^/* /'
}

declare -a pkgorder
declare -A licenses
declare -A descriptions
declare -A copyrights

for file in $@; do
  if [ -f "$file" ] && [[ "$file" =~ deb$ ]]; then
    pkgname=$(dpkg-deb -f $file package)
    pkgorder+=("$pkgname")
    descriptions[$pkgname]=$(dpkg-deb -f $file Description)
    copyright=$(dpkg-deb --fsys-tarfile $file | tar -xO ./usr/share/doc/$pkgname/copyright 2>/dev/null)

    if [ -z "$copyright" ]; then
      licenses[$pkgname]="unknown"
    else
      case "$copyright" in
        *\ GPL-2+*|*\ GPLv2+*)
                          licenses[$pkgname]+="GPL-2.0+ "
                          ;;&
        *\ GPL-2[!+]*|*\ GPL-2.0*|*common-licenses/GPL-2*|*common-licenses/GPL-2|*either\ version\ 2*|*\ GPLv2[!-]*)
                          licenses[$pkgname]+="GPL-2.0 "
                          ;;&
        *\ GPL-3.0*|*common-licenses/GPL-3*|*common-licenses/GPL[!-]*|*common-licenses/GPL)
                          licenses[$pkgname]+="GPL-3.0 "
                          ;;&
        *\ GPL-1+*)
                          licenses[$pkgname]+="GPL-1.0+ "
                          ;;&
        *LGPL-3.0*|common-licenses/LGPL-3[!\.]*|*common-licenses/LGPL-3|*common-licenses/LGPL|*common-licenses/LGPL[!-]*)
                          licenses[$pkgname]+="LGPL-3.0 "
                          ;;&
        *LGPL-2.0*|*common-licenses/LGPL-2[!\.]*|*common-licenses/LGPL-2)
                          licenses[$pkgname]+="LGPL-2.0 "
                          ;;&
        *LGPL-2.1*|*common-licenses/LGPL-2.1*)
                          licenses[$pkgname]+="LGPL-2.1 "
                          ;;&
        *common-licenses/GFDL[!-]*|*common-licenses/GFDL-1.3*|*common-licenses/GFDL)
                          licenses[$pkgname]+="GFDL-1.3 "
                          ;;&
        *common-licenses/GFDL-1.2*)
                          licenses[$pkgname]+="GFDL-1.2 "
                          ;;&
        *BSD?2?[Cc]lause*|*BSD\ \(2\ Clause\)*|*2-clause\ BSD*|*BSD-2*)
                          licenses[$pkgname]+="BSD-2-Clause "
                          ;;&
        *BSD?3?[Cc]lause*|*BSD\ \(3\ clause\)*|*BSD\ license\ \(3-clause\)*|*BSD-3*|*BSD3*)
                          licenses[$pkgname]+="BSD-3-Clause "
                          ;;&
        *BSD?4?[Cc]lause*|*BSD\ \(4\ Clause\)*|*4-clause\ BSD*|*BSD-4*)
                          licenses[$pkgname]+="BSD-4-Clause "
                          ;;&
        *common-licenses/BSD*|*License:\ BSD[!-]*|*License:\ BSD)
                          licenses[$pkgname]+="BSD "
                          ;;&
        *\ MIT* | *M.I.T.*)
                          licenses[$pkgname]+="MIT "
                          ;;&
        *[Pp]ublic\ [Dd]omain*)
                          licenses[$pkgname]+="Public Domain "
                          ;;&
        *ASL\ 2.0*|*ASL-2*|*Apache-2.0*|*apache.org/licenses/LICENSE-2.0*)
                          licenses[$pkgname]+="Apache-2.0 "
                          ;;&
        *\ ISC*)
                          licenses[$pkgname]+="ISC "
                          ;;&
        *LAPACK*)         licenses[$pkgname]+="LAPACK "
                          ;;&
        *Info-ZIP*)       licenses[$pkgname]+="Info-ZIP "
                          ;;
      esac

      if [ -z "${licenses[$pkgname]}" ]; then
        licenses[$pkgname]="Unknown"
      fi

      copyrights[$pkgname]="$copyright"
    fi
  else
    echo "Skipping non-DEB file $file" 1>&2
  fi
done

if [ -f deb_override ]; then
  . deb_override
fi

output "normal" ".. contents:: Table of Contents"
output "normal" ""
#  output "header" "List of packages"
#  output "list" "$(printf -- '%s\n' "${pkgorder[@]}" | tr ' ' '\n')"

for pkgname in "${pkgorder[@]}"; do
    output "subheader" "Package: $pkgname"
    output "normal" ""
    output "normal" "Description:"
    output "quote" "${descriptions[$pkgname]}"
    output "normal" "License: ${licenses[$pkgname]}"
    if [ -n "${copyrights[$pkgname]}" ]; then
      output "normal" "Copyright text:"
      output "quote" "${copyrights[$pkgname]}"
    else
      output "normal" "Copyright text: Unavailable for this package."
    fi
    output "normal" ""
done

output "header" "Common Licenses"
output "normal" "Many licenses above are only referenced. They are as follows:"
common_licenses="GPL Apache-2.0 BSD GPL-2 GPL-3 LGPL LGPL-3 GFDL"

for license in $common_licenses; do
    output "subheader" "License: $license"
    output "normal" "License text:"
    output "quote" "$(cat /usr/share/common-licenses/$license)"
    output "normal" ""
done