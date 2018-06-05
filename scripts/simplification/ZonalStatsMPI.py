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
import vector_functions as vf
from skimage.measure import label
from skimage.measure import regionprops
import numpy as np
import fileUtils as fut
import time

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

def getFidList(vect):
    
    shape = vf.openToRead(vect)
    lyr = shape.GetLayer()
    fidlist = []
    for feat in lyr:
        fidlist.append(feat.GetFID())
        
    return fidlist

def getArea(shape, fid):
    shp = ogr.Open(shape)
    lyr = shp.GetLayer()
    lyr.SetAttributeFilter('FID = '+str(fid))
    for feat in lyr:
        geom = feat.GetGeometryRef()
        area = geom.GetArea()

    return area
        
def zonalstats(params):

    #raster, vector, idfield, idval = params
    path, raster, vector, idval = params
    
    # get geom envelop of stoc
    shp = ogr.Open(vector)
    lyr = shp.GetLayer()

    #tmpfile = 'rast_' + feat.GetField(idfield)
    tmpfile = os.path.join(path, 'rast_' + str(idval))

    # rast resolution
    '''
    spx, spy = fut.getRasterResolution(raster)
    tap = False
    if getArea(vector, idval) < 10000:
        start = time.time()
        cmd = 'timeout 10 gdalwarp -overwrite -cutline %s -crop_to_cutline -wo NUM_THREADS=5 -cwhere "FID=%s" %s %s'%(vector, idval, raster, tmpfile)
        os.system(cmd)
        if time.time() >= start + 10:
            cmd = 'gdalwarp -overwrite -tap -tr %s %s -cutline %s -crop_to_cutline -wo NUM_THREADS=5 -cwhere "FID=%s" %s %s'%(spx, spy, vector, idval, raster, tmpfile)
            os.system(cmd)
    else:
        cmd = 'gdalwarp -overwrite -cutline %s -crop_to_cutline -wo NUM_THREADS=5 -cwhere "FID=%s" %s %s'%(vector, idval, raster, tmpfile)
        os.system(cmd)

    '''
    cmd = '/home/qt/thierionv/sources/gdal224/bin/gdalwarp -overwrite -cutline %s -crop_to_cutline --config GDAL_CACHEMAX 9000 -wm 9000 -wo NUM_THREADS=ALL_CPUS -cwhere "FID=%s" %s %s'%(vector, idval, raster, tmpfile)
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


        if (np.shape(data)[1] == 1 or np.shape(data)[0] == 1):
            if np.shape(data)[1] == 1:
                if np.shape(data)[0]%2 != 0:
                    data = np.append(data, 0)
                    data = data.reshape(-1, 2)
                else:
                    data = data.reshape(-1, 2)    
            if np.shape(data)[0] == 1:
                if np.shape(data)[1]%2 != 0:
                    data = np.append(data, 0)
                    data = data.reshape(-1, 2)
                else:
                    data = data.reshape(-1, 2)

        if (np.shape(img)[1] == 1 or np.shape(img)[0] == 1):
            if np.shape(img)[1] == 1:
                if np.shape(img)[0]%2 != 0:
                    img = np.append(img, 0)
                    img = img.reshape(-1, 2)
                else:
                    img = img.reshape(-1, 2)                    
            if np.shape(img)[0] == 1:
                if np.shape(img)[1]%2 != 0:
                    img = np.append(img, 0)
                    img = img.reshape(-1, 2)
                else:
                    img = img.reshape(-1, 2)
        '''        
        if (np.shape(data)[1] == 1 or np.shape(data)[0]) == 1:
            print np.shape(data)[1]%2
            if np.shape(data)[1]%2 != 0:
                data = np.append(data, 0)
                print data.reshape(-1, 2)
                data = data.reshape(-1, 2)
        print data, img                 
        if (np.shape(img)[1] == 1 or np.shape(img)[0]) == 1:
            if np.shape(img)[1]%2 != 0:
                img = np.append(img, 0)
                img = img.reshape(-1, 2)
        '''
        if band == 1:
            for reg in regionprops(img, data):
                listlab.append([[x for x in np.unique(reg.intensity_image) if x != 0][0], reg.area])
                    
            classmaj = [y for y in listlab if y[1]== max([x[1] for x in listlab])][0][0]
            posclassmaj = np.where(data==classmaj)
            results = []

            for i, g in groupby(sorted(listlab), key = lambda x: x[0]):
                results.append([i, sum(v[1] for v in g)])

            sumpix = sum([x[1] for x in results])
            for elt in [[int(w), round((float(z)/float(sumpix))*100.0, 2)] for w, z in results]:
                results_final.append([idval, 'classif', 'part'] + elt)
                
        if band != 1:
            if band == 2:
                results_final.append([idval, 'confidence', 'mean', int(classmaj), round(np.mean(data[posclassmaj]), 2)])
                #results_final.append([idval, 'confidence', 'std', int(classmaj), round(np.std(data[posclassmaj]), 2)])
            elif band == 3:
                results_final.append([idval, 'validity', 'mean', int(classmaj), round(np.mean(data[posclassmaj]), 2)])
                results_final.append([idval, 'validity', 'std', int(classmaj), round(np.std(data[posclassmaj]), 2)])                
                #results_final.append([idval, 'validity', 'majority', int(classmaj), np.argmax(np.bincount(np.array(data[posclassmaj], dtype=int)))])                

        raster_band = data = img = None
        
        

    os.system("rm %s"%(tmpfile))
    
    rastertmp = None
    print results_final
    return results_final


def master(path, raster, vector, csvstore):
    
    listfid = []
    
    mpi_service=MPIService()
    if mpi_service.rank == 0:
        listfid = getFidList(vector)

    param_list = []
    for i in range(len(listfid)):
        param_list.append((path, raster, vector, listfid[i]))
        
    ja = JobArray(lambda x: zonalstats(x), param_list)    
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
        PARSER.add_argument("-wd", dest="path", action="store",\
                            help="working dir",\
                            required=True)
        PARSER.add_argument("-inr", dest="inr", action="store",\
                            help="input raster",\
                            required=True)
        PARSER.add_argument("-ins", dest="ins", action="store",\
                            help="input shapefile",\
                            required=True)
        PARSER.add_argument("-csv", dest="csv", action="store",\
                            help="csv file to store results", required=True)        
        
        args = PARSER.parse_args()
        master(args.path, args.inr, args.ins, args.csv)


# python devcourant/extractAndConcatRaster.py -ins /work/OT/theia/oso/vincent/vectorisation/loiret_oso2016.shp -inr /work/OT/theia/oso/production/2017/oso2017.tif /work/OT/theia/oso/production/2017/oso2017_confidence.tif /work/OT/theia/oso/production/2017/oso2017_validity.tif -out /work/OT/theia/oso/vincent/test.tif
# Attention vérifier les géométries du vecteur : python chaineIOTA/iota2/scripts/vector-tools/vector_functions.py -s $TMPDIR/zone2_oso2017.shp -v
# mpirun -np 100 python ZonalStatsMPI.py -inr $TMPDIR/concatoso_zone2.tif -ins $TMPDIR/zone2_oso2017.shp -csv statszone2
