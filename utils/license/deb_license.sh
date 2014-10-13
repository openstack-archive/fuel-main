#!/bin/bash
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
if [ -z "$func" ]; then
  echo "Available commands: list (%name-%license) or detail (print copyright)"
fi
declare -a pkgorder
declare -A licenses
declare -A copyrights
for file in $@; do
  pkgname=$(dpkg-deb -f $file package)
  pkgorder+=("$pkgname")
  copyright=$(dpkg-deb --fsys-tarfile $file | tar -xO ./usr/share/doc/$pkgname/copyright 2>/dev/null)
  if [ -z "$copyright" ]; then
    licenses[$pkgname]="unknown"
  else
    case "$copyright" in
      *GPL-2*)		licenses[$pkgname]="GPLv2"
			;;
      *GPLv2*)		licenses[$pkgname]="GPLv2"
			;;
      *either\ version\ 2*)
                        licenses[$pkgname]="GPLv2"
                        ;;
      *LGPLv3*)         licenses[$pkgname]="LGPLv3"
                        ;;
      *LGPLv2*)         licenses[$pkgname]="LGPLv2"
                        ;;
      *GFDL*)           licenses[$pkgname]="GFDL"
                        ;;
      *BSD*)            licenses[$pkgname]="BSD"
                        ;;
      *MIT*)            licenses[$pkgname]="MIT"
                        ;;
      *M.I.T.*)         licenses[$pkgname]="MIT"
                        ;;
      *public\ domain*) licenses[$pkgname]="Public Domain"
                        ;;
      *Public\ Domain*) licenses[$pkgname]="Public Domain"
                        ;;
      *ASL*)            licenses[$pkgname]="ASL 2.0"
                        ;;
      *Apache*)         licenses[$pkgname]="Apache"
                        ;;
      *GPLv3*)          licenses[$pkgname]="GPLv3"
                        ;;
      *GPL-3*)		licenses[$pkgname]="GPLv3"
			;;
      *ISC*)		licenses[$pkgname]="ISC"
			;;
      *LGPL*)           licenses[$pkgname]="LGPL"
                        ;;
      *common-licenses/GPL*)
                        licenses[$pkgname]="GPL"
                        ;;
      *LAPACK*)         licenses[$pkgname]="LAPACK"
                        ;;
      *Info-ZIP*)       licenses[$pkgname]="Info-ZIP"
                        ;;
      *)                licenses[$pkgname]="unknown"
    esac
    copyrights[$pkgname]="$copyright"
  fi
done

#Fixes for packages with no copyright file
licenses["apache2-mpm-prefork"]="BSD"
licenses["apache2-mpm-worker"]="BSD"
licenses["apache2"]="BSD"
licenses["cirros-testvm-mellanox"]="GPLv2"
licenses["cirros-testvm"]="GPLv2"
licenses["cirros-testvmware"]="GPLv2"
licenses["dhcp-checker"]="ASL 2.0"
licenses["fencing-agent"]="ASL 2.0"
licenses["fuel-utils"]="ASL 2.0"
licenses["g++-4.6"]="GPLv3"
licenses["galera"]="GPLv3"
licenses["gcc-4.6"]="GPLv2"
licenses["gcc"]="GPLv2"
licenses["grub2-common"]="GPLv3"
licenses["g++"]="GPLv3"
licenses["hdparm"]="BSD"
licenses["klibc-utils"]="GPLv3"
licenses["libapache2-mod-php5"]="MIT"
licenses["libgcc1"]="GPLv2"
licenses["libgfortran3"]="GPLv2"
licenses["libgomp1"]="GFDL"
licenses["libnih-dbus1"]="GPL"
licenses["libperl5.14"]="GPL"
licenses["libpython2.7"]="GPLv2"
#licenses["libquadmath0"]="unknown"
#licenses["libsnmp-perl"]="unknown"
licenses["libstdc++6-4.6-dev"]="GPLv2"
licenses["libstdc++6"]="GPLv2"
licenses["libterm-readkey-perl"]="GPL"
licenses["libtidy-0.99-0"]="W3C"
#licenses["libwrap0"]="unknown"
#licenses["lsof"]="unknown"
#licenses["mlnx-ofed-light"]="unknown"
licenses["murano-api"]="ASL 2.0"
licenses["murano-apps"]="ASL 2.0"
licenses["murano-dashboard"]="ASL 2.0"
licenses["nailgun-agent"]="ASL 2.0"
licenses["nailgun-mcagents"]="ASL 2.0"
licenses["nailgun-net-check"]="ASL 2.0"
licenses["netcat-traditional"]="BSD"
licenses["netcat"]="BSD"
licenses["openssh-server"]="BSD"
licenses["openssl"]="BSD"
licenses["perl-base"]="GPLv2"
licenses["perl"]="GPLv2"
licenses["sahara-dashboard"]="ASL 2.0"
licenses["sahara"]="ASL 2.0"
licenses["tcpd"]="MIT"
#licenses["xinetd"]="unknown"
#licenses["zlib1g"]="unknown

if [[ "$func" == "detail" ]]; then
  output "normal" ".. contents:: Table of Contents"
  output "normal" ""
  output "header" "List of packages"
  output "normal" "${pkgorder[@]}" | tr ' ' '\n'
fi


for pkgname in "${pkgorder[@]}"; do
  license=${licenses[$pkgname]}
  #Try to fix unknown licenses
  if [[ "$license" == "unknown" ]]; then
    common_guess="$(echo $pkgname | cut -d- -f1)-common"
    common_guess2="$(echo $pkgname | OFS=- cut -d- -f1-2)-common"
    base_guess="$(echo $pkgname | cut -d- -f1)"
    base_guess2="$(echo $pkgname | OFS=- cut -d- -f1-2)"
    if [ -n "${licenses[$common_guess]}" ]; then
      license="${licenses[$common_guess]}"
    elif [ -n "${licenses[$common_guess2]}" ]; then
      license="${licenses[$common_guess2]}"
    elif [ -n "${licenses[$base_guess]}" ]; then
      license="${licenses[$base_guess]}"
    elif [ -n "${licenses[$base_guess2]}" ]; then
      license="${licenses[$base_guess2]}"
    fi
  fi
      
  
  case $func in
    list)		echo "$pkgname-$license"
                        ;;
    pkglist)            echo "$pkgname contents:"
                        dpkg-deb -c "$file"
                        ;;
    detail)             output "subheader" "Package: $pkgname"
                        output "normal" "License: $license"
                        if [ -n "${copyrights[$pkgname]}" ]; then 
                          output "normal" "Copyright text:"
                          output "quote" "${copyrights[$pkgname]}"
                        else
                          output "normal" "Copyright text: Unavailable for this package."
                        fi
                        output "normal" ""
                        ;;
    *)                  echo "Invalid function: $func" 1>&2
                        exit 1
                        ;;
  esac
done

output "header" "Common Licenses"
output "normal" "Many licenses above are only referenced. They are as follows:"
common_licenses="GPL Apache-2.0 BSD GPL-2 GPL-3 LGPL LGPL-3 GFDL"
for license in $common_licenses; do
  output "subheader" "License: $license"
  output "normal" "Text:"
  output "quote" "$(cat /usr/share/common-licenses/$license)"
  output "normal" ""
done
