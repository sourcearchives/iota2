#!/bin/bash

echo "Preparing to launch OSO Chain "
echo "Configuration file : "$1

#. launchChain.sh /home/user13/theia_oso/vincenta/THEIA_OSO/oso/oso/config/ConfigChain_20130205.cfg

module load python/2.7.5
module remove xerces/2.7
module load xerces/2.8

python launchChain.py -launch.config $1









