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
import MergeFiles
import AddFieldArea
import DeleteDuplicateGeometries
import MergeFiles
import AddFieldArea
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
    gscript.run_command("g.proj", flags="c", epsg="2154", location="demolocation")    
    
    #se place dans un mapset qui va contenir les donnees et le cree
    if not os.path.exists(gisdb + "/demolocation/datas") :
        gscript.run_command("g.mapset", flags="c", mapset = "datas", location="demolocation", dbase = gisdb)

def correct_vector(path, grasslib, vector, depts, deptnb, out):
    
    init_grass(path, grasslib)
    os.chdir(path)

    deptfile = os.path.splitext(os.path.basename(vector))[0]
    deptsfile = os.path.splitext(os.path.basename(depts))[0]

    gscript.run_command("v.in.ogr", flags="e", input=vector, output=deptfile, snap="1e-07")
    gscript.run_command("v.in.ogr", flags="e", input=depts, output=deptsfile, snap="1e-07")
    # Extraction du département en cours
    deptcur = "dept{}".format(deptnb)
    
    numdep = ""
    if int(deptnb) < 10:
        numdep = '0' + str(deptnb)
    else:
        numdep = str(deptnb)

    print numdep
    gscript.run_command("v.extract", input="{}@datas".format(deptsfile), \
                        output=deptcur, \
                        where="CODE_DEPT='{}'".format(numdep))

    vectout = "eaux_%s"%(deptnb)
 
    print "Difference between department vector file and classification vector file"
    gscript.run_command("v.overlay", ainput="{}@datas".format(deptcur), \
                        binput="{}@datas".format(deptfile), \
                        operator="xor", \
                        output=vectout)

    gscript.run_command("v.db.renamecolumn", map="%s@datas"%(vectout), column="b_value,Classe")
    gscript.run_command("v.db.renamecolumn", map="%s@datas"%(deptfile), column="value,Classe")     

    gscript.run_command("v.db.update", map="%s@datas"%(vectout), layer=1, column="Classe", value=51)

    # Delete field names except "Classe"
    stdout=gscript.start_command("v.info", flags='c', map="%s@datas"%(vectout), stdout=subprocess.PIPE)
    res = stdout.communicate()
    colnames = [x.split('|')[1] for x in resl[0].rstrip().split('\n')]
    coltodel = [x for x in colnames if x != 'Classe']
    for col in coltodel:
        gscript.start_command("v.db.dropcolumn", map="%s@datas"%(vectout), columns="%s"%(col)) 

    #gscript.run_command("v.db.dropcolumn", map="%s@datas"%(vectout), columns="a_cat,a_ID_GEOFLA,a_CODE_DEPT,a_NOM_DEPT,a_CODE_CHF,a_NOM_CHF,a_X_CHF_LIEU,a_Y_CHF_LIEU,a_X_CENTROID,a_Y_CENTROID,a_CODE_REG,a_NOM_REGION,a_AreaHa,a_surf,b_cat")
    
    print "Exportation des eaux"
    
    gscript.run_command("v.out.ogr", flags="s", input="%s@datas"%(vectout), \
                        output=path, output_layer=vectout, format = "ESRI_Shapefile")
    gscript.run_command("v.out.ogr", flags="s", input="%s@datas"%(deptfile), \
                        output=path, output_layer=deptfile, format = "ESRI_Shapefile")

    pathmerge = path + '/deptmerge' + deptnb + '.shp'
    MergeFiles.mergeVectors([path + '/' + vectout + '.shp', path + '/' + deptfile + '.shp'], pathmerge)
    layermerge = 'deptmerge' + deptnb
    layerarea =  'dept' + deptnb

    for ext in ["shp","shx","dbf","prj"]:
        shutil.copy(pathmerge[:-3] + ext, out + '/' + 'dept_' + deptnb + '/')

    # Delete under MMU limit
    gscript.run_command("v.in.ogr", flags="e", input=pathmerge, output=layermerge, snap="1e-07")
    gscript.run_command("v.clean", input="%s@datas"%(layermerge), output=layerarea, tool="rmarea", thres="100", type="area")
    gscript.run_command("v.out.ogr", flags="s", input="%s@datas"%(layerarea), \
                        output=path, output_layer=layerarea, format = "ESRI_Shapefile")

    # Add area field (hectare)
    AddFieldArea.addFieldArea(path + '/' + layerarea + '.shp', 10000)
    for ext in ["shp","shx","dbf","prj"]:
        shutil.copy(layerarea + '.' + ext, out + '/' + 'dept_' + deptnb + '/')        

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

        parser.add_argument("-depts", dest="depts", action="store", \
                            help="depts vector file", required = True)    

        parser.add_argument("-out", dest="out", action="store", \
                            help="output folder", required = True)  

        args = parser.parse_args()
            
        correct_vector(args.path, args.grass, args.vector, args.depts, args.deptnb, args.out)
