# -*- coding: utf-8 -*-
"""
Simplifie un raster en plusieurs etapes consecutives avec grass GIS : 
vectorisation, simplification, lissage, export au format shapefile.
"""

import shutil
import sys
import os
import time
import argparse
import subprocess

#------------------------------------------------------------------------------
            
def init_grass(path, grasslib):

    """
    Initialisation of Grass GIS in lambert 93.
    
    in : 
        path : directory where create grassdata directory
        grasslib : install directory of Grass GIS
    """ 
    
    global gscript  
    
    #se place dans le repertoire courant pour créer le dossier grassdata     
    if not os.path.exists(os.path.join(path, "grassdata")):
        os.mkdir(os.path.join(path, "grassdata"))
    path_grassdata = os.path.join(path, "grassdata")
    
    #initialise l'utilisation de grass dans un script python
    gisbase = os.environ['GISBASE'] = grasslib
    gisdb = os.path.join(path_grassdata)
    sys.path.append(os.path.join(os.environ["GISBASE"], "etc", "python"))
    os.environ["GISBASE"] = gisbase
    
    #permet de relancer le script plusieurs fois en permettant d'ecraser les fichiers
    os.environ["GRASS_OVERWRITE"] = "1"
    os.environ['GRASS_VERBOSE']='3'
    
    #importe les fonctions grass
    import grass.script.setup as gsetup
    import grass.script as gscript
    
    #initialise grass72 (important pour accelerer Simplification et lissage)
    gsetup.init(gisbase, gisdb)
    
    #supprime la location si elle existe deja
    if os.path.exists(os.path.join(gisdb, "demolocation")):
        shutil.rmtree(os.path.join(gisdb, "demolocation"))
    
    #cree une nouvelle location nommee demolocation en lambert 93
    gscript.run_command("g.proj", flags="c", epsg="2154", location="demolocation")    
    
    #se place dans un mapset qui va contenir les donnees et le cree
    if not os.path.exists(os.path.join(gisdb, "/demolocation/datas")) :
        try:
            gscript.start_command("g.mapset", flags="c", mapset = "datas", location = "demolocation", dbase = gisdb)
        except:
            raise Exception("Folder '%s' does not own to current user")%(gisdb)
        
        
def simplification(path, raster, grasslib, out, douglas, hermite, angle=True):
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
        
    init_grass(path, grasslib)
        
    # classification raster import        
    gscript.run_command("r.in.gdal", input = raster, output = "classification")

    timeimport = time.time()     
    print " ".join([" : ".join(["classification raster import", str(timeimport - timeinit)]), "seconds"])
    
    # manage grass region
    gscript.run_command("g.region", raster = "classification")
    
    if angle:
        # vectorization with corners of pixel smoothing 
        gscript.run_command("r.to.vect", flags = "s", input="classification@datas", output="vecteur", type="area")
        
    else:
        # vectorization without corners of pixel smoothing 
        gscript.run_command("r.to.vect", input = "classification@datas", output="vecteur", type = "area")
    gscript.run_command('g.list', type="vector")
    timevect = time.time()     
    print " ".join([" : ".join(["classification vectorization", str(timevect - timeimport)]), "seconds"])    

    inputv = "vecteur"
    # Douglas simplification    
    if douglas is not None:
        gscript.run_command("v.generalize", input = "%s@datas"%(inputv), method="douglas", threshold="%s"%(douglas), output="douglas", type="area")
        inputv = "douglas"
        
        timedouglas = time.time()     
        print " ".join([" : ".join(["Douglas simplification", str(timedouglas - timevect)]), "seconds"])
        timevect = timedouglas

    gscript.run_command('g.list', type="vector")
    
    # Hermine simplification
    if hermite is not None:
        gscript.run_command("v.generalize", \
                            input = "%s@datas"%(inputv), \
                            method="hermite", \
                            threshold="%s"%(hermite), \
                            output="hermine", \
                            verbose=True, \
                            type="area", \
                            overwrite=True)
        inputv = "hermine"

        timehermine = time.time()     
        print " ".join([" : ".join(["Hermine smoothing", str(timehermine - timevect)]), "seconds"])
        timevect = timehermine
        
    # Delete non OSO class polygons (sea water, nodata and crown entities)
    gscript.run_command("v.edit", map = "%s@datas"%(inputv), tool = "delete", where = "value > 250 or value < 1")

    # Export shapefile vector file
    if os.path.splitext(out)[1] != '.shp':
        out = os.path.splitext(out)[0] + '.shp'
        print "Output name has been changed to '%s'"%(out)
        
    gscript.run_command("v.out.ogr", input = "%s@datas"%(inputv), dsn = out, format = "ESRI_Shapefile")

    timeexp = time.time()     
    print " ".join([" : ".join(["vectorization exportation", str(timeexp - timevect)]), "seconds"])    
        
    shutil.rmtree(os.path.join(path, "grassdata"))                   
    
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
                            help="Input path of tile directory", required = True)
        
        parser.add_argument("-grass", dest="grass", action="store", \
                            help="path of grass library", required = True)
                            
        parser.add_argument("-in", dest="raster", action="store", \
                            help="tile raster from job_tif", required = True)
                            
        parser.add_argument("-out", dest="out", action="store", \
                            help="output foldern and name", required = True)  
                            
        parser.add_argument("-douglas", dest="douglas", action="store", \
                            help="Douglas-Peucker reduction value")   
                            
        parser.add_argument("-hermite", dest="hermite", action="store", \
                            help="Hermite smoothing level")   
                            
        parser.add_argument("-angle", action="store_true", \
                            help="Smooth corners of pixels (45°)", default = False)   
                                
    args = parser.parse_args()
    
    simplification(args.path, args.raster, args.grass, args.out, args.douglas, args.hermite, args.angle)
