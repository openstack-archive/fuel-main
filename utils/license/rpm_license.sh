#!/bin/bash
#!/bin/bash
output_type="rst"

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
    quote)      echo -e "::\n"
                indent "$text"
                echo
                ;;
  esac
}

function list {
  echo -e "$@" | sed 's/^/* /'
}
function indent {
  echo -e "$@" | sed 's/^/  /'
}


declare -a pkgorder
declare -A licenses
declare -A copyrights
for file in "$@"; do
  if [ -f "$file" ] && [[ "$file" =~ rpm$ ]]; then
    pkgname=$(rpm -qp --queryformat="%{NAME}" "$file" 2>/dev/null)
    pkgorder+=("$pkgname")
    license=$(rpm -qp --queryformat='%{LICENSE}' "$file" 2>/dev/null)
    licenses["$pkgname"]=$license
    licensefile=$(rpm -qpd "$file" 2>/dev/null| egrep -i '(LICENSE$|COPYING$)')
    if [ -n "$licensefile" ]; then
      copyrights[$pkgname]="$(rpm2cpio "$file" 2>/dev/null| cpio -iv --to-stdout ".$licensefile" 2>/dev/null)"
    fi
  else
    echo "Skipping non-RPM file $file" 1>&2
  fi
done

output "normal" ".. contents:: Table of Contents"
output "normal" ""
output "header" "List of packages"
output "list" "$(printf -- '%s\n' "${pkgorder[@]}" | tr ' ' '\n')"

for pkgname in "${pkgorder[@]}"; do
  output "subheader" "Package: $pkgname"
  output "normal" "License: $license"
  output "normal" ""
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
  output "quote" "$(cat "/usr/share/common-licenses/$license")"
  output "normal" ""
done
