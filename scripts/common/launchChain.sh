#!/bin/bash
# =========================================================================
#   Program:   iota2
#
#   Copyright (c) CESBIO. All rights reserved.
#
#   See LICENSE for details.
#
#   This software is distributed WITHOUT ANY WARRANTY; without even
#   the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR
#   PURPOSE.  See the above copyright notices for more information.
#
# =========================================================================

# Function erreur : return how to use the script
function erreur {
  echo "Usage : $0 configuration_file"
  exit
}

# Configuration file test
if [[ "$#" != "1" ]]; then
  erreur
fi
# Configuration file exist ?
if [ ! -f $1 ]; then
  echo "Error: $1 doesn't exist !"
  exit
fi

echo "Preparing to launch OSO Chain "
echo "Configuration file : "$1

# Define directory
CMD="$(readlink -e "$0")"
SH_DIR="$(dirname "$CMD")"
CFG_DIR="$(readlink -f "$1")"

# we go to iota2/script/common directory
cd $SH_DIR

parallel_execution=$(grep executionMode $CFG_DIR |grep \'parallel\')
if [[ $parallel_execution == "" ]]
then
    echo "Local mode sequential chain will be launched"
    export ITK_GLOBAL_DEFAULT_NUMBER_OF_THREADS=2
    OTB_HOME=$(grep --only-matching --perl-regex "^((?!#).)*(?<=OTB_HOME\:).*" $CFG_DIR | cut -d "'" -f 2)
    . $OTB_HOME/config_otb.sh
    python launchChain.py -launch.config $CFG_DIR
else
    echo "Server detected : parallel chain will be launched"
    module load python/2.7.12
    module load pygdal/2.1.0-py2.7
    module load mpi4py/2.0.0-py2.7
    OTB_HOME=$(grep --only-matching --perl-regex "^((?!#).)*(?<=OTB_HOME\:).*" $CFG_DIR | cut -d "'" -f 2)
    outputPath=$(grep --only-matching --perl-regex "^((?!#).)*(?<=outputPath\:).*" $CFG_DIR | cut -d "'" -f 2)
    . $OTB_HOME/config_otb.sh
    echo "OTB : "$OTB_HOME/config_otb.sh
	python launchChain.py -launch.config $CFG_DIR
fi

# Come back
cd -
