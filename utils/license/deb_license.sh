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

if [ -z "$func" ]; then
  echo "Available commands: list (%name-%license) or detail (print copyright)"
fi
declare -a pkgorder
declare -A licenses
declare -A descriptions
declare -A encryptions
declare -A encryptionuse
declare -A copyrights
for file in $@; do
  if [ -f "$file" ] && [[ "$file" =~ deb$ ]]; then
    pkgname=$(dpkg-deb -f $file package)
    pkgorder+=("$pkgname")
    descriptions[$pkgname]=$(dpkg-deb -f $file Description)
    copyright=$(dpkg-deb --fsys-tarfile $file | tar -xO ./usr/share/doc/$pkgname/copyright 2>/dev/null)
    encryption=$(dpkg-deb -f $file Depends|egrep -i "libssl|openssl|crypt")
    if [ -z "$encryption" ]; then
      encryptions[$pkgname]="None"
    else
      case "$encryption" in
        *erlang*)          encryptions[$pkgname]="openSSL"
                           ;;
        *m2crypto*)        encryptions[$pkgname]="openSSL"
                           ;;
        *openssl*)         encryptions[$pkgname]="openSSL"
                           ;;
        *libssl*)          encryptions[$pkgname]="openSSL"
                           ;;
        *jsencrypt*)       encryptions[$pkgname]="openSSL"
                           ;;
        *libgnutls*)       encryptions[$pkgname]="libgnutls"
                           ;;
        *gnupg*)           encryptions[$pkgname]="gnupg"
                           ;;
        *libgcrypt*)       encryptions[$pkgname]="libgcrypt"
                           ;;
        *cryptsetup*)      encryptions[$pkgname]="libgcrypt"
                           ;;
        *libk5crypto*)     encryptions[$pkgname]="libhcrypto"
                           ;;
        *libhcrypto*)      encryptions[$pkgname]="libhcrypto"
                           ;;
        *python-crypto*)   encryptions[$pkgname]="python-crypto"
                           ;;
        *)                 encryptions[$pkgname]="unknown"
                           ;;
      esac
    fi
    if [ -z "$copyright" ]; then
      licenses[$pkgname]="unknown"
    else
      case "$copyright" in
        *GPL-2*)          licenses[$pkgname]="GPL-2.0"
                          ;;
        *GPL-2.0*)          licenses[$pkgname]="GPL-2.0"
                          ;;
        *either\ version\ 2*)
                          licenses[$pkgname]="GPL-2.0"
                          ;;
        *LGPL-3.0*)         licenses[$pkgname]="LGPL-3.0"
                          ;;
        *LGPL-2.0*)         licenses[$pkgname]="LGPL-2.0"
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
        *ASL*)            licenses[$pkgname]="Apache-2.0"
                          ;;
        *Apache*)         licenses[$pkgname]="Apache"
                          ;;
        *GPL-3.0*)          licenses[$pkgname]="GPL-3.0"
                          ;;
        *GPL-3*)          licenses[$pkgname]="GPL-3.0"
                          ;;
        *ISC*)            licenses[$pkgname]="ISC"
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
  else
    echo "Skipping non-DEB file $file" 1>&2
  fi
done

