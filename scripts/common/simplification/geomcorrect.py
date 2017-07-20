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
    if not os.path.exists(path + "/grassdata"):
        os.mkdir(path + "/grassdata")
    path_grassdata = path +"/grassdata"
    print path_grassdata
    
    #initialise l'utilisation de grass dans un script python
    gisbase = os.environ['GISBASE'] = grasslib
    gisdb = os.path.join(path_grassdata)
    sys.path.append(os.path.join(os.environ["GISBASE"], "etc", "python"))
    os.environ["GISBASE"] = gisbase
    
    #permet de relancer le script plusieurs fois en permettant d'ecraser les fichiers
    os.environ["GRASS_OVERWRITE"] = "1"
    os.environ['GRASS_VERBOSE']='-1'
    
    #importe les fonctions grass
    import grass.script.setup as gsetup
    import grass.script as gscript
    
    #initialise grass72 (important pour accelerer Simplification et lissage)
    gsetup.init(gisbase, gisdb)

    #supprime la location si elle existe deja
    if os.path.exists(gisdb + "/demolocation"):
        shutil.rmtree(gisdb + "/demolocation")
    
    #cree une nouvelle location nommee demolocation en lambert 93
    gscript.run_command("g.gisenv", set="DEBUG=1")
    gscript.run_command("g.proj", flags="c", epsg="2154", location="demolocation")
    #se place dans un mapset qui va contenir les donnees et le cree
    if not os.path.exists(gisdb + "/demolocation/datas") :
        gscript.run_command("g.mapset", flags="c", mapset = "datas", location="demolocation", dbase = gisdb)
                              
def geom_correct(path, grasslib, vector, snap):

    init_grass(path, grasslib)
    os.chdir(path)

    deptfile = os.path.splitext(os.path.basename(vector))[0]
    msg = gscript.start_command("v.in.ogr", flags="e", input=vector, output=deptfile, snap="1e-0%s"%(snap), verbose=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    stdoutdata, stderrdata = msg.communicate()
    print stdoutdata, stderrdata
    
    while "Some input polygons are overlapping each other" in stdoutdata:
        snap -= 1 
        msg = gscript.start_command("v.in.ogr", flags="e", input=vector, output=deptfile, snap="1e-0%s"%(snap), verbose=True, overwrite=True)
        stdoutdata, stderrdata = msg.communicate()
        
    vectout = "%s_final"%(deptfile)
    
    gscript.run_command("v.out.ogr", input="%s@datas"%(deptfile), output=path, output_layer=vectout, format = "ESRI_Shapefile")

    return vectout

if __name__ == "__main__":
    if len(sys.argv) == 1:
	prog = os.path.basename(sys.argv[0])
	print '      '+sys.argv[0]+' [options]' 
	print "     Help : ", prog, " --help"
	print "        or : ", prog, " -h"
	sys.exit(-1)  

    else:
	usage = "usage: %prog [options] "
	parser = argparse.ArgumentParser(description = "tif generation for simplification")
        parser.add_argument("-wd", dest="path", action="store", \
                            help="Input path of tile directory", required = True)
        
        parser.add_argument("-grass", dest="grass", action="store", \
                            help="path of grass library", required = True)    

        parser.add_argument("-classif", dest="vector", action="store", \
                            help="classification vector file", required = True)    

        parser.add_argument("-out", dest="out", action="store", \
                            help="output folder", required = True)

        parser.add_argument("-snap", dest="snap", action="store", \
                            help="snap to delete overlapping polygons", required = True)           

        args = parser.parse_args()

        vectout = geom_correct(args.path, args.grass, args.vector, args.snap)
        
        for ext in ["shp","shx","dbf","prj"] :
            if os.path.exists(args.path + "/%s.%s"%(vectout, ext)):
                shutil.copy(args.path + "/%s.%s"%(vectout, ext), \
                            args.out + "/%s.%s"%(vectout, ext))             
