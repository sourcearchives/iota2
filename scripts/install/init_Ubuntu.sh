#!/bin/bash
# =========================================
# Project : iota2 Land cover treatment chain
# iota2 dependencies install -yation
# Ubuntu
# =========================================

set -e


function confirm {
  read -r -p "${1} Are you sure you want to continue? [y/N] " response
  if [[ $response == "y" || $response = "Y" ]]; then
    echo -e "${RED}\e[1mLauching generation in $prefix_dir\e[0m"
    ok=1
  else
    exit
  fi
}

verif=`uname -a | grep -c -i ubuntu`

if [[ "$verif" != "1" ]]; then
  echo "Ubuntu was not detected, this script could not worked correctly."
  confirm
else
  ok=1
fi

if [[ "$ok" == "1" ]]; then
  LISTE="cmake git g++ python-dev zlib1g-dev freeglut3-dev libx11-dev libxext-dev libxi-dev libboost-all-dev swig gsl-bin libgsl0-dev python-pip python-numpy python-scipy python-matplotlib python-pandas"

  for i in $LISTE; do 
    echo $i;
    apt-get install -y $i
  done

  LISTE="argparse config datetime osr"

  for i in $LISTE; do 
    echo $i;
    pip install $i
  done
 
fi

echo "Dependencies installation process terminated."
