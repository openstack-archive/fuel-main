#!/bin/bash
#Written by Matthew Mosesohn <mmosesohn@mirantis.com>
#2015-02-09
#Usage: patch-from-repo.sh http://server/repo [env-id]

set -e

#Constants
dist="precise"
yumpaths=("/repodata/repomd.xml")
aptpaths=("/Packages" "/Packages.gz" "/dists/$dist/main/binary-amd64/Packages" "/dists/$dist/main/binary-amd64/Packages.gz")
repobasepath="$(dirname $(readlink /var/www/nailgun/centos))"
tempdownloaddir="$(mktemp -d /tmp/repo.XXXX)"
LOGFILE="/var/log/repomirror.log"
packages=""

function node_add_repo {
  node=$1
  repotype=$2
  repopath=$3
  masterip=$(grep ipaddress: /etc/fuel/astute.yaml | awk '{print $2}')
  repourl="http://${masterip}:8080/$(echo $repopath | cut -d'/' -f5-)"

  case $repotype in
    'apt')  node_apt_repo "$node" "$repourl"
            ;;
    'yum')  node_yum_repo "$node" "$repourl"
            ;;
    *)      echo "Invalid repo type $repotype."
            exit 1
  esac
}

function node_apt_repo {
  node=$1
  repourl=$2
  ssh $node "sed -e '\$adeb $repourl /' -i /etc/apt/sources.list"
}

function node_yum_repo {
  node=$1
  repourl=$2
  ssh $node "/usr/bin/yum-config-manager --add-repo $repourl --setopt=gpgcheck=0" > /dev/null
}

function add_repo {
  repourl=$1
  repotype=$2
  newreponame=$3

  case $repotype in
    'apt')  add_apt_repo "$repourl" "$newreponame"
            ;;
    'yum')  add_yum_repo "$repourl" "$newreponame"
            ;;
    *)      echo "Invalid repo type $repotype."
            exit 1
  esac
}


function get_repo_type {
  repourl=$1
  for yumpath in ${yumpaths[@]}; do
    if curl -f -L "${repourl}${yumpath}" &>/dev/null; then
      echo "yum"
      return
    fi
  done
  for aptpath in ${aptpaths[@]}; do
    if curl -f -L "${repourl}${aptpath}" &>/dev/null; then
      echo "apt"
      return
    fi
  done
  echo "Unrecognized!"
}

function add_apt_repo {
  repourl=$1
  newreponame=$2
  #method="curltoexisting"
  #method="pullviarsync"
  method="recursivewget"
  repodir="${repobasepath}/ubuntu/${newreponame}"
  ##This is easier with python urlparse!
  #proto=$(echo "$repourl" | cut -d':' -f1)
  #host=$(echo $repourl | cut -d'/' -f2)
  #reporoot=$(echo $repourl | cut -d'/' -f3-)

  #conf=$(mktemp /tmp/aptmirror.XXXX)
  #echo "set base_path $repodir" > $conf
  #echo "deb $repourl main" >> $conf
  #apt-mirror $conf
  #debmirror -a amd64 --no-source -h $host --method=$proto -r $reporoot &> $LOGFILE

  mkdir -p "$repodir"
  if [[ "$method" == "curltoexisting" ]]; then
    mkdir -p "$repodir/pool/main"
    packageslist=$(mktemp /tmp/Packages.XXXX)
    for aptpath in ${aptpaths[@]}; do
      if curl -f -L "${repourl}${aptpath}" > $packageslist; then
        break
      fi
    done
    debfiles=$(zgrep Filename: $packageslist | cut -d' ' -f2)
    for debpkg in $debfiles; do
      wget --no-parent --no-use-server-timestamps --no-verbose --directory-prefix \
        "$repodir/pool/main" "${repourl}/${debpkg}"
    done
    regenerate_ubuntu_repo.sh $repodir $dist
  elif [[ "$method" == "recursivewget" ]]; then
    wget -r -l2 --no-verbose --directory-prefix $tempdownloaddir \
      -nH --cut-dirs=2 $repourl
    while read debfile; do
      packages="$packages $(dpkg -f $debfile package)"
    done < <(find $tempdownloaddir -name *.deb)
    #Purge Release.gpg because we don't need it
    find $tempdownloaddir -name Release.gpg | xargs rm -f
    cp -R $tempdownloaddir/* $repodir
  fi
}

function add_yum_repo {
  repourl=$1
  newreponame=$2

  repodir="${repobasepath}/centos/${newreponame}"
  cat > /etc/yum.repos.d/$newreponame.repo << EOF
[$newreponame]
name=$newreponame
baseurl=$repourl
enabled=0
gpgcheck=0
EOF
  mkdir -p $repodir
  reposync -r $newreponame --newest-only -p $repodir -q -m \
    --download-metadata --norepopath
  out=$(createrepo --update -v -o $repodir $repodir)
  rm -f /etc/yum.repos.d/$newreponame.repo
  while read line; do
    if echo $line | grep -q reading; then
      rpmfile=$(echo $line | cut -d' ' -f4)
      packages="$packages $(rpm -qp --nosignature --queryformat \
        '%{name}' "${repodir}/${rpmfile}")"
    fi
  done < <(echo -e "$out")
}

function get_node_list {
  fuel --env "$1" node | awk '/ready/{print "node-"$1}'
}

#TODO(mattymo): validate repo is valid url, env is integer, newreponame is
#               a valid dirname
repo=$1
env=${2:-1}
newreponame=${3:-"fuel-custom"}

repotype=$(get_repo_type "$repo")

#sets repodir and packages
add_repo "$repo" "$repotype" "$newreponame"

nodelist=$(get_node_list $env)

#Prepare commands to run on nodes
if [[ $repotype == "yum" ]]; then
  updatecommand="yum clean expire-cache; yum update -y $packages -x ruby* --nogpgcheck;"
else
  updatecommand="apt-get update; apt-get upgrade -y $packages"
fi

exitcode=0
for node in $nodelist; do
  if [ "$newreponame" != "x86_64" ]; then
    node_add_repo $node $repotype $repodir
  fi
  ssh $node "bash -c '$updatecommand'"
  if [ $? -ne 0 ]; then
    echo "$node failed to update package(s): $packages"
    exitcode=1
  fi
done
exit $exitcode
