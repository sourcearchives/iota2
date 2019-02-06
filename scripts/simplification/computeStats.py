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
import time
import csv
import sqlite3
from zipfile import ZipFile
from pyspatialite import dbapi2 as db
import logging
logger = logging.getLogger(__name__)

try:
    from Common import Utils
except ImportError:
    raise ImportError('Iota2 not well configured / installed')
    
def importstats(csvstore, sqlite):

    print sqlite
    con = sqlite3.connect(sqlite)
    cur = con.cursor()
    cur.execute("CREATE TABLE stats (idstats integer, info text, stat text, class integer, value real);")
    
    with open(csvstore, 'rb') as f:
        reader = csv.reader(f)
        cur = con.cursor()
        cur.executemany("INSERT INTO stats(idstats, info, stat, class, value) VALUES (?, ?, ?, ?, ?);", reader)        
        con.commit()
        con.close()

def getStatsList(path):

    listcsv = []
    for root, dirs, files in os.walk(path):
        for filein in files:
            if "stats" in filein:
                listcsv.append(os.path.join(root, filein))    
    
    return listcsv

def manageClassName(nomenclature):

    exp2 = exp3 = ""
    exp = []
    with open(nomenclature, 'r') as f:
        for line in f.readlines():
            line = line.strip().rstrip('\r\n')
            if int(line.split(":")[1]) != 255:
                exp.append("COALESCE(CAST(ROUND(out%s.value, %s) AS FLOAT),0) AS %s "%(line.split(":")[1], line.split(":")[1], line.split(":")[2]))
                exp2 += 'LEFT JOIN (select idstats, value from stats where info = "classif" and class = %s) out%s ON s.idstats = out%s.idstats '%(line.split(":")[1], line.split(":")[1], line.split(":")[1])
                exp3 += "CAST(%s AS NUMERIC(6,2)) AS %s, "%(line.split(":")[2], line.split(":")[2])
        
    return ",".join(exp), exp2, exp3

def pivotstatsdyn(sqlite, nomenclature):

    exp1, exp2, exp3 = manageClassName(nomenclature)
    
    con = sqlite3.connect(sqlite)
    cur = con.cursor()
    # Pivot statistics table
    cur.execute('CREATE TABLE statsfinal AS '\
                'SELECT s.idstats + 1 as idstats, '\
                'confmean.value as mconf, '\
                'validmean.value as valmean, '\
                'validstd.value as valstd, %s'\
                'FROM '\
                '(SELECT '\
                'idstats '\
                'FROM stats '\
                'GROUP BY idstats '\
                'ORDER BY idstats) s ' \
                'LEFT JOIN '
                '(select idstats, value from stats where info = "confidence" and stat = "mean") confmean ' \
                'ON s.idstats = confmean.idstats '\
                'LEFT JOIN '
                '(select idstats, value from stats where info = "validity" and stat = "mean") validmean ' \
                'ON s.idstats = validmean.idstats '\
                'LEFT JOIN '
                '(select idstats, value from stats where info = "validity" and stat = "std") validstd ' \
                'ON s.idstats = validstd.idstats %s'%(exp1, exp2))
            
