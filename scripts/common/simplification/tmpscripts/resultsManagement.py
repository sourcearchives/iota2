#!/usr/bin/python
#-*- coding: utf-8 -*-

import subprocess
import sys
import argparse
import AddField
import checkvoisins
import vector_functions as vf
import numpy as np
from osgeo import ogr

# génération de jobs avec erreurs

def tileTreatmentStatus(shapefile, log, outpath):

    # get features number
    nbfeat = vf.getNbFeat(shapefile)
    jobs_init = range(0, nbfeat, 1)
    status = [''] * nbfeat

    listjobsinit = jobs_init
    #tabjobvide, listjobsinit = checkvoisins.findEmptyTile(jobs_init, log)
    #print tabjobvide, listjobsinit
    #sys.exit()
    tabjobvide = [0, 1, 10, 11, 15, 16, 17, 18, 19, 20, 30, 4, 5, 6, 7, 70, 8, 80, 81, 9, 90, 91, 95, 96, 99]
    #listjobsinit.pop(jobs_init.index(int(tabjobvide)))
    listjobsinit = [x for x in listjobsinit if x not in tabjobvide]
    taberreur = checkvoisins.findWalltime(log)

    for index in taberreur:
        status[index] = u'voisinage depassement de temps'

    tabresteexcute = [x for x in listjobsinit if x not in taberreur]
    for index in tabresteexcute:
        status[index] = u'voisinage en cours'

    tabjobsuccess, listjobsinit = checkvoisins.findSuccess(outpath, listjobsinit)
    for index in tabjobsuccess:
        status[index] = u'voisinage termine'        

    simplif = checkvoisins.findSimplifTile(outpath)
    for index in simplif:
        status[index] = u'simplification terminee'        
    
    # manage shapefile
    listfields = vf.getFields(shapefile)
    if 'statut' not in listfields:
        AddField.addField(shapefile, 'statut', '')

    source = ogr.Open(shapefile, 1)
    layer = source.GetLayer()

    i = 0
    for feature in layer:
        layer.SetFeature(feature)
        feature.SetField("statut", status[i])
        layer.SetFeature(feature)
        i += 1
        
    layer = feature = data_source = None
    
if __name__ == "__main__":
    if len(sys.argv) == 1:
	prog = os.path.basename(sys.argv[0])
	print '      '+sys.argv[0]+' [options]' 
	print "     Help : ", prog, " --help"
	print "        or : ", prog, " -h"
	sys.exit(-1)  

    else:
	usage = "usage: %prog [options] "
	parser = argparse.ArgumentParser(description = "Job generation for voisinage")
        parser.add_argument("-grille", dest="grille", action="store", \
                            help="grid shapefile file", required = True)
        parser.add_argument("-log", dest="log", action="store", \
                            help="generic log file", required = True)
        parser.add_argument("-out", dest="outpath", action="store", \
                            help="job outpath", required = True)  

        args = parser.parse_args()
    
        tileTreatmentStatus(args.grille, args.log, args.outpath)


