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

import traceback
import datetime
import dill
import os
from mpi4py import MPI
import argparse
import time
import pickle
import datetime
import sys

def launchBashCmd(bashCmd):
    """
    usage : function use to launch bashCmd
    """
    #using subprocess will be better.
    os.system(bashCmd)

class Tasks():
    """
    Class tasks definition : this class launch MPI process
    """
    def __init__(self, tasks, ressources, iota2_config, MPI_service=None,
                 prev_job_id=None):
        """
        :param tasks [tuple] first element must be lambda function
                             second element is a list of parameters
        :param ressources [Ressources Object]
        """
        self.jobs = tasks[0]
        self.parameters = tasks[1]
        self.TaskName = ressources.name
        
        self.ressources = ressources
        self.nb_cpu = ressources.nb_cpu
