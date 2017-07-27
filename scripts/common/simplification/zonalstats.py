#!/usr/bin/python
#-*- coding: utf-8 -*-
"""

"""

import sys
import os
import sqlite3 as lite
import argparse
import time
import math
 
class StdevFunc:
    def __init__(self):
        self.M = 0.0
        self.S = 0.0
        self.k = 1
 
    def step(self, value):
        if value is None:
            return
        tM = self.M
        self.M += (value - tM) / self.k
        self.S += (value - tM) * (value - self.M)
        self.k += 1
 
    def finalize(self):
        if self.k < 3:
            return None
        return math.sqrt(self.S / (self.k-2))

def convertShapefileinSqlite(shape, shapedb, layer):
    
    # convert shapefile to sqlite
    command = "ogr2ogr -f SQLite %s %s -nln %s"%(shapedb, shape, layer)
    os.system(command)

def cleanSqliteDatabase(db, table):

    conn = lite.connect(db)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    res = cursor.fetchall()
    res = [x[0] for x in res]
    if len(res) > 0:
        if table in res:
            cursor.execute("DROP TABLE %s;"%(table))

    cursor = conn = None

            
def test(path, shapefile, statsdb, shapedb, outshape):

    debut = time.time()

    if os.path.exists(shapedb):os.remove(shapedb)

    # If exists delete stats table
    cleanSqliteDatabase(statsdb, 'stats')
    cleanSqliteDatabase(statsdb, 'statsfinal')     

    # Connection to stats sqlite database
    conn = lite.connect(statsdb)
    
    # Add function stdev to sqlite database
    conn.create_aggregate("stdev", 1, StdevFunc)

    cursor = conn.cursor()
    
    # Compute statistics
    cursor.execute('CREATE TABLE stats AS SELECT stats.originfid, stats.class, CAST(stats.value_0 AS INTEGER) AS originclass, '\
                   'stats.mean_validity AS mean_validity, stats.std_validity AS std_validity, '\
                   'stats.mean_confidence AS mean_confidence, '\
                   '100 * CAST(stats.nb AS FLOAT) / totstats.tot AS rate '\
                   'from (select * , avg(value_1) AS mean_validity, count(value_2) AS nb, '\
                   'stdev(value_1) AS std_validity, avg(value_2) AS mean_confidence ' \
                   'FROM output '\
                   'GROUP BY originfid, value_0) stats '\
                   'INNER join '\
                   '(SELECT originfid, count(value_2) as tot FROM output GROUP BY originfid) totstats '\
                   'on stats.originfid = totstats.originfid')

    # Pivot statistics table
    cursor.execute('CREATE TABLE statsfinal AS '\
                   'SELECT s.originfid, '\
                   's.class as classe, '\
                   's.mean_validity as mean_valid, '\
                   'CAST(ROUND(COALESCE(s.std_validity, 0),2 ) AS FLOAT(5,2)) as std_valid, '\
                   's.confidence as confid, '\
                   'COALESCE(CAST(ROUND(out11.rate, 2) AS FLOAT),0) AS Ete, '\
                   'COALESCE(CAST(ROUND(out12.rate, 2) AS FLOAT),0) AS Hiver, '\
                   'COALESCE(CAST(ROUND(out31.rate, 2) AS FLOAT),0) AS Feuillus, '\
                   'COALESCE(CAST(ROUND(out32.rate, 2) AS FLOAT),0) AS Coniferes, '\
                   'COALESCE(CAST(ROUND(out34.rate, 2) AS FLOAT),0) AS Pelouse, '\
                   'COALESCE(CAST(ROUND(out36.rate, 2) AS FLOAT),0) AS Landes, '\
                   'COALESCE(CAST(ROUND(out41.rate, 2) AS FLOAT),0) AS UrbainDens, '\
                   'COALESCE(CAST(ROUND(out42.rate, 2) AS FLOAT),0) AS UrbainDiff, '\
                   'COALESCE(CAST(ROUND(out43.rate, 2) AS FLOAT),0) AS ZoneIndCom, '\
                   'COALESCE(CAST(ROUND(out44.rate, 2) AS FLOAT),0) AS Route, '\
                   'COALESCE(CAST(ROUND(out45.rate, 2) AS FLOAT),0) AS SurfMin, '\
                   'COALESCE(CAST(ROUND(out46.rate, 2) AS FLOAT),0) AS PlageDune, '\
                   'COALESCE(CAST(ROUND(out51.rate, 2) AS FLOAT),0) AS Eau, '\
                   'COALESCE(CAST(ROUND(out53.rate, 2) AS FLOAT),0) AS GlaceNeige, '\
                   'COALESCE(CAST(ROUND(out211.rate, 2) AS FLOAT),0) AS Prairie, '\
                   'COALESCE(CAST(ROUND(out221.rate, 2) AS FLOAT),0) AS Vergers, '\
                   'COALESCE(CAST(ROUND(out222.rate, 2) AS FLOAT),0) AS Vignes '\
                   'FROM '\
                   '(SELECT '\
                   'originfid AS originfid, '\
                   'class AS class, '\
                   'mean_validity AS mean_validity, '\
                   'std_validity AS std_validity, '\
                   'max(mean_confidence) AS confidence '\
                   'FROM stats '\
                   'GROUP BY originfid '\
                   'ORDER BY originfid) s ' \
                   'LEFT JOIN '
                   '(select originfid, rate AS rate FROM stats WHERE originclass = 11) out11 '\
                   'ON s.originfid = out11.originfid '\
                   'LEFT JOIN '                   
                   '(select originfid, rate AS rate FROM stats WHERE originclass = 12) out12 '\
                   'ON s.originfid = out12.originfid '\
                   'LEFT JOIN '
                   '(select originfid, rate AS rate FROM stats WHERE originclass = 31) out31 '\
                   'ON s.originfid = out31.originfid '\
                   'LEFT JOIN '
                   '(select originfid, rate AS rate FROM stats WHERE originclass = 32) out32 '\
                   'ON s.originfid = out32.originfid '\
                   'LEFT JOIN '
                   '(select originfid, rate AS rate FROM stats WHERE originclass = 34) out34 '\
                   'ON s.originfid = out34.originfid '\
                   'LEFT JOIN '
                   '(select originfid, rate AS rate FROM stats WHERE originclass = 36) out36 '\
                   'ON s.originfid = out36.originfid '\
                   'LEFT JOIN '
                   '(select originfid, rate AS rate FROM stats WHERE originclass = 41) out41 '\
                   'ON s.originfid = out41.originfid '\
                   'LEFT JOIN '
                   '(select originfid, rate AS rate FROM stats WHERE originclass = 42) out42 '\
                   'ON s.originfid = out42.originfid '\
                   'LEFT JOIN '                   
                   '(select originfid, rate AS rate FROM stats WHERE originclass = 43) out43 '\
                   'ON s.originfid = out43.originfid '\
                   'LEFT JOIN '                   
                   '(select originfid, rate AS rate FROM stats WHERE originclass = 44) out44 '\
                   'ON s.originfid = out44.originfid '\
                   'LEFT JOIN '                   
                   '(select originfid, rate AS rate FROM stats WHERE originclass = 45) out45 '\
                   'ON s.originfid = out45.originfid '\
                   'LEFT JOIN '                   
                   '(select originfid, rate AS rate FROM stats WHERE originclass = 46) out46 '\
                   'ON s.originfid = out46.originfid '\
                   'LEFT JOIN '                   
                   '(select originfid, rate AS rate FROM stats WHERE originclass = 51) out51 '\
                   'ON s.originfid = out51.originfid '\
                   'LEFT JOIN '                   
                   '(select originfid, rate AS rate FROM stats WHERE originclass = 53) out53 '\
                   'ON s.originfid = out53.originfid '\
                   'LEFT JOIN '                   
                   '(select originfid, rate AS rate FROM stats WHERE originclass = 221) out221 '\
                   'ON s.originfid = out221.originfid '\
                   'LEFT JOIN '                   
                   '(select originfid, rate AS rate FROM stats WHERE originclass = 222) out222 '\
                   'ON s.originfid = out222.originfid '\
                   'LEFT JOIN '                   
                   '(select originfid, rate AS rate FROM stats WHERE originclass = 211) out211 '\
                   'ON s.originfid = out211.originfid ')
  
    conn = cursor = None
    layer = os.path.splitext(os.path.basename(shapedb))[0]
    convertShapefileinSqlite(shapefile, shapedb, layer)

    # Connection to shapefile sqlite database
    conn = lite.connect(shapedb)

    # Create cursor
    cursor = conn.cursor()
    
    cursor.execute("ATTACH '%s' as db2;"%(statsdb))
    cursor.execute("CREATE TABLE stats AS SELECT * FROM db2.statsfinal;")

    # get shapefile fid colname
    cursor.execute('select * from %s'%(layer))
    fieldnames=[f[0] for f in cursor.description]
    idcolname = fieldnames[0]
                
    # Add index to shapefile table 
    AddIndex = "CREATE INDEX idx_shp ON %s(%s);"%(layer, idcolname)  
    cursor.execute(AddIndex)

    # Add index to stats table 
    AddIndex = "CREATE INDEX idx_stats ON stats(%s);"%('originfid')  
    cursor.execute(AddIndex)

    # Join shapefile and stats tables
    sqljoin = "create view datajoin as SELECT * FROM %s LEFT JOIN stats ON %s.%s = stats.originfid;"%(layer, layer, idcolname)
    cursor.execute(sqljoin)

    # Export all table to preserve field width
    command = "ogr2ogr -q -overwrite -sql 'SELECT * from datajoin' %s/shape_join.shp %s/%s.sqlite"%(path, path, layer)
    os.system(command)
    
    command = "ogr2ogr -q -f 'ESRI Shapefile' -overwrite -sql "\
              "'SELECT CAST(class AS INTEGER(4)) AS Class, "\
              "CAST(mean_valid AS INTEGER(4)) AS Validmean, "\
              "CAST(std_valid AS NUMERIC(6,2)) AS Validstd, "\
              "CAST(confid AS INTEGER(4)) AS Confidence, "\
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
              "CAST(Vignes AS NUMERIC(6,2)) AS Vignes FROM shape_join' "\
              "%s %s/shape_join.shp"%(os.path.join(path, outshape), path)
    
    os.system(command)
    
test('/home/vthierion/Documents/OSO/Dev/iota2/data/simplification/', \
     '/home/vthierion/Documents/OSO/Dev/iota2/data/simplification/vectors/classification.shp',\
     '/home/vthierion/Documents/OSO/Dev/iota2/data/simplification/sample_extraction.sqlite', \
     '/home/vthierion/Documents/OSO/Dev/iota2/data/simplification/shape.sqlite', \
     'classification.shp')
