# -*- coding: utf-8 -*-
"""
Join out shapefile with stats.csv and rename fields.

"""

import sys
import os
import argparse
import vector_functions as vf
import DeleteField
import AddFieldID
import time
import shutil
import ogr
import sqlite3 as lite
import pandas as pad

def renameDeleteFields(inshapefile):
    """
    Rename and delete fields
    
    in :
        inshapefile : out shape from join step
    """

    columns = ["Classe", "Validmean", "Validstd", "Confidence","Hiver", "Ete", "Feuillus", "Coniferes", \
               "Pelouse", "Landes", "UrbainDens", "UrbainDiff", "ZoneIndCom","Route", "PlageDune", "SurfMin", \
               "Eau", "GlaceNeige", "Prairie", "Vergers", "Vignes", "Aire"]    

    layer = os.path.splitext(os.path.basename(inshapefile))[0]
    fields = vf.getFields(inshapefile)
    count = 0
    countclass = 0
    todel = []
    for field in fields:
        if count in [0, 2, 3]:
            todel.append(field)
            count += 1
        else:
            os.system(("ogrinfo {} -sql \"ALTER TABLE {} RENAME COLUMN {} TO {}\"")\
                      .format(inshapefile, layer, field, columns[countclass]))
            count += 1
            countclass += 1

    for delfield in todel:
        DeleteField.deleteField(inshapefile, delfield)
    
def join_csv_with_shape(shape, stats, dept_folder, ndept):
    """
    Join a departement shapefile with a stats csv file.
    
    in  : 
        shape : name of simplified shapefile
        out : name of directory where the shapefile and csvfile are located
        
    out :
        shapefile with stats and classes
    """
    os.chdir(dept_folder)
    shape_name = os.path.splitext(os.path.basename(shape))[0]
    debut = time.time()
    
    IdExist = False
    
    driver = ogr.GetDriverByName("ESRI Shapefile")
    shapefile = driver.Open(shape, 0)
    layer = shapefile.GetLayer()
    layerDfn = layer.GetLayerDefn()
    for field in range(layerDfn.GetFieldCount()):
        print layerDfn.GetFieldDefn(field).GetName()
        if layerDfn.GetFieldDefn(field).GetName() == "ID" :
            IdExist = True
            
    layer = None
    shapefile = None
    
    if not IdExist :    
        AddFieldID.addFieldID(shape)
        print "Creation de l'attribut ID"

    # do join between simplified shapefile and stats csv
    command = "ogr2ogr -sql 'SELECT CAST(%s.ID AS INTEGER(10)), CAST(%s.Classe AS INTEGER(10)), CAST(stats.FID AS INTEGER(10)), CAST(stats.Classe AS INTEGER(4)), CAST(stats.Validmean AS INTEGER(4)), CAST(stats.Validstd AS NUMERIC(5,2)), CAST(stats.Confidence AS INTEGER(4)), CAST(stats.Hiver AS NUMERIC(5,2)), CAST(stats.Ete AS NUMERIC(5,2)), CAST(stats.Feuillus AS NUMERIC(5,2)), CAST(stats.Coniferes AS NUMERIC(5,2)), CAST(stats.Pelouse AS NUMERIC(5,2)), CAST(stats.Landes AS NUMERIC(5,2)), CAST(stats.UrbainDens AS NUMERIC(5,2)), CAST(stats.UrbainDiff AS NUMERIC(5,2)), CAST(stats.ZoneIndCom AS NUMERIC(5,2)), CAST(stats.Route AS NUMERIC(5,2)), CAST(stats.PlageDune AS NUMERIC(5,2)), CAST(stats.SurfMin AS NUMERIC(5,2)), CAST(stats.Eau AS NUMERIC(5,2)), CAST(stats.GlaceNeige AS NUMERIC(5,2)), CAST(stats.Prairie AS NUMERIC(5,2)), CAST(stats.Vergers AS NUMERIC(5,2)), CAST(stats.Vignes AS NUMERIC(5,2)), CAST(%s.Area AS NUMERIC(5,2)) FROM %s LEFT JOIN \"%s\".stats on %s.ID = stats.FID' departement_%s.shp %s"\
    %(shape_name, shape_name, shape_name, shape_name, stats, shape_name, ndept, shape)
    os.system(command)
    
    # rename fields and delete fields
    renameDeleteFields(dept_folder + "/departement_%s.shp"%(ndept))
    
    fin = time.time() - debut     
    
    return fin, "departement_%s"%(ndept)

if __name__ == "__main__":
    if len(sys.argv) == 1:
	prog = os.path.basename(sys.argv[0])
	print '      '+sys.argv[0]+' [options]' 
	print "     Help : ", prog, " --help"
	print "        or : ", prog, " -h"
	sys.exit(-1)  
 
    else:
	usage = "usage: %prog [options] "
	parser = argparse.ArgumentParser(description = "Regulararize a raster" \
        "and simplify the corresponding vector ")
        parser.add_argument("-wd", dest="path", action="store", \
                            help="Input path where vector and stats.csv", required = True)
                     
        parser.add_argument("-vecteur", dest="shape", action="store", \
                            help="Name of departement shapefile", required = True)
                            
        parser.add_argument("-stats", dest="stats", action="store", \
                            help="stats.csv file", required = True)
        
        parser.add_argument("-out", dest="out", action="store", \
                            help="out directory name", required = True) 
                            
        parser.add_argument("-ndept", dest="ndept", action="store", \
                        help="departement number for directory and selection", required = True)                    
                                  
        args = parser.parse_args()
        
        os.chdir(args.path)
            
        if not os.path.exists(args.path+"/dept_%s"%(args.ndept)):
            os.mkdir(args.path+"/dept_%s"%(args.ndept))
        else :
            print "Le dossier de sortie est %s."%("dept_"+args.ndept)
            
        time_join_csv_shape,deptname  = join_csv_with_shape(args.shape, args.stats, args.path+"/dept_"+args.ndept, args.ndept)
        
        with open(args.path+"/dept_%s"%(args.ndept)+"/log_%s_join.csv"%(args.ndept), "w") as csvfile :
            csvfile.write("time_join_csv_shape\n")
            csvfile.close()
    
        #initialise un fichier log de serialisation tif
        with open(args.path+"/dept_%s"%(args.ndept)+"/log_%s_join.csv"%(args.ndept), "a") as csvfile :
            csvfile.write("%s\n"%(round(time_join_csv_shape,0)))
            csvfile.close()
        
        for ext in ["shp","shx","dbf","prj"] :
            if os.path.exists(args.path+"/dept_%s"%(args.ndept) + "/" + deptname + ".%s"%(ext)):
                shutil.copy(args.path+"/dept_%s"%(args.ndept) + "/" + deptname + ".%s"%(ext), \
                            args.out + "/" + deptname + ".%s"%(ext))
                
        pathdept = os.path.dirname(args.shape)
        if os.path.exists(args.path+"/dept_%s"%(args.ndept)+"/log_%s_join.csv"%(args.ndept)):
                shutil.copy(args.path + "/dept_%s"%(args.ndept)+"/log_%s_join.csv"%(args.ndept), \
                            pathdept + "/log_%s_join.csv"%(args.ndept))
        
