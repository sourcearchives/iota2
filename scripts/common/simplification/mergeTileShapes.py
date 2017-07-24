# -*- coding: utf-8 -*-
"""
Merge some shapefile simplified and clip them according to an another shape.

"""

import shutil
import sys
import os
import time
import argparse
import correct_vector
try:
    import fileUtils as fut
except ImportError:
    raise ImportError('Iota2 not well configured / installed')

try:    
    import DeleteDuplicateGeometries
    import vector_functions as vf
except ImportError:
    raise ImportError('Vector tools not well configured / installed')


def init_grass(path, grasslib):

    """
    Initialisation of Grass GIS in lambert 93.
    
    in : 
        path : directory where create grassdata directory
        grasslib : install directory of Grass GIS
    """ 
    
    global gscript  
    
    # Grass folder Initialisation
    if not os.path.exists(os.path.join(path, "grassdata")):
        os.mkdir(os.path.join(path, "grassdata"))
    path_grassdata = os.path.join(path, "grassdata")
    
    # Init Grass environment
    gisbase = os.environ['GISBASE'] = grasslib
    gisdb = os.path.join(path_grassdata)
    sys.path.append(os.path.join(os.environ["GISBASE"], "etc", "python"))
    os.environ["GISBASE"] = gisbase
    
    # Overwrite and verbose parameters
    os.environ["GRASS_OVERWRITE"] = "1"
    os.environ['GRASS_VERBOSE']='-1'
    
    # Grass functions import
    import grass.script.setup as gsetup
    import grass.script as gscript
    
    # Init Grass
    gsetup.init(gisbase, gisdb)
    
    # Delete existing location
    if os.path.exists(os.path.join(gisdb, "demolocation")):
        shutil.rmtree(os.path.join(gisdb, "demolocation"))
    
    # Create the location in Lambert 93
    gscript.run_command("g.proj", flags="c", epsg="2154", location="demolocation")    
    
    # Create datas mapset
    if not os.path.exists(os.path.join(gisdb, "/demolocation/datas")) :
        try:
            gscript.start_command("g.mapset", flags="c", mapset = "datas", location = "demolocation", dbase = gisdb)
        except:
            raise Exception("Folder '%s' does not own to current user")%(gisdb)


def mergeTileShapes(path, list_files_tiles, out, grass, mmu, clipfile = "", fieldclip = "", valueclip = ""):

    timeinit = time.time()
    
    # Empty shapefile
    fut.createPolygonShapefile(os.path.join(path, "merge.shp"), 2154, 'ESRI Shapefile')

    # merge tile shapefiles   
    for file_tile in list_files_tiles:
        command = "ogr2ogr -update -addfields -skipfailures %s %s"%(os.path.join(path, "merge.shp"), file_tile)
        os.system(command)

    timemerge = time.time()     
    print " ".join([" : ".join(["Merge shapefiles", str(timemerge - timeinit)]), "seconds"])    
        
    # Get clip shafile layer    
    if clipfile != "":
        if getNbFeat(shapefile) != 1:
            clip = os.path.join(path + "clip.shp")
            layer = vf.getFirstLayer(shp)
            fieldType = vf.getFieldType(clipfile, fieldclip)

            if fieldType == str:
                command = "ogr2ogr -sql \"SELECT * FROM %s WHERE %s = \'%s\'\" %s %s"%(fieldclip, \
                                                                                       layer, \
                                                                                       valueclip, \
                                                                                       clip, \
                                                                                       clipfile)
            elif fieldType == int or fieldType == float:
                command = "ogr2ogr -sql \"SELECT * FROM %s WHERE %s = %s\" %s %s"%(fieldclip, \
                                                                                   layer, \
                                                                                   valueclip, \
                                                                                   clip, \
                                                                                   clipfile)
            else:
                raise Exception('Field type %s not handled'%(fieldType))
        else:
            print "'%s' shapefile has only one feature which will used to clip data"%(clip)
            clip = clipfile
            
        os.system(command)
        
        # clip
        clipped = os.path.join(path + "clipped.shp")
        command = "ogr2ogr -select value -clipsrc %s %s %s"%(clip, \
                                                             clipped, \
                                                             os.path.join(path, "merge.shp"))
        os.system(command)
        
    else:
        clipped = os.path.join(path, "merge.shp")

    timeclip = time.time()     
    print " ".join([" : ".join(["Clip final shapefile", str(timeclip - timemerge)]), "seconds"])            
        
    # Delete duplicate geometries
    outshape = DeleteDuplicateGeometries.DeleteDupGeom(clipped)
    for ext in [".shp",".shx",".dbf",".prj"]:
        shutil.copy(os.path.splitext(outshape) + ext, os.path.join(path, "clean") + ext)    

    timedupli = time.time()     
    print " ".join([" : ".join(["Delete duplicated geometries", str(timedupli - timeclip)]), "seconds"])            
        
    # Delete under MMU limit
    init_grass(path, grasslib)
    gscript.run_command("v.in.ogr", flags="e", input="clean", output="cleansnap", snap="1e-07")
    gscript.run_command("v.clean", input="cleansnap@datas"%(cleansnap), output="cleanarea", tool="rmarea", thres=mmu, type="area")
    gscript.run_command("v.out.ogr", input = "cleanarea@datas", dsn = out, format = "ESRI_Shapefile")
    
    timemmu = time.time()     
    print " ".join([" : ".join(["Delete and merge under MMU polygons", str(timemmu - timedupli)]), "seconds"])            

    timeprodvect = time.time()     
    print " ".join([" : ".join(["Production of final shapefile geometry", str(timeprodvect - timeinit)]), "seconds"])            
    
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

        parser.add_argument("-listTiles", dest="listTiles", nargs='+', \
                                help="list of tiles shapefiles")

        parser.add_argument("-grass", dest="grass", action="store", \
                            help="path of grass library", required = True)

        parser.add_argument("-out", dest="out", action="store", \
                                help="out name file and directory", required = True)
        
        parser.add_argument("-mmu", dest="mmu", action="store", \
                                help="Mininal Mapping Unit (shapefile area unit)", required = True)                

        parser.add_argument("-extract", dest="extract", action="store", \
                                help="clip shapefile")

        parser.add_argument("-field", dest="field", action="store", \
                                help="Field to select feature to clip")

        parser.add_argument("-value", dest="value", action="store", \
                                help="Value of the field to select feature to clip")                
        
	args = parser.parse_args()
            
        mergeTileShapes(args.path, args.listTiles, args.out, args.grass, args.mmu, args.extract, args.field, args.value)
