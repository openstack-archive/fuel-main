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
declare -A descriptions
declare -A encryptions
declare -A encryptionuse
declare -A licenses
declare -A copyrights
for file in "$@"; do
  if [ -f "$file" ] && [[ "$file" =~ rpm$ ]]; then
    pkgname=$(rpm -qp --queryformat="%{NAME}" "$file" 2>/dev/null)
    pkgorder+=("$pkgname")
    descriptions[$pkgname]=$(rpm -qp --queryformat='%{DESCRIPTION}' "$file" 2>/dev/null)
    licenses["$pkgname"]=$(rpm -qp --queryformat='%{LICENSE}' "$file" 2>/dev/null)
    licensefile=$(rpm -qpd "$file" 2>/dev/null| egrep -i '(LICENSE$|COPYING$)')
    if [ -n "$licensefile" ]; then
      copyrights[$pkgname]="$(rpm2cpio "$file" 2>/dev/null| cpio -iv --to-stdout ".$licensefile" 2>/dev/null)"
    fi
    encryption=$(rpm -qpR "$file" 2> /dev/null|egrep -i "libssl|openssl|crypt")
    if [ -z "$encryption" ]; then
      encryptions[$pkgname]="None"
    else
      case "$encryption" in
        *erlang*)          encryptions[$pkgname]="openSSL"
                           ;;
        *m2crypto*)        encryptions[$pkgname]="openSSL"
                           ;;
        *pyOpenSSL*)       encryptions[$pkgname]="openSSL"
                           ;;
        *openssl*)         encryptions[$pkgname]="openSSL"
                           ;;
        *libssl*)          encryptions[$pkgname]="openSSL"
                           ;;
        *libcrypto.so*)    encryptions[$pkgname]="openSSL"
                           ;;
        *JSEncrypt*)       encryptions[$pkgname]="openSSL"
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
        *libcrypt.so*)     encryptions[$pkgname]="None"
                           ;;
        *)                 encryptions[$pkgname]="unknown"
                           ;;
      esac
    fi
  else
    echo "Skipping non-RPM file $file" 1>&2
  fi
done

output "normal" ".. contents:: Table of Contents"
output "normal" ""
#output "header" "List of packages"
#output "list" "$(printf -- '%s\n' "${pkgorder[@]}" | tr ' ' '\n')"

encryptionuse["sslserver"]="Uses parts of openSSL to listen for secure SSLv2/SSLv3 connections"
encryptionuse["sslclient"]="Uses parts of openSSL to connect to secure SSL hosts"
encryptionuse["sshserver"]="Uses parts of openSSL to listen for secure shell connections"
encryptionuse["sshclient"]="Uses parts of openSSL to connect to ssh hosts"
encryptionuse["ssldebug"]="Uses parts of openSSL to debug SSL connections"

for pkgname in "${pkgorder[@]}"; do
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
  output "subheader" "Package: $pkgname"
  output "normal" "Description:"
  output "quote" "${descriptions[$pkgname]}"
  if [ -n "${encryptionuse[$pkgname]}" ] && [ "${encryptions[$pkgname]}" != "None" ]; then
    output "normal" "Encryption: ${encryptionuse[$pkgname]}"
  fi
  output "normal" "Potential encryption used: ${encryptions[$pkgname]}"
  output "normal" ""
  output "normal" "License: ${licenses[$pkgname]}"
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
output "normal" "List of algorithms available:"
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
