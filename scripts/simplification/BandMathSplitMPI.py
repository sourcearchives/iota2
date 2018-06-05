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

"""
Apply a bandmath expression on sub-rasters produced by ExtractAndSplit.py script

"""

import argparse, os, shutil, glob
import ExtractAndSplit as eas
import traceback
import datetime

try:
    import OtbAppBank
    import fileUtils as fu
except ImportError:
    raise ImportError('Iota2 not well configured / installed')

import dill
from mpi4py import MPI

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
            results = []
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
            print "All tasks sent"
            try:
                kill_slaves(mpi_service)
            except Exception as inst:
                print inst
            print "All tasks completed"
        else:
            # slave
            mpi_status = MPI.Status()
            while 1:
                # waiting sending works by master
                print 'Slave ' + str(mpi_service.rank) + ' is ready...'
                [task_job, task_param] = mpi_service.comm.recv(source=0, tag=MPI.ANY_TAG, status=mpi_status)
                if mpi_status.Get_tag() == 1:
                    print 'Closed rank ' + str(mpi_service.rank)
                    break
                start_date = datetime.datetime.now()
                result = task_job(task_param)
                end_date = datetime.datetime.now()
                print mpi_service.rank, task_param, "ended"
                mpi_service.comm.send([mpi_service.rank, [start_date, end_date]], dest=0, tag=0)

    except:
        if mpi_service.rank == 0:
            print "Something went wrong, we should log errors."
            traceback.print_exc()
            kill_slaves(mpi_service)
            sys.exit(1)
   

def imageFilter(params):

    splitsName, expressionFile, bandMathExe, splitsDirectory, shareDirectory, threads, pixType, nbStreamDiv = params

    filtsplitsName = os.path.join(os.environ['TMPDIR'], os.path.basename(splitsName)[:-4] + "_filtered.tif")
    if bandMathExe == 'otbcli_BandMath':
        exp = open(expressionFile, 'r').read()
        strexe = 'otbcli_BandMath -il %s -out %s %s -exp "%s"'%(splitsName, \
                                                                filtsplitsName, \
                                                                pixType, \
                                                                exp)
    else:
        strexe = '%s %s %s %s %s'%(bandMathExe, splitsName, expressionFile, filtsplitsName, nbStreamDiv)

    shutil.copy(splitsName, os.environ['TMPDIR'])
    os.system(strexe)
    shutil.copy(filtsplitsName, shareDirectory)
    
def bandMathSplit(rasterIn, rasterOut, expressionFile, workingDirectory, bandMathExe, shareDirectory, splits, nbStreamDiv, pixType = 'uint8'):

    '''
    splits = []
    mpi_service = MPIService()
    if mpi_service.rank == 0:
        subRasterName = "bandMathSplit"
        spx, spy = fu.getRasterResolution(rasterIn)
        outDirectory, OutName = os.path.split(rasterOut)
        threads = os.environ['ITK_GLOBAL_DEFAULT_NUMBER_OF_THREADS']
        splits = eas.extractAndSplit(rasterIn,\
                                     None,None,None,\
                                     shareDirectory,\
                                     subRasterName,\
                                     X,Y,\
                                     None, "entire", 'gdal', 'UInt32', threads)
    '''
        
    param_list = []
    threads = os.environ['ITK_GLOBAL_DEFAULT_NUMBER_OF_THREADS']
    for split in splits:
        param_list.append((split, expressionFile, bandMathExe, workingDirectory, shareDirectory, threads, pixType, nbStreamDiv))

    ja = JobArray(lambda x: imageFilter(x), param_list)
    mpi_schedule_job_array(ja, mpi_service=MPIService())
                              
    mpi_service = MPIService()
    if mpi_service.rank == 0:
        spx, spy = fu.getRasterResolution(rasterIn)
        outDirectory, OutName = os.path.split(rasterOut)
        bandMathOutput = fu.fileSearchRegEx(shareDirectory + "/*filtered.tif")
        fu.assembleTile_Merge(bandMathOutput, spx, os.path.join(workingDirectory, OutName), "UInt32")
    
        # check if raster is not alterate
        rasterInExtent = [int(val) for val in fu.getRasterExtent(rasterIn)]
        rasterOutExtent =  [int(val) for val in fu.getRasterExtent(os.path.join(workingDirectory, OutName))]
        if rasterInExtent != rasterOutExtent:
            raise Exception("Error during splitting bandMath")
    
        shutil.copy(os.path.join(workingDirectory, OutName), rasterOut)

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description = "split raster into sub-raster and apply to each bandMathExpression")
    parser.add_argument("-in",dest = "rasterIn",help ="path to the raster to split",default=None,required=True)
    parser.add_argument("-out",dest = "rasterOut",help ="output raster",default=None,required=True)
    parser.add_argument("-expression.file",dest = "expressionFile",help ="path to the file containing bandMath expression"\
                        ,default=None,required=True)
    parser.add_argument("-wd",dest = "workingDirectory",help ="working directory",default=None,required=True)
    #parser.add_argument("-X",dest = "X",help ="split number in X",default="5",required=False,type=int)
    #parser.add_argument("-Y",dest = "Y",help ="split number in Y",default="5",required=False,type=int)
    parser.add_argument("-bandMathExe",dest = "bandMathExe",help ="path to the bandMath exe",required=True)
    parser.add_argument("-nbStreamDiv",dest = "nbStreamDiv",help ="number of streams division",required=True)
    parser.add_argument("-share.Directory",dest = "shareDirectory",help ="path to a sharing directory (hpc mode)",required=False)
    parser.add_argument("-splits",dest = "splits", nargs="+", help ="list of splits files",required=True)
    
    args = parser.parse_args()
    bandMathSplit(args.rasterIn, args.rasterOut, args.expressionFile, args.workingDirectory, \
                  args.bandMathExe, args.shareDirectory, args.splits, args.nbStreamDiv)