def pivotstats(sqlite):

    con = sqlite3.connect(sqlite)
    cur = con.cursor()
    # Pivot statistics table
    cur.execute('CREATE TABLE statsfinal AS '\
                'SELECT s.idstats + 1 as idstats, '\
                'confmean.value as mconf, '\
                'validmean.value as valmean, '\
                'validstd.value as valstd, '\
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
                'idstats '\
                'FROM stats '\
                'GROUP BY idstats '\
                'ORDER BY idstats) s ' \
                'LEFT JOIN '
                '(select idstats, value from stats where info = "confidence" and stat = "mean") confmean ' \
                'ON s.idstats = confmean.idstats '\
                'LEFT JOIN '
                '(select idstats, value from stats where info = "validity" and stat = "mean") validmean ' \
                'ON s.idstats = validmean.idstats '\
                'LEFT JOIN '
                '(select idstats, value from stats where info = "validity" and stat = "std") validstd ' \
                'ON s.idstats = validstd.idstats '\
                'LEFT JOIN '
                '(select idstats, value from stats where info = "classif" and class = 11) out11 '\
                'ON s.idstats = out11.idstats '\
                'LEFT JOIN '                   
                '(select idstats, value from stats where info = "classif" and class = 12) out12 '\
                'ON s.idstats = out12.idstats '\
                'LEFT JOIN '
                '(select idstats, value from stats where info = "classif" and class = 31) out31 '\
                'ON s.idstats = out31.idstats '\
                'LEFT JOIN '
                '(select idstats, value from stats where info = "classif" and class = 32) out32 '\
                'ON s.idstats = out32.idstats '\
                'LEFT JOIN '
                '(select idstats, value from stats where info = "classif" and class = 34) out34 '\
                'ON s.idstats = out34.idstats '\
                'LEFT JOIN '
                '(select idstats, value from stats where info = "classif" and class = 36) out36 '\
                'ON s.idstats = out36.idstats '\
                'LEFT JOIN '
                '(select idstats, value from stats where info = "classif" and class = 41) out41 '\
                'ON s.idstats = out41.idstats '\
                'LEFT JOIN '
                '(select idstats, value from stats where info = "classif" and class = 42) out42 '\
                'ON s.idstats = out42.idstats '\
                'LEFT JOIN '                   
                '(select idstats, value from stats where info = "classif" and class = 43) out43 '\
                'ON s.idstats = out43.idstats '\
                'LEFT JOIN '                   
                '(select idstats, value from stats where info = "classif" and class = 44) out44 '\
                'ON s.idstats = out44.idstats '\
                'LEFT JOIN '                   
                '(select idstats, value from stats where info = "classif" and class = 45) out45 '\
                'ON s.idstats = out45.idstats '\
                'LEFT JOIN '                   
                '(select idstats, value from stats where info = "classif" and class = 46) out46 '\
                'ON s.idstats = out46.idstats '\
                'LEFT JOIN '                   
                '(select idstats, value from stats where info = "classif" and class = 51) out51 '\
                'ON s.idstats = out51.idstats '\
                'LEFT JOIN '                   
                '(select idstats, value from stats where info = "classif" and class = 53) out53 '\
                'ON s.idstats = out53.idstats '\
                'LEFT JOIN '                   
                '(select idstats, value from stats where info = "classif" and class = 211) out211 '\
                'ON s.idstats = out211.idstats '\
                'LEFT JOIN '                   
                '(select idstats, value from stats where info = "classif" and class = 221) out221 '\
                'ON s.idstats = out221.idstats '\
                'LEFT JOIN '                   
                '(select idstats, value from stats where info = "classif" and class = 222) out222 '\
                'ON s.idstats = out222.idstats ')
        
    con.commit()
    con.close()

