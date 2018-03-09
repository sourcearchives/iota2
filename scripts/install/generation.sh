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
OTB_VERSION='6.4'

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
      mkdir -p $prefix_dir/OTB
      cd $prefix_dir/OTB
      if [ -d "./otb" ]; then
        echo "otb repository already cloned. skipping."
      else
        git clone https://git@git.orfeo-toolbox.org/git/otb.git
      fi

      echo "Getting Superbuild archives ..."
      cd $prefix_dir/OTB
      mkdir -p SuperBuild-archives
      cd SuperBuild-archives
      if [ -f "./SuperBuild-archives-${OTB_VERSION}.tar.bz2" ]; then
        echo "SuperBuild archives already downloaded. skipping."
      else
        wget https://www.orfeo-toolbox.org/packages/SuperBuild-archives-${OTB_VERSION}.tar.bz2
      fi
      wget https://www.orfeo-toolbox.org/packages/SuperBuild-archives-${OTB_VERSION}.md5
      md5sum SuperBuild-archives-${OTB_VERSION}.tar.bz2 > verif_MD5
      nbDiff=`diff verif_MD5 SuperBuild-archives-${OTB_VERSION}.md5 | wc -l`
      if [[ "$nbDiff" == 0 ]]; then
        tar -xvjf SuperBuild-archives-${OTB_VERSION}.tar.bz2
      else
        echo "MD5sum is different for SuperBuild-archives-${OTB_VERSION}.tar.bz2 file !"
        echo "Maybe a problem during download ?"
        exit
      fi
    fi
    if [[ "$#" == 1 ]] || [[ "$2" == "iota2" ]]; then
      # Getting GapFilling source files
      echo "Adding OTBGapFilling module ..."
      mkdir -p $prefix_dir/CESBIO
      cd $prefix_dir/CESBIO
      if [ -d "./temporalgapfilling" ]; then
        echo "temporalgapfilling repository already cloned. skipping."
      else
        git clone http://tully.ups-tlse.fr/jordi/temporalgapfilling.git
      fi
      cd $prefix_dir/OTB/otb/Modules/Remote/
      ln -sf ../../../../CESBIO/temporalgapfilling OTBTemporalGapFilling                                                                                   
      # Add iota2 module                                          
      echo "Adding iota2 module ..."                              
      cd $prefix_dir/CESBIO
      if [ -d "./iota2" ]; then
        echo "iota2 repository already cloned. skipping."
      else
        #git clone http://tully.ups-tlse.fr/jordi/iota2.git
        git clone https://framagit.org/inglada/iota2.git
      fi
      cd $prefix_dir/OTB/otb/Modules/Remote/
      ln -sf ../../../../CESBIO/iota2 
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

#     cmake -DCMAKE_CXX_FLAGS:STRING=-std=c++11 -DUSE_SYSTEM_BOOST=ON -DBUILD_TESTING=OFF -DCMAKE_BUILD_TYPE=Release -DOTB_WRAP_PYTHON:BOOL=ON -DGDAL_SB_EXTRA_OPTIONS:STRING="--with-python" -DCMAKE_INSTALL_PREFIX=$prefix_dir/OTB/install/ -DDOWNLOAD_LOCATION=$prefix_dir/OTB/SuperBuild-archives/ -DModule_IOTA2:BOOL=ON -DOTB_USE_QWT=ON -DOTB_USE_GLEW=ON -DOTB_USE_GLUT=ON -DOTB_USE_OPENGL=ON $prefix_dir/OTB/otb/SuperBuild/
      cmake -DCMAKE_CXX_FLAGS:STRING=-std=c++1y -DUSE_SYSTEM_BOOST=ON -DBUILD_TESTING=OFF -DCMAKE_BUILD_TYPE=Release -DOTB_WRAP_PYTHON:BOOL=ON -DGDAL_SB_EXTRA_OPTIONS:STRING="--with-python" -DCMAKE_INSTALL_PREFIX=$prefix_dir/OTB/install/ -DDOWNLOAD_LOCATION=$prefix_dir/OTB/SuperBuild-archives/ -DModule_IOTA2:BOOL=ON -DOTB_USE_QWT=ON -DOTB_USE_GLEW=ON -DOTB_USE_GLUT=ON -DOTB_USE_OPENGL=ON $prefix_dir/OTB/otb/SuperBuild/
      make VERBOSE=1 -j2
    fi
    if [[ "$#" == 1 ]] || [[ "$2" == "iota2" ]]; then 
      # Building iota2
      echo "Building iota2 ..."
      cd $prefix_dir/OTB/build/OTB/build
      cmake -DCMAKE_CXX_FLAGS:STRING=-std=c++1y -DModule_IOTA2:BOOL=ON -DModule_IOTA2:BOOL=ON -DModule_OTBTemporalGapFilling:BOOL=ON $prefix_dir/OTB/otb 
      make -j2
      make install
    fi
  fi
  #----------------------------------------
  # Generation de l'archive
  #----------------------------------------
  echo "Generate Archive ..."
  cd $prefix_dir
  tar -czf iota2_OTB-${OTB_VERSION}.tar.gz OTB/install CESBIO prepare_env* README*
  echo "--> Archive ${prefix_dir}/iota2_OTB-${OTB_VERSION}.tar.gz available"
  echo "Generation process terminated"
fi
