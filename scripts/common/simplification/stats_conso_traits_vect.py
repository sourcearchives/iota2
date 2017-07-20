#!/usr/bin/python
#-*- coding: utf-8 -*-

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

import subprocess
from operator import itemgetter
import time
import sys
import argparse


def stats(logpath):
        # logpath='/home/qt/thierionv/simplification/post-processing-oso/script_oso/prepareStats1.o487497'
        command = 'grep -r ' + logpath + '.* -e "vmem"'
        result_success = subprocess.check_output(command, shell=True)
        tabjobsuccess = []
        tabresultsuccess = result_success.rstrip().split('\n')
        for line in tabresultsuccess:
	        walltime = line.split(',')[5]
                memory = line.split(',')[4]
                cpuused = line.split(',')[0].split(':')[2].split('=')[1]
                cpuasked = line.split(',')[2]
                
	        try:
		        tabjobsuccess.append(int(resfinalsuccess))
		        listjobsinit.pop(jobs_init.index(int(resfinalsuccess)))
	        except:
		        pass		

        return tabjobsuccess, listjobsinit