def pivotstats23(sqlite):

    con = sqlite3.connect(sqlite)
    cur = con.cursor()
    # Pivot statistics table
    cur.execute('CREATE TABLE statsfinal AS '\
                'SELECT s.idstats + 1 as idstats, '\
                'confmean.value as mconf, '\
                'validmean.value as valmean, '\
                'validstd.value as valstd, '\
                'COALESCE(CAST(ROUND(out1.value, 1) AS FLOAT),0) AS UrbainDens, '\
                'COALESCE(CAST(ROUND(out2.value, 2) AS FLOAT),0) AS UrbainDiff, '\
                'COALESCE(CAST(ROUND(out3.value, 3) AS FLOAT),0) AS ZoneIndCom, '\
                'COALESCE(CAST(ROUND(out4.value, 4) AS FLOAT),0) AS Route, '\
                'COALESCE(CAST(ROUND(out5.value, 5) AS FLOAT),0) AS Colza, '\
                'COALESCE(CAST(ROUND(out6.value, 6) AS FLOAT),0) AS CerealPail, '\
                'COALESCE(CAST(ROUND(out7.value, 7) AS FLOAT),0) AS Proteagine, '\
                'COALESCE(CAST(ROUND(out8.value, 8) AS FLOAT),0) AS Soja, '\
                'COALESCE(CAST(ROUND(out9.value, 9) AS FLOAT),0) AS Tournesol, '\
                'COALESCE(CAST(ROUND(out10.value, 10) AS FLOAT),0) AS Mais, '\
                'COALESCE(CAST(ROUND(out11.value, 11) AS FLOAT),0) AS Riz, '\
                'COALESCE(CAST(ROUND(out12.value, 12) AS FLOAT),0) AS TuberRacin, '\
                'COALESCE(CAST(ROUND(out13.value, 13) AS FLOAT),0) AS Prairie, '\
                'COALESCE(CAST(ROUND(out14.value, 14) AS FLOAT),0) AS Vergers, '\
                'COALESCE(CAST(ROUND(out15.value, 15) AS FLOAT),0) AS Vignes, '\
                'COALESCE(CAST(ROUND(out16.value, 16) AS FLOAT),0) AS Feuillus, '\
                'COALESCE(CAST(ROUND(out17.value, 17) AS FLOAT),0) AS Coniferes, '\
                'COALESCE(CAST(ROUND(out18.value, 18) AS FLOAT),0) AS Pelouse, '\
                'COALESCE(CAST(ROUND(out19.value, 19) AS FLOAT),0) AS Landes, '\
                'COALESCE(CAST(ROUND(out20.value, 20) AS FLOAT),0) AS SurfMin, '\
                'COALESCE(CAST(ROUND(out21.value, 21) AS FLOAT),0) AS PlageDune, '\
                'COALESCE(CAST(ROUND(out22.value, 22) AS FLOAT),0) AS GlaceNeige, '\
                'COALESCE(CAST(ROUND(out23.value, 23) AS FLOAT),0) AS Eau '\
                'FROM '\
                '(SELECT '\
                'idstats '\
                'FROM stats '\
                'GROUP BY idstats '\
                'ORDER BY idstats) s '\
                'LEFT JOIN '
                '(select idstats, value from stats where info = "confidence" and stat = "mean") confmean '\
                'ON s.idstats = confmean.idstats '\
                'LEFT JOIN '
                '(select idstats, value from stats where info = "validity" and stat = "mean") validmean '\
                'ON s.idstats = validmean.idstats '\
                'LEFT JOIN '
                '(select idstats, value from stats where info = "validity" and stat = "std") validstd '\
                'ON s.idstats = validstd.idstats '\
                'LEFT JOIN ' 
                '(select idstats, value from stats where info = "classif" and class = 1) out1 '\
                'ON s.idstats = out1.idstats '\
                'LEFT JOIN '
                '(select idstats, value from stats where info = "classif" and class = 2) out2 '\
                'ON s.idstats = out2.idstats '\
                'LEFT JOIN '
                '(select idstats, value from stats where info = "classif" and class = 3) out3 '\
                'ON s.idstats = out3.idstats '\
                'LEFT JOIN '
                '(select idstats, value from stats where info = "classif" and class = 4) out4 '\
                'ON s.idstats = out4.idstats '\
                'LEFT JOIN '
                '(select idstats, value from stats where info = "classif" and class = 5) out5 '\
                'ON s.idstats = out5.idstats '\
                'LEFT JOIN '
                '(select idstats, value from stats where info = "classif" and class = 6) out6 '\
                'ON s.idstats = out6.idstats '\
                'LEFT JOIN '
                '(select idstats, value from stats where info = "classif" and class = 7) out7 '\
                'ON s.idstats = out7.idstats '\
                'LEFT JOIN '
                '(select idstats, value from stats where info = "classif" and class = 8) out8 '\
                'ON s.idstats = out8.idstats '\
                'LEFT JOIN '
                '(select idstats, value from stats where info = "classif" and class = 9) out9 '\
                'ON s.idstats = out9.idstats '\
                'LEFT JOIN '
                '(select idstats, value from stats where info = "classif" and class = 10) out10 '\
                'ON s.idstats = out10.idstats '\
                'LEFT JOIN '
                '(select idstats, value from stats where info = "classif" and class = 11) out11 '\
                'ON s.idstats = out11.idstats '\
                'LEFT JOIN '
                '(select idstats, value from stats where info = "classif" and class = 12) out12 '\
                'ON s.idstats = out12.idstats '\
                'LEFT JOIN '
                '(select idstats, value from stats where info = "classif" and class = 13) out13 '\
                'ON s.idstats = out13.idstats '\
                'LEFT JOIN '
                '(select idstats, value from stats where info = "classif" and class = 14) out14 '\
                'ON s.idstats = out14.idstats '\
                'LEFT JOIN '
                '(select idstats, value from stats where info = "classif" and class = 15) out15 '\
                'ON s.idstats = out15.idstats '\
                'LEFT JOIN '
                '(select idstats, value from stats where info = "classif" and class = 16) out16 '\
                'ON s.idstats = out16.idstats '\
                'LEFT JOIN '
                '(select idstats, value from stats where info = "classif" and class = 17) out17 '\
                'ON s.idstats = out17.idstats '\
                'LEFT JOIN '
                '(select idstats, value from stats where info = "classif" and class = 18) out18 '\
                'ON s.idstats = out18.idstats '\
                'LEFT JOIN '
                '(select idstats, value from stats where info = "classif" and class = 19) out19 '\
                'ON s.idstats = out19.idstats '\
                'LEFT JOIN '
                '(select idstats, value from stats where info = "classif" and class = 20) out20 '\
                'ON s.idstats = out20.idstats '\
                'LEFT JOIN '
                '(select idstats, value from stats where info = "classif" and class = 21) out21 '\
                'ON s.idstats = out21.idstats '\
                'LEFT JOIN '
                '(select idstats, value from stats where info = "classif" and class = 22) out22 '\
                'ON s.idstats = out22.idstats '\
                'LEFT JOIN '
                '(select idstats, value from stats where info = "classif" and class = 23) out23 '\
                'ON s.idstats = out23.idstats ')
    
    con.commit()
    con.close()
    
