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

# This is needed in order to be able to send pyhton objects throug MPI send
MPI.pickle.dumps = dill.dumps
MPI.pickle.loads = dill.loads


class MPIService():
    """
    Class for storing the MPI context
    """
    def __init__(self):
        self.comm = MPI.COMM_WORLD
        self.rank = self.comm.Get_rank()
        self.size = self.comm.Get_size()


class JobArray():
    """
    Class for storing a function to be applied to an array of parameters.
    - job is a callable object like a lambda expression; it takes a single parameter
    - param_array is a list of the parameters for each call to job
    """
    def __init__(self, job, param_array):
        self.job = job
        self.param_array = param_array


def kill_slaves(mpi_service):
    """
    kill slaves
    :param mpi_service
    """
    for i in range(1, mpi_service.size):
        print "Kill signal to slave " + str(i), "debug"
        mpi_service.comm.send(None, dest=i, tag=1)


def mpi_schedule_job_array(job_array, mpi_service=MPIService()):
    """
    A simple MPI scheduler to execute jobs in parallel.
    """
    param_array = job_array.param_array
    job = job_array.job
    try:
        if mpi_service.rank == 0:
            # master
            nb_completed_tasks = 0
            nb_tasks = len(param_array)
            for i in range(1, mpi_service.size):
                if len(param_array) > 0:
                    task_param = param_array.pop(0)
                    mpi_service.comm.send([job, task_param], dest=i, tag=0)
            while nb_completed_tasks < nb_tasks:
                [slave_rank, [start, end]] = mpi_service.comm.recv(source=MPI.ANY_SOURCE, tag=0)
                nb_completed_tasks += 1
                if len(param_array) > 0:
                    task_param = param_array.pop(0)
                    mpi_service.comm.send([job, task_param], dest=slave_rank, tag=0)

            kill_slaves(mpi_service)

        else:
            # slave
            mpi_status = MPI.Status()
            while 1:
                # waiting sending works by master
                [task_job, task_param] = mpi_service.comm.recv(source=0, tag=MPI.ANY_TAG, status=mpi_status)
                if mpi_status.Get_tag() == 1:
                    print 'Closed rank ' + str(mpi_service.rank)
                    break
                start_date = datetime.datetime.now()
                task_job(task_param)
                end_date = datetime.datetime.now()
                print "************* SLAVE REPORT *************"
                print "slave : " + str(mpi_service.rank)
                print "parameter : " + str(task_param) + " ended"
                print "****************************************"
                mpi_service.comm.send([mpi_service.rank, [start_date, end_date]], dest=0, tag=0)

    except:
        if mpi_service.rank == 0:
            print "Something went wrong, we should log errors."
            traceback.print_exc()
            kill_slaves(mpi_service)
            sys.exit(1)
            
def computeMPIRequest(nb_mpi_procs, nb_cpu, nbSocket=2, nbSocketThreads=12):
    nbProcessBySocket = nbSocketThreads
    nbThreadsByProcess = int(nb_cpu)/int(nb_mpi_procs)
    
    return nbProcessBySocket, nbThreadsByProcess

def launchBashCmd(bashCmd):
    """
    usage : function use to launch bashCmd
    """
    os.system(bashCmd)#using subprocess will be better.

def launch_common_task(task_function):
    task_function()

