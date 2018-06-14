#!/bin/bash
# =========================================
# Project : iota2 Land cover treatment chain
# iota2 dependencies install -yation
# CentOS
# =========================================

set -e

if [ "$EUID" -ne 0 ]
  then echo "Please run as root"
  exit
fi

function confirm {
  read -r -p "${1} Are you sure you want to continue? [y/N] " response
  if [[ $response == "y" || $response = "Y" ]]; then
    echo -e "${RED}\e[1mLauching generation in $prefix_dir\e[0m"
    ok=1
  else
    exit
  fi
}

verif=`cat /etc/centos-release | wc -l`

if [[ "$verif" != "1" ]]; then
  echo "CentOS was not detected, this script could not worked correctly."
  confirm
else
  ok=1
fi

if [[ "$ok" == "1" ]]; then

  LISTE="cmake git gcc python-devel zlib-devel freeglut-devel libX11-devel libXext-devel libXi-devel boost-devel swig gsl gsl-devel python-pip numpy scipy python-matplotlib python-pandas patch libspatialite-devel libspatialite mpi4py-openmpi mpi4py-common libXrandr-devel libXinerama-devel libXcursor-devel"

  for i in $LISTE; do
    echo $i;
    yum install -y $i
  done

  LISTE="argparse config datetime osr pyspatialite dill"

  for i in $LISTE; do
    echo $i;
    pip install $i
  done

fi

echo "Dependencies installation process terminated."

