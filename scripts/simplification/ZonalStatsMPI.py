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

import vector_functions as vf
import csv
from itertools import groupby
import ogr
import gdal
from skimage.measure import label
from skimage.measure import regionprops
import numpy as np

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
                [slave_rank, [start, end, result]] = mpi_service.comm.recv(source=MPI.ANY_SOURCE, tag=0)
                results.append(result)
                print results
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

def selectTile(tiles, field, idmin, idmax, opath):

    shape = vf.openToRead(tiles)
    lyr = shape.GetLayer()
    lyr.SetAttributeFilter(field + ">=" + idmin + ' and ' + field + "<" + idmax)
    vf.CreateNewLayer(lyr, opath)

def getFidList(vect):
    
    shape = vf.openToRead(vect)
    lyr = shape.GetLayer()
    fidlist = []
    for feat in lyr:
        fidlist.append(feat.GetFID())
        
    fidlist = fidlist.sort()
    return fidlist
    
def zonalstats(params):

    #raster, vector, idfield, idval = params
    raster, vector, idval = params
    
    # get geom envelop of stoc
    #shp = ogr.Open(vector)
    #lyr = shp.GetLayer()
    #lyr.SetAttributeFilter(field + "==" + idval)
    #feat = layer.GetNextFeature()
    #geom = feat.GetGeometryRef()
    #env = geom.GetEnvelope()

    #tmpfile = 'rast_' + feat.GetField(idfield)
    tmpfile = 'rast_' + str(idval)
    
    # Check geometry before
    cmd = 'gdalwarp -cutline %s -crop_to_cutline -wo NUM_THREADS=5 -cwhere "FID=%s" %s %s'%(vector, idval, raster, tmpfile)

    '''
    # clip raster gdal_translate (ulx uly lrx lry) with geom envelop (minX, maxX, minY, maxY)
    cmd = "gdal_translate -quiet -projwin %s %s %s %s %s %s"%(env[0], \
                                                              env[3], \
                                                              env[1], \
                                                              env[2], \
                                                              raster, \
                                                              tmpfile)
    '''
    os.system(cmd)
    
    # analyze raster
    rastertmp = gdal.Open(tmpfile, 0)
    results_final = []
    for band in range(rastertmp.RasterCount):
        band += 1
        raster_band = rastertmp.GetRasterBand(band)
        data = raster_band.ReadAsArray()
    
        img = label(data)
        listlab = []
        for reg in regionprops(img, data):
            listlab.append([[x for x in np.unique(reg.intensity_image) if x != 0][0], reg.area])
            
        results = []    
        for i, g in groupby(sorted(listlab), key = lambda x: x[0]):
            #results.append([feat.GetField(idfield), i, sum(v[1] for v in g)])
            results.append([idval, band, i, sum(v[1] for v in g)])
        
        sumpix = sum([x[3] for x in results])
        results_final.append([[x, y, w, round((float(z)/float(sumpix))*100.0, 2)] for x, y, w, z in results])
    
        raster_band = data = img = None

    os.system("rm %s"%(tmpfile))
    
    rastertmp = None

    return results_final


#def master(raster, vector, idfield, valmin, valmax, csvstore):
def master():
    #opath = 'gridvcf_' + str(valmin) + '_' + str(valmax)
    #selectTile(vector, idfield, valmin, valmax, opath)

    vector = '/mnt/data/home/thierionv/workcluster/vincent/vectorisation/test_loiret_oso2016.shp'
    raster = '/mnt/data/home/thierionv/workcluster/vincent/vectorisation/stack_loiret.tif'
    csvstore = '/mnt/data/home/thierionv/workcluster/vincent/vectorisation/test.csv'
    #fidlist = getFidList(vector)
    
    param_list = []
    #for i in range(valmin, valmax, 1):
    for i in range(250):
        #param_list.append((raster, opath, idfield, i))
        param_list.append((raster, vector, i))
                          
    ja = JobArray(lambda x: zonalstats(x), param_list)
    results = mpi_schedule_job_array(ja, mpi_service=MPIService())

    with open(csvstore, 'a') as myfile:
        writer = csv.writer(myfile)
        writer.writerows(results)

master()
        
'''        
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
        PARSER.add_argument("-inr", dest="inr", action="store",\
                            help="input raster",\
                            required=True)
        PARSER.add_argument("-ins", dest="ins", action="store",\
                            help="input shapefile",\
                            required=True)
        #PARSER.add_argument("-field", dest="field", action="store",\
        #                    help="field for selection", required=True)
        #PARSER.add_argument("-valmin", dest="valmin", action="store",\
        #                    help="min val to select", required=True)
        #PARSER.add_argument("-valmax", dest="valmax", action="store",\
        #                    help="max val to select", required=True)
        PARSER.add_argument("-csv", dest="csv", action="store",\
                            help="csv file to store results", required=True)        
        
        args = PARSER.parse_args()
        #master(args.inr, args.ins, args.field, args.valmin, args.valmax, args.csv)
        master(args.inr, args.ins, args.csv)
'''
