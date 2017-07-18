#!/bin/bash
# =========================================
# Project : iota2 Land cover treatment chain
# iota2 Environment variable setting
# Dedicated script for CNES cluster hpc-5g
# =========================================

function test_dir 
  if [ ! -d "$1" ]; then
    echo "$1 doesn't exist. Check your installation."
  fi


#----------------------------------------
# Check if iota2_PATH is define
if test -z "$iota2_PATH"; then
  echo "Environment variable iota2_PATH doesn't exist. Please define it."
else
  echo "Cleanning environnement"
  module purge
  echo "Load python and gdal"
  module load python
  module load pygdal/2.1.0-py2.7

  #----------------------------------------
  # General environment variables
  export IOTA2DIR=$iota2_PATH/CESBIO/iota2/
  test_dir $IOTA2DIR
  export prefix_dir=$iota2_PATH/OTB/
  test_dir $prefix_dir
  install_dir=$prefix_dir/install
  test_dir $install_dir

  #----------------------------------------
  # PATH and LD_LIBRARY_PATH environment variables
  export PATH=$install_dir/bin:$PATH
  export LD_LIBRARY_PATH=$install_dir/lib:$install_dir/lib/otb/python:$LD_LIBRARY_PATH

  #----------------------------------------
  # Specific environment variables
  export ITK_AUTOLOAD_PATH=""
  export OTB_APPLICATION_PATH=$install_dir/lib/otb/applications/
  export GDAL_DATA=$install_dir/share/gdal/
  export GEOTIFF_CSV=$install_dir/share/epsg_csv/

  #----------------------------------------
  # PYTHONPATH environment variable
  if test -z "$PYTHONPATH"; then
    export PYTHONPATH=$install_dir/lib64/python2.7/site-packages/
  else
    export PYTHONPATH=$PYTHONPATH:$install_dir/lib64/python2.7/site-packages/
  fi
  export PYTHONPATH=$PYTHONPATH:$IOTA2DIR/data/test_scripts/
  export PYTHONPATH=$install_dir/lib/otb/python/:$install_dir/lib/python2.7/site-packages/:$PYTHONPATH
fi
