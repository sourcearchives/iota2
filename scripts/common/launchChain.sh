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

echo "Preparing to launch OSO Chain "
echo "Configuration file : "$1

parallel_execution=$(grep executionMode $1 |grep \'parallel\')
if [[ $parallel_execution == "" ]]
then
    echo "Local mode sequential chain will be launched"

    export ITK_AUTOLOAD_PATH=""
    export OTB_HOME=$(grep --only-matching --perl-regex "(?<=OTB_HOME\:).*" $1 | cut -d "'" -f 2) 
    export PATH=${OTB_HOME}/bin:$PATH
    export LD_LIBRARY_PATH=${OTB_HOME}/lib:${OTB_HOME}/lib/otb/python:${LD_LIBRARY_PATH}
    export PYTHONPATH=${OTB_HOME}/lib/otb/python:${PYTHONPATH}
    export GDAL_DATA=${OTB_HOME}/share/gdal
    export GEOTIFF_CSV=${OTB_HOME}/share/epsg_csv

else
    echo "Server detected : parallel chain will be launched"
    module load python/2.7.5
    module remove xerces/2.7
    module load xerces/2.8
fi
python launchChain.py -launch.config $1









