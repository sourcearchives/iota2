#!/bin/bash
# =========================================
# Project : iota2 Land cover treatment chain
# iota2 generation script
# =========================================

function erreur {
  echo "Usage : $0 [--update --compil --all] [module]"
  echo "--update : download of source files only"
  echo "--compil : compilation only"
  echo "--all : download + compilation"
  echo "module : OTB iota2"
  exit
}

function confirm {
  read -r -p "${1} Are you sure you want to continue? [y/N] " response
  if [[ $response == "y" || $response = "Y" ]]; then
    echo -e "${RED}\e[1mLauching generation in $prefix_dir\e[0m"
    ok=1
  else
    exit
  fi
}

set -e
#Couleur rouge
RED='\033[0;31m'

# On prend comme répertoire de référence le répertoire où se trouve le script.
prefix_dir=$PWD
ok=0

# Error test
if [[ "$#" != "1" ]] && [[ "$#" != "2" ]]; then
  erreur
fi
if [[ "$1" != "--update" ]] && [[ "$1" != "--compil" ]] && [[ "$1" != "--all" ]]; then
  erreur
fi
if [[ "$#" == "2" ]]; then
  if [[ "$2" != "OTB" ]] && [[ "$2" != "iota2" ]]; then
    erreur
  fi
fi

echo "iota2 will be installed and compiled in ${prefix_dir}"
confirm  

if [[ "$ok" == "1" ]]; then
  #----------------------------------------
  # Getting source file
  if [[ "$1" == "--update" ]] || [[ "$1" == "--all" ]]; then
    if [[ "$#" == 1 ]] || [[ "$2" == "OTB" ]]; then
      # Getting OTB source files
      echo "Cloning OTB ..."
      mkdir $prefix_dir/OTB
      cd $prefix_dir/OTB
      git clone https://git@git.orfeo-toolbox.org/git/otb.git

      echo "Getting Superbuild archives ..."
      cd $prefix_dir/OTB
      mkdir SuperBuild-archives
      cd SuperBuild-archives
      wget https://www.orfeo-toolbox.org/packages/SuperBuild-archives-6.0.tar.bz2
      tar -xvjf SuperBuild-archives-6.0.tar.bz2
    fi
    if [[ "$#" == 1 ]] || [[ "$2" == "iota2" ]]; then
      # Getting GapFilling source files
      echo "Adding OTBGapFilling module ..."
      mkdir $prefix_dir/CESBIO
      cd $prefix_dir/CESBIO
      git clone http://tully.ups-tlse.fr/jordi/temporalgapfilling.git
      cd $prefix_dir/OTB/otb/Modules/Remote/
      ln -s ../../../../CESBIO/temporalgapfilling OTBTemporalGapFilling                                                                                   
      # Add iota2 module                                          
      echo "Adding iota2 module ..."                              
      cd $prefix_dir/CESBIO
      #git clone http://tully.ups-tlse.fr/jordi/iota2.git
      git clone https://ArthurV@framagit.org/ArthurV/iota2.git
      cd $prefix_dir/OTB/otb/Modules/Remote/
      ln -s ../../../../CESBIO/iota2 
    fi
  fi
  #----------------------------------------
  # Building
  if [[ "$1" == "--compil" ]] || [[ "$1" == "--all" ]]; then  
    if [[ "$#" == 1 ]] || [[ "$2" == "OTB" ]]; then
      # Building OTB
      echo "Building OTB ..."
      cd $prefix_dir/OTB
      mkdir -p build
      cd build

      cmake -DCMAKE_CXX_FLAGS:STRING=-std=c++11 -DUSE_SYSTEM_BOOST=ON -DBUILD_TESTING=OFF -DCMAKE_BUILD_TYPE=Release -DOTB_WRAP_PYTHON:BOOL=ON -DGDAL_SB_EXTRA_OPTIONS:STRING="--with-python" -DCMAKE_INSTALL_PREFIX=$prefix_dir/OTB/install/ -DDOWNLOAD_LOCATION=$prefix_dir/OTB/SuperBuild-archives/ -DModule_IOTA2:BOOL=ON -DOTB_USE_QWT=ON -DOTB_USE_GLEW=ON -DOTB_USE_GLUT=ON -DOTB_USE_OPENGL=ON $prefix_dir/OTB/otb/SuperBuild/
      make -j2
    fi
    if [[ "$#" == 1 ]] || [[ "$2" == "iota2" ]]; then 
      # Building iota2
      echo "Building iota2 ..."
      cd $prefix_dir/OTB/build/OTB/build
      cmake -DCMAKE_CXX_FLAGS:STRING=-std=c++11 -DModule_IOTA2:BOOL=ON -DModule_IOTA2:BOOL=ON -DModule_OTBTemporalGapFilling:BOOL=ON $prefix_dir/OTB/otb 
      make -j2
      make install
    fi
  fi
  #----------------------------------------
  # Generation de l'archive
  #----------------------------------------
  echo "Generate Archive ..."
  cd $prefix_dir
  tar -czf iota2_OTB-6.0.tar.gz OTB/install CESBIO prepare_env* README*
  echo "--> Archive ${prefix_dir}/iota2_OTB-6.0.tar.gz available"
  echo "Generation process terminated"
fi
