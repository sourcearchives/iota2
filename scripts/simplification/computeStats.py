#!/usr/bin/python
#-*- coding: utf-8 -*-

# =========================================================================
#   Program:   iota2
#
#   Copyright (c) CESBIO. All rights reserved.
#
#   See LICENSE for details.
#
#   This software is distributed WITHOUT ANY WARRANTY; without even
#   the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR
#   PURPOSE.  See the above copyright notices for more information.
#
# =========================================================================

import os
import sys
import argparse
import csv
import sqlite3
from pyspatialite import dbapi2 as db
    
def importstats(csvstore, sqlite):

    con = sqlite3.connect(sqlite)
    cur = con.cursor()
    cur.execute("CREATE TABLE stats (fid integer, info text, stat text, class integer, value real);")
    
    with open(csvstore, 'rb') as f:
        reader = csv.reader(f)
        cur = con.cursor()
        cur.executemany("INSERT INTO stats(fid, info, stat, class, value) VALUES (?, ?, ?, ?, ?);", reader)        
        con.commit()
        con.close()

def pivotstats(sqlite):

    con = sqlite3.connect(sqlite)
    cur = con.cursor()
    # Pivot statistics table
    cur.execute('CREATE TABLE statsfinal AS '\
                'SELECT s.fid, '\
                'confmean.value as mconf, '\
                'confstd.value as stdconf, '\
                'CAST(valid.value AS INTEGER) as validity, '\
                'COALESCE(CAST(ROUND(out11.value, 2) AS FLOAT),0) AS Ete, '\
                'COALESCE(CAST(ROUND(out12.value, 2) AS FLOAT),0) AS Hiver, '\
                'COALESCE(CAST(ROUND(out31.value, 2) AS FLOAT),0) AS Feuillus, '\
                'COALESCE(CAST(ROUND(out32.value, 2) AS FLOAT),0) AS Coniferes, '\
                'COALESCE(CAST(ROUND(out34.value, 2) AS FLOAT),0) AS Pelouse, '\
                'COALESCE(CAST(ROUND(out36.value, 2) AS FLOAT),0) AS Landes, '\
                'COALESCE(CAST(ROUND(out41.value, 2) AS FLOAT),0) AS UrbainDens, '\
                'COALESCE(CAST(ROUND(out42.value, 2) AS FLOAT),0) AS UrbainDiff, '\
                'COALESCE(CAST(ROUND(out43.value, 2) AS FLOAT),0) AS ZoneIndCom, '\
                'COALESCE(CAST(ROUND(out44.value, 2) AS FLOAT),0) AS Route, '\
                'COALESCE(CAST(ROUND(out45.value, 2) AS FLOAT),0) AS SurfMin, '\
                'COALESCE(CAST(ROUND(out46.value, 2) AS FLOAT),0) AS PlageDune, '\
                'COALESCE(CAST(ROUND(out51.value, 2) AS FLOAT),0) AS Eau, '\
                'COALESCE(CAST(ROUND(out53.value, 2) AS FLOAT),0) AS GlaceNeige, '\
                'COALESCE(CAST(ROUND(out211.value, 2) AS FLOAT),0) AS Prairie, '\
                'COALESCE(CAST(ROUND(out221.value, 2) AS FLOAT),0) AS Vergers, '\
                'COALESCE(CAST(ROUND(out222.value, 2) AS FLOAT),0) AS Vignes '\
                'FROM '\
                '(SELECT '\
                'fid '\
                'FROM stats '\
                'GROUP BY fid '\
                'ORDER BY fid) s ' \
                'LEFT JOIN '
                '(select fid, value from stats where info = "confidence" and stat = "mean") confmean ' \
                'ON s.fid = confmean.fid '\
                'LEFT JOIN '
                '(select fid, value from stats where info = "confidence" and stat = "std") confstd ' \
                'ON s.fid = confstd.fid '\
                'LEFT JOIN '
                '(select fid, value from stats where info = "validity") valid ' \
                'ON s.fid = valid.fid '\
                'LEFT JOIN '
                '(select fid, value from stats where info = "classif" and class = 11) out11 '\
                'ON s.fid = out11.fid '\
                'LEFT JOIN '                   
                '(select fid, value from stats where info = "classif" and class = 12) out12 '\
                'ON s.fid = out12.fid '\
                'LEFT JOIN '
                '(select fid, value from stats where info = "classif" and class = 31) out31 '\
                'ON s.fid = out31.fid '\
                'LEFT JOIN '
                '(select fid, value from stats where info = "classif" and class = 32) out32 '\
                'ON s.fid = out32.fid '\
                'LEFT JOIN '
                '(select fid, value from stats where info = "classif" and class = 34) out34 '\
                'ON s.fid = out34.fid '\
                'LEFT JOIN '
                '(select fid, value from stats where info = "classif" and class = 36) out36 '\
                'ON s.fid = out36.fid '\
                'LEFT JOIN '
                '(select fid, value from stats where info = "classif" and class = 41) out41 '\
                'ON s.fid = out41.fid '\
                'LEFT JOIN '
                '(select fid, value from stats where info = "classif" and class = 42) out42 '\
                'ON s.fid = out42.fid '\
                'LEFT JOIN '                   
                '(select fid, value from stats where info = "classif" and class = 43) out43 '\
                'ON s.fid = out43.fid '\
                'LEFT JOIN '                   
                '(select fid, value from stats where info = "classif" and class = 44) out44 '\
                'ON s.fid = out44.fid '\
                'LEFT JOIN '                   
                '(select fid, value from stats where info = "classif" and class = 45) out45 '\
                'ON s.fid = out45.fid '\
                'LEFT JOIN '                   
                '(select fid, value from stats where info = "classif" and class = 46) out46 '\
                'ON s.fid = out46.fid '\
                'LEFT JOIN '                   
                '(select fid, value from stats where info = "classif" and class = 51) out51 '\
                'ON s.fid = out51.fid '\
                'LEFT JOIN '                   
                '(select fid, value from stats where info = "classif" and class = 53) out53 '\
                'ON s.fid = out53.fid '\
                'LEFT JOIN '                   
                '(select fid, value from stats where info = "classif" and class = 211) out211 '\
                'ON s.fid = out211.fid '\
                'LEFT JOIN '                   
                '(select fid, value from stats where info = "classif" and class = 221) out221 '\
                'ON s.fid = out221.fid '\
                'LEFT JOIN '                   
                '(select fid, value from stats where info = "classif" and class = 222) out222 '\
                'ON s.fid = out222.fid ')
        
    con.commit()
    con.close()