class Task():
    """
    Class tasks definition : this class does not launch MPI process
    """
    def __init__(self, task, nb_procs, iota2_config, pbs_config,
                 prev_job_id=None):
        """
        :param task [function] must be lambda function
        :param nb_mpi_procs [integer] number of cpu to use 
        :param nb_mpi_procs [integer] number of MPI process 
        :param enablePBS [bool] enable PBS launcher or not
        :param iota2_config [string] 
        :param pbs_config  [function] function to determine ressources request
                                      in PBS mode
        :param prev_job_id  [string] previous job id, doesn't use but maybe in the futur
        """
        if not callable(task):
            raise Exception("task not callable")
        self.task = task
        self.nb_procs = nb_procs
        self.iota2_config = iota2_config
        exeMode = self.iota2_config.getParam("chain","executionMode")
        outputPath = self.iota2_config.getParam("chain","outputPath")
        self.logPath = None
        self.pickleDirectory = outputPath+"/TasksObj"
        if not os.path.exists(self.pickleDirectory):
            os.mkdir(self.pickleDirectory)
            
        self.pickleObj = os.path.join(self.pickleDirectory, pbs_config.__name__ + ".task")
        
        os.environ["ITK_GLOBAL_DEFAULT_NUMBER_OF_THREADS"] = str(nb_procs)
        os.environ["OMP_NUM_THREADS"] = str(nb_procs)
        
        self.enable_PBS = False
        #if exeMode == 'parallel':
        if 1 == 1:
            self.enable_PBS = True
            self.logPath = self.iota2_config.getParam("chain","logPath")
            self.pbs_config = pbs_config(self.nb_procs, self.logPath)

        self.current_job_id = None
        self.previous_job_id = prev_job_id

    def run(self):
        """
        launch tasks
        """
        import subprocess
        import pickle
        
        if os.path.exists(self.pickleObj):
            os.remove(self.pickleObj)
        pickle.dump(self.task, open(self.pickleObj, 'wb'))
        
        dir_path = os.path.dirname(os.path.realpath(__file__))
        if not self.enable_PBS:
            cmd = "python "+dir_path+"/launch_tasks.py -mode common -task " + self.pickleObj
        #else:
        if 1==1:
            if not self.previous_job_id:
                depend = " -W block=true "
            else:
                depend = "-W depend=afterok:" + self.previous_job_id
            cmd = "qsub "+ depend +" " + self.pbs_config + "-V -- /usr/bin/bash -c \
                  \"python "+dir_path+"/launch_tasks.py -mode common -task "+ self.pickleObj +"\""
        #print cmd
        mpi = subprocess.Popen(cmd, shell=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
        mpi.wait()
        stdout, stderr = mpi.communicate()
        if self.enable_PBS:
            self.current_job_id = stdout.rstrip()


class MPI_Tasks():
    """
    Class tasks definition : this class launch MPI process
    """
    def __init__(self, tasks, nb_procs, nb_mpi_procs, iota2_config, pbs_config,
                 prev_job_id=None):
        """
        :param tasks [tuple] first element must be lambda function
                             second element is a list of variable parameter
        :param nb_mpi_procs [integer] number of cpu to use 
        :param nb_mpi_procs [integer] number of MPI process 
        :param enablePBS [bool] enable PBS launcher or not
        :param iota2_config [string] 
        :param pbs_config  [function] function to determine ressources request
                                      in PBS mode
        :param prev_job_id  [string] previous job id, doesn't use but maybe in the futur
        """

        if not callable(tasks[0]):
            raise Exception("task not callable")
        if not callable(pbs_config):
            raise Exception("'pbs_config' parameter must be a function")
        self.jobs = JobArray(tasks[0],tasks[1])
        self.nb_procs = nb_procs
        self.nb_mpi_procs = nb_mpi_procs
        self.iota2_config = iota2_config
        exeMode = self.iota2_config.getParam("chain","executionMode")
        outputPath = self.iota2_config.getParam("chain","outputPath")
        self.logPath = None
        self.pickleDirectory = outputPath+"/TasksObj"
        if not os.path.exists(self.pickleDirectory):
            os.mkdir(self.pickleDirectory)
            
        self.pickleObj = os.path.join(self.pickleDirectory, pbs_config.__name__ + ".task")
        
        os.environ["ITK_GLOBAL_DEFAULT_NUMBER_OF_THREADS"] = str(nb_procs)
        os.environ["OMP_NUM_THREADS"] = str(nb_procs)
        
        self.enable_PBS = False
        #if exeMode == 'parallel':
        if 1 == 1:
            self.enable_PBS = True
            self.logPath = self.iota2_config.getParam("chain","logPath")
            self.pbs_config = pbs_config(self.nb_procs, self.nb_mpi_procs, self.logPath)

        self.current_job_id = None
        self.previous_job_id = prev_job_id

    
    def run(self):
        """
        launch tasks
        """
        import subprocess
        import pickle

        if os.path.exists(self.pickleObj):
            os.remove(self.pickleObj)
        pickle.dump(self.jobs, open(self.pickleObj, 'wb'))
        dir_path = os.path.dirname(os.path.realpath(__file__))
        if not self.enable_PBS:
            cmd = "mpirun -np " + str(self.nb_mpi_procs) + " python "+dir_path+"/launch_tasks.py -task " + self.pickleObj
        
        #else:
        if 1==1:
            nbProcessBySocket, nbThreadsByProcess = computeMPIRequest(self.nb_mpi_procs,
                                                                      self.nb_procs)
            if not self.previous_job_id:
                depend = " -W block=true"
            else:
                depend = "-W depend=afterok:" + self.previous_job_id
            cmd = "qsub "+ depend +" " + self.pbs_config + "-V -- /usr/bin/bash -c \
                  \"mpirun --report-bindings -np "+ str(self.nb_mpi_procs) +"\
                   --map-by ppr:"+str(nbProcessBySocket)+":socket:pe="+str(nbThreadsByProcess)+"\
                    python "+dir_path+"/launch_tasks.py -task "+ self.pickleObj +"\""
        #print cmd
        mpi = subprocess.Popen(cmd, shell=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
        mpi.wait()
        stdout, stderr = mpi.communicate()
        if self.enable_PBS:
            self.current_job_id = stdout.rstrip()
    def get_current_Job_id(self):
        return self.current_job_id
    def set_previous_Job_id(self,ID):
        self.previous_job_id = ID

if __name__ == "__main__":
    
    parser = argparse.ArgumentParser(description="This script launch tasks")
    parser.add_argument("-mode", help ="launch MPI tasks or common tasks",
                        dest="mode", required=False, default="MPI", choices=["MPI","common"])
    parser.add_argument("-task", help ="task to launch",
                        dest="task", required=True)
    args = parser.parse_args()
    
    import pickle
    import sys
    import os
    parentDir = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                os.pardir))
    sys.path.append(parentDir)

    with open(args.task, 'rb') as f:
        pickleObj = pickle.load(f)

    if args.mode == "MPI":
        mpi_schedule_job_array(pickleObj, mpi_service=MPIService())
    elif args.mode == "common":
        launch_common_task(pickleObj)