#def joinShapeStats(shapefile, stats, tmp, outfile, nomenclature):
def joinShapeStats(shapefile, stats, tmp, outfile):    

    layer = os.path.splitext(os.path.basename(shapefile))[0]
    tmpfile = os.path.join(tmp, 'tmp_%s.sqlite'%(layer))
    Utils.run('ogr2ogr -f SQLite %s %s -nln %s'%(tmpfile, shapefile, layer))

    database = db.connect(tmpfile)     
    cursor = database.cursor()
    cursor.execute("ATTACH '%s' as db;"%(stats))
    cursor.execute("create table stats as select * from db.statsfinal;")

    # get shapefile fid colname
    cursor.execute('select * from %s'%(layer))
    fieldnames=[f[0] for f in cursor.description]
    idcolname = fieldnames[0]
    
    cursor.execute("CREATE INDEX idx_shp ON %s(%s);"%(layer, idcolname))  
    cursor.execute("CREATE INDEX idx_stats ON %s(%s);"%('stats', 'idstats'))  

    cursor.execute("create view datajoin as SELECT * FROM %s LEFT JOIN stats ON %s.%s = stats.idstats;"%(layer, layer, idcolname))
    
    database.commit()
    database.close()

    outfiletmp = os.path.join(tmp, os.path.splitext(os.path.basename(outfile))[0] + '_tmp.shp')
    Utils.run('ogr2ogr -f "ESRI Shapefile" -sql "select * from datajoin" %s %s -nln %s'%(outfiletmp, tmpfile, layer))

    #exp1, exp2, exp3 = manageClassName(nomenclature)
    
    layerout = os.path.splitext(os.path.basename(outfiletmp))[0]
    '''
    command = "ogr2ogr -overwrite -q -f 'ESRI Shapefile' -overwrite -sql "\
              "'SELECT CAST(class AS INTEGER(4)) AS Classe, "\
              "CAST(valmean AS INTEGER(4)) AS Validmean, "\
              "CAST(valstd AS NUMERIC(6,2)) AS Validstd, "\
              "CAST(mconf AS INTEGER(4)) AS Confidence, %s"\
              "CAST(Area AS NUMERIC(10,2)) AS Aire "\
              "FROM %s' "\
              "%s %s"%(exp3, layerout, outfile, outfiletmp)
    '''
    command = "ogr2ogr -overwrite -q -f 'ESRI Shapefile' -overwrite -sql "\
              "'SELECT CAST(class AS INTEGER(4)) AS Classe, "\
              "CAST(valmean AS INTEGER(4)) AS Validmean, "\
              "CAST(valstd AS NUMERIC(6,2)) AS Validstd, "\
              "CAST(mconf AS INTEGER(4)) AS Confidence, "\
              "CAST(Hiver AS NUMERIC(6,2)) AS Hiver, "\
              "CAST(Ete AS NUMERIC(6,2)) AS Ete, "\
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
    '''    
    command = "ogr2ogr -overwrite -q -f 'ESRI Shapefile' -overwrite -sql "\
              "'SELECT CAST(class AS INTEGER(4)) AS Classe, "\
              "CAST(valmean AS INTEGER(4)) AS Validmean, "\
              "CAST(valstd AS NUMERIC(6,2)) AS Validstd, "\
              "CAST(mconf AS INTEGER(4)) AS Confidence, "\
              "CAST(UrbainDens AS NUMERIC(6,2)) AS UrbainDens, "\
              "CAST(UrbainDiff AS NUMERIC(6,2)) AS UrbainDiff, "\
              "CAST(ZoneIndCom AS NUMERIC(6,2)) AS ZoneIndCom, "\
              "CAST(Route AS NUMERIC(6,2)) AS Route, "\
              "CAST(Colza AS NUMERIC(6,2)) AS Colza, "\
              "CAST(CerealPail AS NUMERIC(6,2)) AS CerealPail, "\
              "CAST(Proteagine AS NUMERIC(6,2)) AS Proteagine, "\
              "CAST(Soja AS NUMERIC(6,2)) AS Soja, "\
              "CAST(Tournesol AS NUMERIC(6,2)) AS Tournesol, "\
              "CAST(Mais AS NUMERIC(6,2)) AS Mais, "\
              "CAST(Riz AS NUMERIC(6,2)) AS Riz, "\
              "CAST(TuberRacin AS NUMERIC(6,2)) AS TuberRacin, "\
              "CAST(Prairie AS NUMERIC(6,2)) AS Prairie, "\
              "CAST(Vergers AS NUMERIC(6,2)) AS Vergers, "\
              "CAST(Vignes AS NUMERIC(6,2)) AS Vignes, "\
              "CAST(Feuillus AS NUMERIC(6,2)) AS Feuillus, "\
              "CAST(Coniferes AS NUMERIC(6,2)) AS Coniferes, "\
              "CAST(Pelouse AS NUMERIC(6,2)) AS Pelouse, "\
              "CAST(Landes AS NUMERIC(6,2)) AS Landes, "\
              "CAST(SurfMin AS NUMERIC(6,2)) AS SurfMin, "\
              "CAST(PlageDune AS NUMERIC(6,2)) AS PlageDune, "\
              "CAST(GlaceNeige AS NUMERIC(6,2)) AS GlaceNeige, "\
              "CAST(Eau AS NUMERIC(6,2)) AS Eau, "\
              "CAST(Area AS NUMERIC(10,2)) AS Aire "\
              "FROM %s' "\
              "%s %s"%(layerout, outfile, outfiletmp)
    '''
    Utils.run(command)

    for ext in ['.dbf', '.shp', '.prj', '.shx']:
        os.remove(os.path.splitext(outfiletmp)[0] + ext)
        
    os.remove(stats)
    os.remove(tmpfile)