def joinShapeStats(shapefile, stats, tmp, outfile):

    layer = os.path.splitext(os.path.basename(shapefile))[0]
    tmpfile = os.path.join(tmp, 'tmp_%s.sqlite'%(layer))
    os.system('ogr2ogr -f SQLite %s %s -nln %s'%(tmpfile, shapefile, layer))

    database = db.connect(tmpfile)     
    cursor = database.cursor()
    cursor.execute("ATTACH '%s' as db;"%(stats))
    cursor.execute("create table stats as select * from db.statsfinal;")

    # get shapefile fid colname
    cursor.execute('select * from %s'%(layer))
    fieldnames=[f[0] for f in cursor.description]
    idcolname = fieldnames[0]

    cursor.execute("CREATE INDEX idx_shp ON %s(%s);"%(layer, idcolname))  
    cursor.execute("CREATE INDEX idx_stats ON %s(%s);"%('stats', 'fid'))  

    cursor.execute("create view datajoin as SELECT * FROM %s LEFT JOIN stats ON %s.%s = stats.fid;"%(layer, layer, idcolname))
    
    database.commit()
    database.close()

    outfiletmp = os.path.splitext(outfile)[0] + '_tmp.shp'
    os.system('ogr2ogr -f "ESRI Shapefile" -sql "select * from datajoin" %s %s -nln %s'%(outfiletmp, tmpfile, layer))

    layerout = os.path.splitext(os.path.basename(outfiletmp))[0]
    command = "ogr2ogr -q -f 'ESRI Shapefile' -overwrite -sql "\
              "'SELECT CAST(class AS INTEGER(4)) AS Class, "\
              "CAST(validity AS INTEGER(4)) AS Validity, "\
              "CAST(mconf AS NUMERIC(6,2)) AS MoyConf, "\
              "CAST(stdconf AS NUMERIC(6,2)) AS StdConf, "\
              "CAST(Ete AS NUMERIC(6,2)) AS Ete, "\
              "CAST(Hiver AS NUMERIC(6,2)) AS Hiver, "\
              "CAST(Feuillus AS NUMERIC(6,2)) AS Feuillus, "\
              "CAST(Coniferes AS NUMERIC(6,2)) AS Coniferes, "\
              "CAST(Pelouse AS NUMERIC(6,2)) AS Pelouse, "\
              "CAST(Landes AS NUMERIC(6,2)) AS Landes, "\
              "CAST(UrbainDens AS NUMERIC(6,2)) AS UrbainDens, "\
              "CAST(UrbainDiff AS NUMERIC(6,2)) AS UrbainDiff, "\
              "CAST(ZoneIndCom AS NUMERIC(6,2)) AS ZoneIndCom, "\
              "CAST(Route AS NUMERIC(6,2)) AS Route, "\
              "CAST(PlageDune AS NUMERIC(6,2)) AS PlageDune, "\
              "CAST(SurfMin AS NUMERIC(6,2)) AS SurfMin, "\
              "CAST(Eau AS NUMERIC(6,2)) AS Eau, "\
              "CAST(GlaceNeige AS NUMERIC(6,2)) AS GlaceNeige, "\
              "CAST(Prairie AS NUMERIC(6,2)) AS Prairie, "\
              "CAST(Vergers AS NUMERIC(6,2)) AS Vergers, "\
              "CAST(Vignes AS NUMERIC(6,2)) AS Vignes, "\
              "CAST(Area AS NUMERIC(10,2)) AS Aire "\
              "FROM %s' "\
              "%s %s"%(layerout, outfile, outfiletmp)
    
    os.system(command)

    for ext in ['.dbf', '.shp', '.prj', '.shx']:
        os.remove(os.path.splitext(outfiletmp)[0] + ext)

    os.remove(stats)
        
