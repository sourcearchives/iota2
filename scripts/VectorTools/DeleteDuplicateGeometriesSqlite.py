#!/usr/bin/python
#-*- coding: utf-8 -*-

import sys
import os
import sqlite3 as lite
import argparse

def deleteDuplicateGeometriesSqlite(shapefile):

    tmpnamelyr = "tmp" + os.path.splitext(os.path.basename(shapefile))[0]
    tmpname = "%s.sqlite"%(tmpnamelyr)
    outsqlite = os.path.join(os.path.dirname(shapefile), tmpname)
    os.system("ogr2ogr -f SQLite %s %s -nln tmp"%(outsqlite, shapefile))

    conn = lite.connect(outsqlite)
    cursor = conn.cursor()

    cursor.execute("select count(*) from tmp")
    nbfeat0 = cursor.fetchall()
    
    cursor.execute("create temporary table to_del (ogc_fid int, geom blob);")
    cursor.execute("insert into to_del(ogc_fid, geom) select min(ogc_fid), GEOMETRY from tmp group by GEOMETRY having count(*) > 1;")
    cursor.execute("delete from tmp where exists(select * from to_del where to_del.geom = tmp.GEOMETRY and to_del.ogc_fid <> tmp.ogc_fid);")

    cursor.execute("select count(*) from tmp")
    nbfeat1 = cursor.fetchall()

    conn.commit()
    
    os.system("rm %s"%(shapefile))
    os.system("ogr2ogr -f 'ESRI Shapefile' %s %s"%(shapefile, outsqlite))

    if int(nbfeat0[0][0]) - int(nbfeat1[0][0]) != 0:
        print "Analyse of duplicated features done. %s duplicates found and deleted"%(int(nbfeat0[0][0]) - int(nbfeat1[0][0]))
    else:
        print "Analyse of duplicated features done. No duplicates found"
        
    cursor = conn = None

    os.remove(outsqlite)

if __name__ == "__main__":
    if len(sys.argv) == 1:
	prog = os.path.basename(sys.argv[0])
	print '      '+sys.argv[0]+' [options]' 
	print "     Help : ", prog, " --help"
	print "        or : ", prog, " -h"
	sys.exit(-1)  
 
    else:
	usage = "usage: %prog [options] "
	parser = argparse.ArgumentParser(description = "Find geometries duplicates based on sqlite method")
        
        parser.add_argument("-in", dest="inshape", action="store", \
                            help="Input shapefile to analyse", required = True)
                                  
        args = parser.parse_args()

        deleteDuplicateGeometriesSqlite(args.inshape)
