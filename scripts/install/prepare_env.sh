#!/bin/bash
# =========================================
# Project : iota2 Land cover treatment chain
# iota2 Environment variable setting
# =========================================

function test_dir 
  if [ ! -d "$1" ]; then
    echo "$1 doesn't exist. Check your installation."
  fi

# The directory where the script has been set as reference.
CMD="$(readlink -e "${BASH_SOURCE[0]}")"
SH_DIR="$(dirname "$CMD")"
export IOTA2DIR=$SH_DIR/../..
export prefix_dir=$SH_DIR/OTB/

#----------------------------------------
# Check if IOTA2DIR is define
if test -z "$IOTA2DIR"; then
  echo "Problem with IOTA2DIR environment variable."
else
  #----------------------------------------
  # General environment variables
  test_dir $IOTA2DIR
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
  export PYTHONPATH=$PYTHONPATH:$IOTA2DIR/scripts/common/
  export PYTHONPATH=$PYTHONPATH:$IOTA2DIR/data/test_scripts/
  export PYTHONPATH=$install_dir/lib/otb/python/:$install_dir/lib/python2.7/site-packages/:$PYTHONPATH
  export PYTHONPATH=$PYTHONPATH:/usr/lib64/python2.7/site-packages/openmpi
fi
