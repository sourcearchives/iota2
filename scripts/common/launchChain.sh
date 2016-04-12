#!/bin/bash

echo "Preparing to launch OSO Chain "
echo "Configuration file : "$1

#. launchChain.sh /home/user13/theia_oso/vincenta/THEIA_OSO/oso/oso/config/ConfigChain_20130205.cfg

j=0
old_IFS=$IFS
IFS=$\'%s\'
for ligne in $(cat /etc/issue)
do
	cmd[$j]=$ligne
	j=$j+1
done
IFS=$old_IFS

if [[ $cmd{[0]} == *Red* ]]
then
	echo "Server detected : parallel chain will be launched"
	module load python/2.7.5
	module remove xerces/2.7
	module load xerces/2.8
else
	echo $cmd
	echo "Local mode sequential chain will be launched"
fi

python launchChain.py -launch.config $1









