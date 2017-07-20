# -*- coding: utf-8 -*-
"""
Merge some shapefile simplified and clip them according to an another shape.

"""

import shutil
import sys
import os
import time
import argparse
import DeleteDuplicateGeometries
import MergeFiles
import OSO_functions as osof
import correct_vector

def mergeTileShapes(path, list_files_tiles, ndept, depts, out, grass):

    debut_export_zone = time.time()
    
    # Empty shapefile
    osof.create_shape(path + "/dept_%s/merge.shp"%(ndept), 2154)

    #merge les shapes   
    for file_tile in list_files_tiles:
        command = "ogr2ogr -update -addfields -skipfailures %s/merge.shp %s"%(path + "/dept_" + ndept, file_tile)
        os.system(command)

    #recupere la forme du departement
    if int(ndept) < 10:
        ndeptcond = '0' + str(ndept)
    else:
        ndeptcond = str(ndept)
        
    command = "ogr2ogr -sql \"SELECT * FROM %s WHERE CODE_DEPT = \'%s\'\" %s %s"%(os.path.basename(depts).split(".")[0], \
                                                                                  ndeptcond, \
                                                                                  path + "/dept_"+ndept+"/dept_" + ndept + ".shp", \
                                                                                  depts)
    os.system(command)
        
    #clip selon la forme du departement
    command = "ogr2ogr -select value -clipsrc %s %s %s/merge.shp"%(path + "/dept_" + ndept + "/dept_" + ndept + ".shp", \
                                                                   path + "/dept_" + ndept + "/departement_" + ndept + ".shp", \
                                                                   path + "/dept_" + ndept)
    os.system(command)

    #va supprimer l'ensemble des geometries dupliquee
    outshape = DeleteDuplicateGeometries.DeleteDupGeom(path + "/dept_" + ndept + "/departement_" + ndept + ".shp")

    print "suppression des doubles"

    # rename delete duplicate output
    outclean = path + "/dept_" + ndept + "/departement_" + ndept + "_clean.shp"
    for ext in ["shp","shx","dbf","prj"]:
        shutil.copy(outshape[:-3] + ext, outclean[:-3] + ext)
        
    for ext in ["shp","shx","dbf","prj"]:
        shutil.copy(outshape[:-3] + ext, out + "/dept_" + ndept + "/")
        
    # fill holes 
    correct_vector.correct_vector(path, grass, outclean, depts, ndept, out)
    
    return time.time() - debut_export_zone
        
if __name__ == "__main__":
    if len(sys.argv) == 1:
	prog = os.path.basename(sys.argv[0])
	print '      '+sys.argv[0]+' [options]' 
	print "     Help : ", prog, " --help"
	print "        or : ", prog, " -h"
	sys.exit(-1)  
 
    else:
	usage = "usage: %prog [options] "
	parser = argparse.ArgumentParser(description = "Merge and clip vector tiles " \
        "on a given department")
        parser.add_argument("-wd", dest="path", action="store", \
                            help="Input path where tiles are located", required = True)
                                
        parser.add_argument("-extract", dest="extract", action="store", \
                                help="departements shapefile", required = True)
                                
        parser.add_argument("-ndept", dest="ndept", action="store", \
                                help="departement number for directory and selection", required = True)
        
        parser.add_argument("-out", dest="out", action="store", \
                                help="out name directory", required = True)

        parser.add_argument("-listTiles", dest="listTiles", nargs='+', \
                                help="list of vector tiles path")

        parser.add_argument("-grass", dest="grass", action="store", \
                            help="path of grass library", required = True)           
                                
	args = parser.parse_args()
        
        if not os.path.exists(args.out + "/dept_%s"%(args.ndept)):
            os.mkdir(args.out + "/dept_%s"%(args.ndept))
        else :
            print "le repertoire de travail est %s."%("dept_" + args.ndept)
        
         
        if not os.path.exists(args.path + "/dept_%s"%(args.ndept)) :  
            os.mkdir(args.path + "/dept_%s"%(args.ndept))
        else :
            print "le repertoire de sortie est %s."%("dept_"+args.ndept)
            
        time_export_zone = mergeTileShapes(args.path, args.listTiles, args.ndept, args.extract, args.out, args.grass)
        
        with open(args.path + "/log_%s_zone_extract.csv"%(args.ndept), "w") as csvfile :
            csvfile.write("time_export_zone\n")
            csvfile.close()
            
        #initialise un fichier log de serialisation tif
        with open(args.path + "/log_%s_zone_extract.csv"%(args.ndept), "a") as csvfile :
            csvfile.write("%s\n"%(round(time_export_zone,0)))
            csvfile.close()
        
        #copy log
        shutil.copy(args.path + "/log_%s_zone_extract.csv"%(args.ndept), \
                    args.out + "/dept_%s"%(args.ndept) + "/log_%s_zone_extract.csv"%(args.ndept))
