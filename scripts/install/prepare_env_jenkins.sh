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
  module load python
  module load pygdal/2.1.0-py2.7
  module load openmpi/2.0.1
  module load mpi4py/2.0.0-py2.7
  # TODO : check if there is a compatible version of mpi4py with openmpi 2.0.1
  module swap openmpi/1.10.3 openmpi/2.0.1
  module load otb/develop
  module load cmake

  #----------------------------------------
  # General environment variables
  export IOTA2DIR=$OSO_PATH
  test_dir $IOTA2DIR

  export LD_LIBRARY_PATH=$IOTA2DIR/install/lib:$LD_LIBRARY_PATH

  #----------------------------------------
  # PYTHONPATH environment variable
  export PYTHONPATH=$PYTHONPATH:$IOTA2DIR/data/test_scripts/
  export PYTHONPATH=$PYTHONPATH:$IOTA2DIR/scripts/common/
fi
