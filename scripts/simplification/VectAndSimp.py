#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Vectorisation and simplification of a raster file with grass library
"""

import shutil
import sys, os, argparse
import time
import logging
logger = logging.getLogger(__name__)

#------------------------------------------------------------------------------
            
def init_grass(path, grasslib, debuglvl):

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
    debugdic = {"critical" : '0', "error" : '0', "warning":'1', "info":'2' , "debug":'3'}
    os.environ["GRASS_OVERWRITE"] = "1"
    os.environ['GRASS_VERBOSE']= debugdic[debuglvl]

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
        
        
def simplification(path, raster, grasslib, out, douglas, hermite, mmu, angle=True, debulvl="info", logger=logger):
    """
        Simplification of raster dataset with Grass GIS.
        
        in :
            path : path where do treatments
            raster : classification raster name
            douglas : Douglas-Peucker reduction value
            hermite : Hermite smoothing level
            angle : Smooth corners of pixels (45°)
            grasslib : Path of folder with grass GIS install
            
        out : 
            shapefile with standart name ("tile_ngrid.shp")
    """
    
    timeinit = time.time()
        
    init_grass(path, grasslib,  debulvl)
        
    # classification raster import        
    gscript.run_command("r.in.gdal", flags="e", input=raster, output="tile", overwrite=True)

    timeimport = time.time()     
    logger.info(" ".join([" : ".join(["Classification raster import", str(timeimport - timeinit)]), "seconds"]))
    
    # manage grass region
    gscript.run_command("g.region", raster="tile")
    
    if angle:
        # vectorization with corners of pixel smoothing 
        gscript.run_command("r.to.vect", flags = "sv", input="tile@datas", output="vectile", type="area", overwrite=True)
        
    else:
        # vectorization without corners of pixel smoothing 
        gscript.run_command("r.to.vect", flags = "v", input = "tile@datas", output="vectile", type="area", overwrite=True)

    timevect = time.time()     
    logger.info(" ".join([" : ".join(["Classification vectorization", str(timevect - timeimport)]), "seconds"]))

    inputv = "vectile"
    # Douglas simplification    
    if douglas is not None:
        gscript.run_command("v.generalize", \
                            input = "%s@datas"%(inputv), \
                            method="douglas", \
                            threshold="%s"%(douglas), \
                            output="douglas",
                            overwrite=True)
        inputv = "douglas"
        
        timedouglas = time.time()     
        logger.info(" ".join([" : ".join(["Douglas simplification", str(timedouglas - timevect)]), "seconds"]))
        timevect = timedouglas
    
    # Hermine simplification
    if hermite is not None:
        gscript.run_command("v.generalize", \
                            input = "%s@datas"%(inputv), \
                            method="hermite", \
                            threshold="%s"%(hermite), \
                            output="hermine", \
                            overwrite=True)
        inputv = "hermine"

        timehermine = time.time()     
        logger.info(" ".join([" : ".join(["Hermine smoothing", str(timehermine - timevect)]), "seconds"]))
        timevect = timehermine
        
    # Delete non OSO class polygons (sea water, nodata and crown entities)
    gscript.run_command("v.edit", map = "%s@datas"%(inputv), tool = "delete", where = "cat > 250 or cat < 1")

    # Export shapefile vector file
    if os.path.splitext(out)[1] != '.shp':
        out = os.path.splitext(out)[0] + '.shp'
        logger.info("Output name has been changed to '%s'"%(out))

    # Delete under MMU limit    
    gscript.run_command("v.clean", input = "%s@datas"%(inputv), output="cleanarea", tool="rmarea", thres=mmu, type="area")        

    # Export vector file
    gscript.run_command("v.out.ogr", input = "cleanarea", output = out, format = "ESRI_Shapefile")

    timeexp = time.time()     
    logger.info(" ".join([" : ".join(["Vectorization exportation", str(timeexp - timevect)]), "seconds"]))
        
    shutil.rmtree(os.path.join(path, "grassdata"))

    timeend = time.time()     
    logger.info(" ".join([" : ".join(["Global Vectorization and Simplification process", str(timeend - timeinit)]), "seconds"]))
    
if __name__ == "__main__":
    if len(sys.argv) == 1:
	prog = os.path.basename(sys.argv[0])
	print '      '+sys.argv[0]+' [options]' 
	print "     Help : ", prog, " --help"
	print "        or : ", prog, " -h"
	sys.exit(-1)  

    else:
	usage = "usage: %prog [options] "
	parser = argparse.ArgumentParser(description = "Vectorisation and simplification of a raster file")
        
        parser.add_argument("-wd", dest="path", action="store", \
                            help="Working directory", required = True)
        
        parser.add_argument("-grass", dest="grass", action="store", \
                            help="path of grass library", required = True)
                            
        parser.add_argument("-in", dest="raster", action="store", \
                            help="classification raster", required = True)
                            
        parser.add_argument("-out", dest="out", action="store", \
                            help="output folder and name", required = True)  
                            
        parser.add_argument("-douglas", dest="douglas", action="store", \
                            help="Douglas-Peucker reduction value, if empty no Douglas-Peucker reduction")   
                            
        parser.add_argument("-hermite", dest="hermite", action="store", \
                            help="Hermite smoothing level, if empty no Hermite smoothing reduction")   
                            
        parser.add_argument("-angle", action="store_true", \
                            help="Smooth corners of pixels (45°), if empty no corners smoothing", default = False)
        
        parser.add_argument("-mmu", dest="mmu", action="store", \
                                help="Mininal Mapping Unit (shapefile area unit)", type = int, required = True)                        

        parser.add_argument("-debuglvl", dest="debuglvl", action="store", \
                                help="Debug level", default = "info", required = False)                        
                                
    args = parser.parse_args()
    
    simplification(args.path, args.raster, args.grass, args.out, args.douglas, args.hermite, args.mmu, args.angle, args.debuglvl)
