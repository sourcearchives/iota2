#!/bin/bash
# =========================================
# Project : OSO Land cover treatment chain
# OSO Environment variable setting
# Dedicated script for CNES cluster hpc-5g
# and for jenkins platform
# =========================================

function test_dir 
  if [ ! -d "$1" ]; then
    echo "$1 doesn't exist. Check your installation."
  fi


#----------------------------------------
# Check if OSO_PATH is define
if test -z "$OSO_PATH"; then
  echo "Environment variable OSO_PATH doesn't exist. Please define it."
else
  echo "Cleanning environnement"
  module purge
  echo "Load OTB, python and gdal"
  export MODULEPATH="/work/OT/theia/oso/CAPGEMINI/INSTALL/OSO/modulefiles/":$MODULEPATH
  module load python
  module load pygdal/2.1.0-py2.7
  module load mpi4py/2.0.0-py2.7
  # TODO : check if there is a compatible version of mpi4py with openmpi 2.0.1
  module swap openmpi/1.10.3 openmpi/2.0.1
#  module load otb/develop
  module load cmake
  module load gcc/6.3.0
  module load sqlite/3.23.1
  module load libspatialite/4.3.0a
  module load pyspatialite/4.3.0a


  export CXX=`type g++ | awk '{print $3}'`
  export CMAKE_CXX_COMPILER=$CXX
  export CMAKE_C_COMPILER=$CC

  #----------------------------------------
  # General environment variables
  export IOTA2DIR=$OSO_PATH
  test_dir $IOTA2DIR

  #----------------------------------------
  # General environment variables
  test_dir $OTB_PATH
  install_dir=$OTB_PATH/scripts/install/OTB/install
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
fi


