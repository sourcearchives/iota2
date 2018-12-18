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

import os, sys, argparse
import traceback
import datetime
import dill
from mpi4py import MPI
import csv
from itertools import groupby
import ogr
import gdal
from VectorTools import vector_functions as vf
from skimage.measure import label
from skimage.measure import regionprops
import numpy as np
from Common import FileUtils as fut
import time
import vector_functions as vf

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


def mpi_schedule_job_array(csvstore, job_array, mpi_service=MPIService()):
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
                [slave_rank, [start, end, result]] = mpi_service.comm.recv(source=MPI.ANY_SOURCE, tag=0)
                results += result
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
            return results
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
                mpi_service.comm.send([mpi_service.rank, [start_date, end_date, result]], dest=0, tag=0)

    except:
        if mpi_service.rank == 0:
            print "Something went wrong, we should log errors."
            traceback.print_exc()
            kill_slaves(mpi_service)
            sys.exit(1)


def listClasses(shpfile, field):

    ds = vf.openToRead(shpfile)	
    layer = ds.GetLayer()
    classes = []
    for feature in layer:
        cl =  feature.GetField(field)
        if cl not in classes:
            classes.append(cl)

    classes.sort()

    return classes

def countByAtt(params):

    vector, classe, field = params
    
    ds = vf.openToRead(vector)
    layer = ds.GetLayer()    
    layerDfn = layer.GetLayerDefn()
    fields = vf.getFields(vector)
    fieldTypeCode = layerDfn.GetFieldDefn(fields.index(field)).GetType()    
        
    layer.ResetReading()
    totalarea = 0
    for feat in layer:
        geom = feat.GetGeometryRef()
        totalarea += geom.GetArea()

    stats = []        
    if fieldTypeCode == 4:
        layer.SetAttributeFilter(field+" = \'"+str(classe)+"\'")
        featureCount = layer.GetFeatureCount()
        area = 0
        for feat in layer:
                geom = feat.GetGeometryRef()
                area += geom.GetArea()
        partcl = area / totalarea * 100
        print "Class # %s: %s features and a total area of %s (rate : %s)"%(str(classe), \
                                                                            str(featureCount),\
                                                                            str(area), \
                                                                            str(round(partcl,4)))
        stats.append([classe, featureCount, area, partcl])
        layer.ResetReading()
    else:
        layer.SetAttributeFilter(field+" = "+str(classe))
        featureCount = layer.GetFeatureCount()
        area = 0
        for feat in layer:
                geom = feat.GetGeometryRef()
                area += geom.GetArea()
        partcl = area / totalarea * 100       
        print "Class # %s: %s features and a total area of %s (rate : %s)"%(str(classe), \
                                                                            str(featureCount),\
                                                                            str(area),\
                                                                            str(round(partcl,4)))           
        stats.append([classe, featureCount, area, partcl])
        layer.ResetReading()

    return stats


def master(vector, field, csvstore):

    listclasses = []

    mpi_service=MPIService()
    if mpi_service.rank == 0:
        listclasses = listClasses(vector, field)

    param_list = []
    print listclasses
    for classe in listclasses:
        param_list.append((vector, classe, field))

    ja = JobArray(lambda x: countByAtt(x), param_list)    
    results = mpi_schedule_job_array(csvstore, ja, mpi_service=MPIService())

    if mpi_service.rank == 0:
        with open(csvstore, 'a') as myfile:
            writer = csv.writer(myfile)
            writer.writerows(results)

            
if __name__ == "__main__":
    if len(sys.argv) == 1:
        PROG = os.path.basename(sys.argv[0])
        print '      '+sys.argv[0]+' [options]'
        print "     Help : ", PROG, " --help"
        print "        or : ", PROG, " -h"
        sys.exit(-1)
    else:
        USAGE = "usage: %prog [options] "
        PARSER = argparse.ArgumentParser(description="Extract shapefile records")
        PARSER.add_argument("-ins", dest="ins", action="store",\
                            help="input shapefile",\
                            required=True)
        PARSER.add_argument("-field", dest="field", action="store",\
                            help="input shapefile field to analyse",\
                            required=True)        
        PARSER.add_argument("-csv", dest="csv", action="store",\
                            help="csv file to store results", required=True)

        
        args = PARSER.parse_args()
        master(args.ins, args.field, args.csv)