def computeStats(shapefile, csv, tmp, output):

    tmpsqlite = os.path.splitext(csv)[0] + '.sqlite'
    if os.path.exists(tmpsqlite):
        os.remove(tmpsqlite)
       
    importstats(csv, tmpsqlite)
    pivotstats(tmpsqlite)
    joinShapeStats(shapefile, tmpsqlite, tmp, output)

    
if __name__ == "__main__":
    if len(sys.argv) == 1:
	prog = os.path.basename(sys.argv[0])
	print '      '+sys.argv[0]+' [options]' 
	print "     Help : ", prog, " --help"
	print "        or : ", prog, " -h"
	sys.exit(-1)  
    else:
	usage = "usage: %prog [options] "
	parser = argparse.ArgumentParser(description = "Join stats list to shapefile")
        parser.add_argument("-shape", dest="shape", action="store", \
                            help="vector file of landcover (shapefile)", required = True)
        parser.add_argument("-stats", dest="stats", action="store", \
                            help="stats file (csv)", required = True)
        parser.add_argument("-tmp", dest="tmp", action="store", \
                            help="tmp folder", required = True)
        parser.add_argument("-output", dest="output", action="store", \
                            help="output path", required = True) 
        args = parser.parse_args()

        if not os.path.exists(args.output):
            computeStats(args.shape, args.stats, args.tmp, args.output)
        else:
            print "Output file '%s' already exists, please delete it or change output path"%(args.output)
            sys.exit()


            