def compressShape(shapefile, outzip):

    with ZipFile(outzip, 'w') as myzip:
        for ext in ['.shp', '.dbf', '.shx', '.prj']:
            myzip.write(os.path.splitext(shapefile)[0] + ext, os.path.basename(os.path.splitext(shapefile)[0] + ext))
        
#def computeStats(shapefile, csv, nomenclature, tmp, outzip = True, output = ""):
def computeStats(shapefile, csv, tmp, outzip = True, output = ""):
    
    idxval = os.path.splitext(csv)[0].split("_")[len(os.path.splitext(csv)[0].split("_")) - 1]
    shapefile = os.path.splitext(shapefile)[0] + str(idxval) + ".shp"
    output = shapefile

    begintime = time.time()
    tmpsqlite = os.path.join(tmp, os.path.splitext(os.path.basename(csv))[0] + '.sqlite')
    if os.path.exists(tmpsqlite):
        os.remove(tmpsqlite)

    importstats(csv, tmpsqlite)
    timeimport = time.time()
    logger.info(" ".join([" : ".join(["Statistics importation in sqlite database", str(round(timeimport - begintime, 2))]), "seconds"]))

    #pivotstats(tmpsqlite, nomenclature)
    pivotstats(tmpsqlite)
    

    timepivot = time.time()
    logger.info(" ".join([" : ".join(["Transpose statistics table", str(round(timepivot - timeimport, 2))]), "seconds"]))

    #joinShapeStats(shapefile, tmpsqlite, tmp, output, nomenclature)
    joinShapeStats(shapefile, tmpsqlite, tmp, output)    
    os.remove(csv)
    
    timejoin = time.time()
    logger.info(" ".join([" : ".join(["Join statistics and create final vector file", str(round(timejoin - timepivot, 2))]), "seconds"]))
    
    if outzip:
        outzip = os.path.splitext(output)[0] + '.zip'
        compressShape(output, outzip)
        for ext in ['.shp', '.dbf', '.shx', '.prj']: 
            os.remove(os.path.splitext(output)[0] + ext)

        timecompress = time.time()
        logger.info(" ".join([" : ".join(["Compression of vector file ", str(round(timecompress - timejoin, 2))]), "seconds"]))
    
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
        parser.add_argument("-nclture", dest="nclture", action="store", \
                            help="Nomenclature of the classification - (description:code:alias)")        
        parser.add_argument("-tmp", dest="tmp", action="store", \
                            help="tmp folder", required = True)
        parser.add_argument("-output", dest="output", action="store", \
                            help="output path")
        parser.add_argument("-dozip", action="store_true", \
                            help="Store shapefile in zip filme with the output name",  default = False)
        args = parser.parse_args()

        if not os.path.exists(args.output):
            #computeStats(args.shape, args.stats, args.nclture, args.tmp, args.dozip, args.output)
            computeStats(args.shape, args.stats, args.tmp, args.dozip, args.output)
        else:
            print "Output file '%s' already exists, please delete it or change output path"%(args.output)
            sys.exit()


            
