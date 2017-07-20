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
    gscript.run_command("g.proj", flags="c", epsg="2154", location="demolocation")    
    
    #se place dans un mapset qui va contenir les donnees et le cree
    if not os.path.exists(gisdb + "/demolocation/datas") :
        gscript.run_command("g.mapset", flags="c", mapset = "datas", location="demolocation", dbase = gisdb)

def correct_vector(path, grasslib, vector, deptnb):

    init_grass(path, grasslib)
    os.chdir(path)

    deptfile = os.path.splitext(os.path.basename(vector))[0]
    
    print "importation of input files"

    gscript.run_command("v.in.ogr", flags="e", input=vector, output=deptfile)
    
    vectout = "dept_final%s"%(deptnb)

    print "modification NUll"    

    gscript.run_command("v.db.update", map="%s@datas"%(deptfile), layer=1, column="Classe", value=51, where="Classe is NULL")

    print "exportation test"    

    gscript.run_command("v.out.ogr", input="%s@datas"%(deptfile), output=path, output_layer=deptfile, format = "ESRI_Shapefile")

    print "Fusion"    
    
    gscript.run_command("v.dissolve", input="%s@datas"%(deptfile), column="Classe", output="%s@datas"%(vectout))  

    print "Exportation"
    
    gscript.run_command("v.out.ogr", input="%s@datas"%(vectout), output=path, output_layer=vectout, format = "ESRI_Shapefile")
    

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

        parser.add_argument("-ndept", dest="deptnb", action="store", \
                            help="dept number", required = True)     

        parser.add_argument("-classif", dest="vector", action="store", \
                            help="classification vector file", required = True)    

        parser.add_argument("-out", dest="out", action="store", \
                            help="output folder", required = True)  

        args = parser.parse_args()

        correct_vector(args.path, args.grass, args.vector, args.deptnb)

        for ext in ["shp","shx","dbf","prj"] :
            if os.path.exists(args.path + "/dept_final%s.%s"%(deptnb, ext)):
                shutil.copy(args.path + "/dept_final%s.%s"%(deptnb, ext), \
                            args.out + "/dept_final%s.%s"%(deptnb, ext))             
