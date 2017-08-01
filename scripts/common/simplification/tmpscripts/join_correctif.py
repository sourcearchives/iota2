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
               "Eau", "GlaceNeige", "Prairie", "Vergers", "Vignes"]    

    layer = os.path.splitext(os.path.basename(inshapefile))[0]
    fields = vf.getFields(inshapefile)
    count = 0
    todel = []
    for field in fields:
        if count in [0, 1, 2]:
            todel.append(field)
            count += 1
        else:
            os.system(("ogrinfo {} -sql \"ALTER TABLE {} RENAME COLUMN {} TO {}\"")\
                      .format(inshapefile, layer, field, columns[count - 3]))
            count += 1

    for delfield in todel:
        DeleteField.deleteField(inshapefile, delfield)
    
def join_csv_with_shape(shape, stats, dept_folder):
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

    # do join between simplified shapefile and stats csv
    command = "ogr2ogr -sql 'SELECT CAST(%s.value AS NUMERIC(5,2)), CAST(%s.cat AS INTEGER(10)), CAST(stats.FID AS INTEGER(10)), CAST(stats.Classe AS INTEGER(4)), CAST(stats.Validmean AS INTEGER(4)), CAST(stats.Validstd AS NUMERIC(5,2)), CAST(stats.Confidence AS INTEGER(4)), CAST(stats.Hiver AS NUMERIC(5,2)), CAST(stats.Ete AS NUMERIC(5,2)), CAST(stats.Feuillus AS NUMERIC(5,2)), CAST(stats.Coniferes AS NUMERIC(5,2)), CAST(stats.Pelouse AS NUMERIC(5,2)), CAST(stats.Landes AS NUMERIC(5,2)), CAST(stats.UrbainDens AS NUMERIC(5,2)), CAST(stats.UrbainDiff AS NUMERIC(5,2)), CAST(stats.ZoneIndCom AS NUMERIC(5,2)), CAST(stats.Route AS NUMERIC(5,2)), CAST(stats.PlageDune AS NUMERIC(5,2)), CAST(stats.SurfMin AS NUMERIC(5,2)), CAST(stats.Eau AS NUMERIC(5,2)), CAST(stats.GlaceNeige AS NUMERIC(5,2)), CAST(stats.Prairie AS NUMERIC(5,2)), CAST(stats.Vergers AS NUMERIC(5,2)), CAST(stats.Vignes AS NUMERIC(5,2)) FROM %s LEFT JOIN \"%s\".stats on %s.cat = stats.FID' %s_resultatfinal.shp %s"\
    %(shape_name, shape_name, shape_name, stats, shape_name, shape_name, shape)
    os.system(command)
    
    # rename fields and delete fields
    renameDeleteFields(dept_folder + "/" + shape_name + "_resultatfinal.shp")

    return shape_name + "_resultatfinal"

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

        if not os.path.exists(args.out+"/dept_%s"%(args.ndept)) :
            print "Le dossier correspondant au departement %s n'existe pas dans le dossier de sortie. Le departement n'existe pas ou bien, l'etape oso_extract n'a pas ete effectuee. Arret"%(args.ndept)
            sys.exit()
            
        if not os.path.exists(args.path+"/dept_%s"%(args.ndept)):
            os.mkdir(args.path+"/dept_%s"%(args.ndept))
        else :
            print "Le dossier de sortie est %s."%("dept_"+args.ndept)

        name = join_csv_with_shape(args.shape, args.stats, args.path+"/dept_"+args.ndept)

        shape_name = os.path.splitext(os.path.basename(args.shape))[0]

        for ext in ["shp","shx","dbf","prj"] :
            if os.path.exists(args.path+"/dept_%s"%(args.ndept) + '/' + name + ".%s"%(ext)):
                shutil.copy(args.path+"/dept_%s"%(args.ndept) + '/' + name +".%s"%(ext), \
                            args.out+"/dept_%s"%(args.ndept) + '/' + shape_name + ".%s"%(ext))
        
        #suppression des fichiers du cluster
        for ext in ["shp","shx","dbf","prj"] :
            os.remove(args.path+"/dept_%s"%(args.ndept) + '/' + name +".%s"%(ext))            
