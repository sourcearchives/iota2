# -*- coding: utf-8 -*-
"""
Created on Tue Apr 18 18:49:47 2017

@author: donatien
"""

import os
import sys
import ogr
import shutil
import AddFieldID
import argparse
import sqlite3
import pandas as pd
import time

def SqliteJoin(wd, shape, stats, outshape):
    
    debut = time.time()
    
    #conversion shapefile to sqlite
    command="ogr2ogr -f SQLite %s/db.sqlite %s -nln db"%(wd, shape)
    os.system(command)    
    conn=sqlite3.connect('%s/db.sqlite'%(wd))

    # get fid colname
    cursor = conn.cursor()
    cursor.execute('select * from db')
    fieldnames=[f[0] for f in cursor.description]
    idcolname = fieldnames[0]

    print idcolname
    
    # Find Max area to format area field
    sql='SELECT max(Area) FROM db'
    cursor.execute(sql)
    maxarea = cursor.fetchone()[0]
    width = len(repr(maxarea).split('.')[0]) + 3
        
    #ouvre le fichier csv
    df = pd.read_csv(stats)
    
    #cree une table avec un index selon le csv
    df.to_sql('stats', conn, if_exists='replace', index=True)
    
    cursor = conn.cursor()
    #ajoute un index à la table du shape
    AddIndex = "CREATE INDEX idx_shp ON db(%s);"%(idcolname)  
    cursor.execute(AddIndex)
    
    #creation d'une vue de jointure
    sqljoin = "create view datajoin as SELECT * FROM db LEFT JOIN stats ON db.%s = stats.FID;"%(idcolname)
    cursor.execute(sqljoin)
    print "Jointure effectuee"
    
    command = "ogr2ogr -sql 'SELECT * from datajoin' %s/shape_join.shp %s/db.sqlite"%(wd, wd)
    os.system(command)

    command = "ogr2ogr -sql 'SELECT CAST(classe AS INTEGER(4)) AS Classe, CAST(Validmean AS INTEGER(4)) AS Validmean, CAST(Validstd AS NUMERIC(5,2)) AS Validstd, CAST(Confidence AS INTEGER(4)) AS Confidence, CAST(Hiver AS NUMERIC(5,2)) AS Hiver, CAST(Ete AS NUMERIC(5,2)) AS Ete, CAST(Feuillus AS NUMERIC(5,2)) AS Feuillus, CAST(Coniferes AS NUMERIC(5,2)) AS Coniferes, CAST(Pelouse AS NUMERIC(5,2)) AS Pelouse, CAST(Landes AS NUMERIC(5,2)) AS Landes, CAST(UrbainDens AS NUMERIC(5,2)) AS UrbainDens, CAST(UrbainDiff AS NUMERIC(5,2)) AS UrbainDiff, CAST(ZoneIndCom AS NUMERIC(5,2)) AS ZoneIndCom, CAST(Route AS NUMERIC(5,2)) AS Route, CAST(PlageDune AS NUMERIC(5,2)) AS PlageDune, CAST(SurfMin AS NUMERIC(5,2)) AS SurfMin, CAST(Eau AS NUMERIC(5,2)) AS Eau, CAST(GlaceNeige AS NUMERIC(5,2)) AS GlaceNeige, CAST(Prairie AS NUMERIC(5,2)) AS Prairie, CAST(Vergers AS NUMERIC(5,2)) AS Vergers, CAST(Vignes AS NUMERIC(5,2)) AS Vignes, CAST(area AS NUMERIC(%s,2)) AS Aire FROM shape_join' %s %s/shape_join.shp"%(width, wd + "/" + outshape, wd)
    os.system(command)
    
    fin = time.time() - debut   
    
    return fin

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
        parser.add_argument("-wd", dest="wd", action="store", \
                            help="Working directory path", required = True)
                     
        parser.add_argument("-shape", dest="shape", action="store", \
                            help="Shapefile of departement", required = True)
                            
        parser.add_argument("-stats", dest="stats", action="store", \
                            help="stats.csv file of departement", required = True)
                            
        parser.add_argument("-outshape", dest="outshape", action="store", \
                            help="out shapefile name like : departement_76.shp")
                            
        parser.add_argument("-ndept", dest="ndept", action="store", \
                        help="departement number for directory and selection", required = True)   
                        
        parser.add_argument("-out", dest="out", action="store", \
                            help="out directory name", required = True) 
                                  
        args = parser.parse_args()
        
        
        if args.outshape == None :
            outshape = "departement_"+args.ndept+".shp"
        else:
            outshape = args.outshape
            
        if not os.path.exists(args.out+"/dept_%s"%(args.ndept)) :
            print "Le dossier du departement %s n'existe pas. Creation"%(args.ndept)
            os.mkdir(args.out+"/dept_%s"%(args.ndept))
            
        if not os.path.exists(args.wd+"/dept_%s"%(args.ndept)):
            os.mkdir(args.wd+"/dept_%s"%(args.ndept))
        else :
            print "Le dossier de sortie est %s."%("dept_"+args.ndept)
            
        time_join_csv_shape = SqliteJoin(args.wd+"/dept_%s"%(args.ndept), args.shape, args.stats, outshape)
        
        with open(args.wd+"/dept_%s"%(args.ndept)+"/log_%s_join.csv"%(args.ndept), "w") as csvfile :
            csvfile.write("time_join_csv_shape\n")
            csvfile.close()
    
        #initialise un fichier log de serialisation tif
        with open(args.wd+"/dept_%s"%(args.ndept)+"/log_%s_join.csv"%(args.ndept), "a") as csvfile :
            csvfile.write("%s\n"%(round(time_join_csv_shape,0)))
            csvfile.close()
        
        for ext in ["shp","shx","dbf","prj"] :
            if os.path.exists(args.wd+"/dept_%s"%(args.ndept)+"/"+outshape.split(".")[0]+"."+ext):
                shutil.copyfile(args.wd+"/dept_%s"%(args.ndept)+"/"+outshape.split(".")[0]+"."+ext, args.out+"/dept_%s"%(args.ndept)+"/"+ outshape.split(".")[0]+"." + ext)
                
        if os.path.exists(args.wd+"/dept_%s"%(args.ndept)+"/log_%s_join.csv"%(args.ndept)):
                shutil.copyfile(args.wd+"/dept_%s"%(args.ndept)+"/log_%s_join.csv"%(args.ndept), args.out+"/dept_%s"%(args.ndept)+"/log_%s_join.csv"%(args.ndept))
        
        #suppression des fichiers du cluster
        for ext in ["shp","shx","dbf","prj"] :
            os.remove(args.wd+"/dept_%s"%(args.ndept)+"/shape_join.%s"%(ext))
            os.remove(args.wd+"/dept_%s"%(args.ndept)+"/"+outshape.split(".")[0]+"."+ext)            
        os.remove(args.wd+"/dept_%s"%(args.ndept)+"/log_%s_join.csv"%(args.ndept))
        os.remove(args.wd+"/dept_%s"%(args.ndept)+"/db.sqlite")