#Fixes for packages with no copyright file
licenses["apache2-mpm-prefork"]="BSD"
licenses["apache2-mpm-worker"]="BSD"
licenses["apache2"]="BSD"
licenses["cirros-testvm-mellanox"]="GPL-2.0"
licenses["cirros-testvm"]="GPL-2.0"
licenses["cirros-testvmware"]="GPL-2.0"
licenses["dhcp-checker"]="Apache-2.0"
licenses["fencing-agent"]="Apache-2.0"
licenses["fuel-utils"]="Apache-2.0"
licenses["g++-4.6"]="GPL-3.0"
licenses["galera"]="GPL-3.0"
licenses["gcc-4.6"]="GPL-2.0"
licenses["gcc"]="GPL-2.0"
licenses["grub2-common"]="GPL-3.0"
licenses["g++"]="GPL-3.0"
licenses["hdparm"]="BSD"
licenses["klibc-utils"]="GPL-3.0"
licenses["libapache2-mod-php5"]="MIT"
licenses["libgcc1"]="GPL-2.0"
licenses["libgfortran3"]="GPL-2.0"
licenses["libgomp1"]="GFDL"
licenses["libnih-dbus1"]="GPL"
licenses["libperl5.14"]="GPL"
licenses["libpython2.7"]="GPL-2.0"
licenses["libstdc++6-4.6-dev"]="GPL-2.0"
licenses["libstdc++6"]="GPL-2.0"
licenses["libterm-readkey-perl"]="GPL"
licenses["libtidy-0.99-0"]="W3C"
licenses["murano-api"]="Apache-2.0"
licenses["murano-apps"]="Apache-2.0"
licenses["murano-dashboard"]="Apache-2.0"
licenses["nailgun-agent"]="Apache-2.0"
licenses["nailgun-mcagents"]="Apache-2.0"
licenses["nailgun-net-check"]="Apache-2.0"
licenses["netcat-traditional"]="BSD"
licenses["netcat"]="BSD"
licenses["openssh-server"]="BSD"
licenses["openssl"]="BSD"
licenses["perl-base"]="GPL-2.0"
licenses["perl"]="GPL-2.0"
licenses["sahara-dashboard"]="Apache-2.0"
licenses["sahara"]="Apache-2.0"
licenses["tcpd"]="MIT"

# Basic purposes of encryption usage for some packages
encryptionuse["sslserver"]="Uses parts of openSSL to listen for secure SSLv2/SSLv3 connections"
encryptionuse["sslclient"]="Uses parts of openSSL to connect to secure SSL hosts"
encryptionuse["sshserver"]="Uses parts of openSSL to listen for secure shell connections"
encryptionuse["sshclient"]="Uses parts of openSSL to connect to ssh hosts"
encryptionuse["ssldebug"]="Uses parts of openSSL to debug SSL connections"

if [[ "$func" == "detail" ]]; then
  output "normal" ".. contents:: Table of Contents"
  output "normal" ""
#  output "header" "List of packages"
#  output "list" "$(printf -- '%s\n' "${pkgorder[@]}" | tr ' ' '\n')"
fi


for pkgname in "${pkgorder[@]}"; do
  encryption=${encryptions[$pkgname]}
  description=${descriptions[$pkgname]}
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
  case "$pkgname" in
    *nginx*)            encryptionuse[$pkgname]=${encryptionuse["sslserver"]}
                        ;;
    *openssh-server*)   encryptionuse[$pkgname]=${encryptionuse["sshserver"]}
                        ;;
    *openssh-client*)   encryptionuse[$pkgname]=${encryptionuse["sshclient"]}
                        ;;
    *nagios*)           encryptionuse[$pkgname]=${encryptionuse["sslserver"]}
                        ;;
    *apache*)           encryptionuse[$pkgname]=${encryptionuse["sslserver"]}
                        ;;
    *ipmitool*)         encryptionuse[$pkgname]=${encryptionuse["sslclient"]}
                        ;;
    *mysql-server*)     encryptionuse[$pkgname]=${encryptionuse["sslserver"]}
                        ;;
    *nrpe*)             encryptionuse[$pkgname]=${encryptionuse["sslclient"]}
                        ;;
    *postfix*)          encryptionuse[$pkgname]=${encrypyionuse["sslserver"]}
                        ;;
    *postgres*)         encryptionuse[$pkgname]=${encryptionuse["sslserver"]}
                        ;;
    *keepalived*)       encryptionuse[$pkgname]=${encryptionuse["sslserver"]}
                        ;;
    *tcpdump*)          encryptionuse[$pkgname]=${encryptionuse["ssldebug"]}
                        ;;
    *wget*)             encryptionuse[$pkgname]=${encryptionuse["sslclient"]}
                        ;;
    *zabbix*)           encryptionuse[$pkgname]=${encryptionuse["sslserver"]}
                        ;;
  esac
 
  case $func in
    list)		echo "$pkgname-$license"
                        ;;
    pkglist)            echo "$pkgname contents:"
                        dpkg-deb -c "$file"
                        ;;
    detail)             output "subheader" "Package: $pkgname"
                        output "normal" ""
                        if [ -n "${encryptionuse[$pkgname]}" ] && [ "${encryptions[$pkgname]}" != "None" ]; then
                          output "normal" "Encryption: ${encryptionuse[$pkgname]}"
                          output "normal" ""
                        fi
                        output "normal" "Potential encryption used: $encryption"
                        output "normal" ""
                        output "normal" "Description:"
                        output "quote" "$description"
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
  output "normal" "License text:"
  output "quote" "$(cat /usr/share/common-licenses/$license)"
  output "normal" ""
