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

#. launchChain.sh /home/user13/theia_oso/vincenta/THEIA_OSO/oso/oso/config/ConfigChain_20130205.cfg

parallel_execution=$(grep executionMode $1 |grep \'parallel\')
if [[ $parallel_execution == "" ]]
then
    echo "Local mode sequential chain will be launched"
else
    echo "Server detected : parallel chain will be launched"
    module load python/2.7.5
    module remove xerces/2.7
    module load xerces/2.8
fi
python launchChain.py -launch.config $1