done

output "header" "Encryption tools"
output "subheader" "OpenSSL"
output "normal" "Description:"
output "quote" "OpenSSL is a cryptography toolkit implementing the Secure Sockets Layer
(SSL v2/v3) and Transport Layer Security (TLS v1) network protocols and
related cryptography standards required by them."
output "normal" "List of available algorithms:"
output "quote" " * Ciphers: AES, Blowfish, Camellia, SEED, CAST-128, DES, IDEA, RC2,
RC4, RC5, Triple DES, GOST 28147-89
 * Cryptographic hash functions: MD5, MD4, MD2, SHA-1, SHA-2, RIPEMD-160,
MDC-2, GOST R 34.11-94
 * Public-key cryptography: RSA, DSA, Diffie–Hellman key exchange,
Elliptic curve, GOST R 34.10-2001"
output "subheader" "libgcrypt"
output "normal" "Description"
output "quote" "Libgcrypt is a general purpose cryptographic library based on the code
from GnuPG. It provides functions for all cryptograhic building blocks"
output "normal" "List of available algorithms:"
output "quote" " * Symmetric ciphers: AES, DES, Blowfish, CAST5, Twofish, SEED,
Camellia, Arcfour
 * Hash algorithms: MD4, MD5, RIPE-MD160, SHA-1, SHA_224, SHA-256,
SHA-384, SHA-512, TIGER-192, Whirlpool
 * Public-key algorithms: RSA, Elgamal, DSA, ECDSA"
output "subheader" "python-crypto"
output "normal" "Description:"
output "quote" "A collection of cryptographic algorithms and protocols, implemented
for use from Python."
output "normal" "List of available algorithms:"
output "quote" " * Hash functions: HMAC, MD2, MD4, MD5, RIPEMD160, SHA, SHA256.
 * Block encryption algorithms: AES, ARC2, Blowfish, CAST, DES, Triple-DES.
 * Stream encryption algorithms: ARC4, simple XOR.
 * Public-key algorithms: RSA, DSA, ElGamal.
 * Protocols: All-or-nothing transforms, chaffing/winnowing.
 * Miscellaneous: RFC1751 module for converting 128-bit keys
   into a set of English words, primality testing, random number generation."
output "subheader" "libhcrypto"
output "normal" "Description:"
output "quote" "Libhcrypto is a cryptograhic library used in Heimdal -
a free implementation of Kerberos 5 that aims to be compatible with
MIT Kerberos."
output "normal" "List of available algorithms:"
output "quote" "DES cbc mode with CRC-32DES cbc mode with RSA-MD4
DES cbc mode with RSA-MD5
DES cbc mode raw
Triple DES cbc mode raw
Triple DES cbc mode with HMAC/sha1
DES with HMAC/sha1
CTS mode with 96-bit SHA-1 HMAC
CTS mode with 96-bit SHA-1 HMAC
RC4 with HMAC/MD5
Exportable RC4 with HMAC/MD5
Camellia-256 CTS mode with CMAC
Camellia-128 CTS mode with CMAC
DES family: des-cbc-crc, des-cbc-md5, and des-cbc-md4
Triple DES family: des3-cbc-sha1
The AES family: aes256-cts-hmac-sha1-96 and aes128-cts-hmac-sha1-96
The RC4 family: arcfour-hmac
The Camellia family: camellia256-cts-cmac and camellia128-cts-cmac"
