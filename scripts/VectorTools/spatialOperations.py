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
import vector_functions as vf

def intersectSqlites(t1, t2, tmp, output, epsg, operation, keepfields, vectformat='SQLite'):
    """
    """
    from pyspatialite import dbapi2 as db
    tmpfile = []

    if not os.path.exists(tmp):
        print "Temporary folder '%s' does not exist, please create it"%(tmp)
        sys.exit()

    if os.path.exists(output):
        print "Outpout file %s already exists, please delete it"%(output)
        sys.exit()        

    if os.path.splitext(os.path.basename(t1))[1] == '.sqlite':        
        layert1 = vf.getLayerName(t1, "SQLite")
    elif os.path.splitext(os.path.basename(t1))[1] == '.shp':
        layert1 = vf.getLayerName(t1, "ESRI Shapefile")
    else:
        print "Type of vector file '%s' not supported"%(t1)
        sys.exit()

    if os.path.splitext(os.path.basename(t2))[1] == '.sqlite':        
        layert2 = vf.getLayerName(t2, "SQLite")
    elif os.path.splitext(os.path.basename(t2))[1] == '.shp':
        layert2 = vf.getLayerName(t2, "ESRI Shapefile")
    else:
        print "Type of vector file '%s' not supported"%(t2)
        sys.exit()
        
    layerout = os.path.splitext(os.path.basename(output))[0]
        
    if os.path.exists(os.path.join(tmp, 'tmp%s.sqlite'%(layerout))):
        os.remove(os.path.join(tmp, 'tmp%s.sqlite'%(layerout)))
        
    database = db.connect(os.path.join(tmp, 'tmp%s.sqlite'%(layerout)))
    cursor = database.cursor()
    cursor.execute('SELECT InitSpatialMetadata()')

    
    # Check if shapefile (and convert in sqlite) or sqlite inputs
    if os.path.splitext(os.path.basename(t1))[1] == '.sqlite':
        t1type = vf.getGeomType(t1, "SQLite")
        cursor.execute("ATTACH '%s' as db1;"%(t1))
    elif os.path.splitext(os.path.basename(t1))[1] == '.shp':
        t1type = vf.getGeomType(t1)
        t1sqlite = os.path.join(tmp, layert1 + '.sqlite')
        if os.path.exists(t1sqlite):
            os.remove(t1sqlite)
        os.system('ogr2ogr -f SQLite %s %s -nln %s'%(t1sqlite, t1, layert1))
        cursor.execute("ATTACH '%s' as db1;"%(t1sqlite))
        tmpfile.append(t1sqlite)
    else:
        print "Type of vector file '%s' not supported"%(t1)
        sys.exit()
        
    if os.path.splitext(os.path.basename(t2))[1] == '.sqlite':
        cursor.execute("ATTACH '%s' as db2;"%(t2))
        t2type = vf.getGeomType(t2, "SQLite")
    elif os.path.splitext(os.path.basename(t2))[1] == '.shp':
        t2type = vf.getGeomType(t2)
        t2sqlite = os.path.join(tmp, layert2 + '.sqlite')
        if os.path.exists(t2sqlite):
            os.remove(t2sqlite)
        os.system('ogr2ogr -f SQLite %s %s -nln %s'%(t2sqlite, t2, layert2))
        cursor.execute("ATTACH '%s' as db2;"%(t2sqlite))
        tmpfile.append(t2sqlite)
    else:
        print "Type of vector file '%s' not supported"%(t2)
        sys.exit()

    # get fields list
    cursor.execute("create table tmpt1 as select * from db1.%s;"%(layert1))
    cursor.execute("pragma table_info(tmpt1)")

    listfieldst1 = []

    for field in cursor.fetchall():
        if keepfields:
            if field[2] != '' and field[1] in [x.lower() for x in keepfields]:
                listfieldst1.append((field[1],field[2]))
        else:
            if field[2] != '':
                listfieldst1.append((field[1],field[2]))

    cursor.execute("create table tmpt2 as select * from db2.%s;"%(layert2))
    cursor.execute("pragma table_info(tmpt2)")

    listfieldst2 = []
    for field in cursor.fetchall():
        if keepfields:
            if field[2] != '' and field[1] in [x.lower() for x in keepfields]:
                listfieldst2.append((field[1], field[2]))
        else:
            if field[2] != '':
                listfieldst2.append((field[1], field[2]))

    cursor.execute("drop table tmpt1")    
    cursor.execute("drop table tmpt2")
    cursor.execute('create table t1 (fid integer not null primary key autoincrement);')
    point1 = point2 = False
    if t1type in (3, 6, 1003, 1006):
        cursor.execute('select AddGeometryColumn("t1", "geometry", %s, "MULTIPOLYGON", 2)'%(epsg))
    elif t1type in (1, 4, 1001, 1004):
        cursor.execute('select AddGeometryColumn("t1", "geometry", %s, "MULTIPOINT", 2)'%(epsg))
        point1 = True
    else:
        print "Geometry type of file %s not handled"%(t1)
        
    listnamefieldst1 = []
    for field in listfieldst1:
        try:
            cursor.execute("ALTER TABLE t1 ADD COLUMN %s %s;"%(field[0], field[1]))
            listnamefieldst1.append(field[0])
        except:
            print "Column '%s' already exists, not added"%(field[0])
            continue
    cursor.execute('create table t2 (fid integer not null primary key autoincrement);')
    if t2type in (3, 6, 1003, 1006):
        cursor.execute('select AddGeometryColumn("t2", "geometry", %s, "MULTIPOLYGON", 2)'%(epsg))
    elif t2type in (1, 4, 1001, 1004):
        cursor.execute('select AddGeometryColumn("t2", "geometry", %s, "MULTIPOINT", 2)'%(epsg))
        point2 = True        
    else:
        print "Geometry type of file %s not handled"%(t2)
        
    listnamefieldst2 = []
    for field in listfieldst2:
        try:
            cursor.execute("ALTER TABLE t2 ADD COLUMN %s %s;"%(field[0], field[1]))
            listnamefieldst2.append(field[0])
        except:
            print "Column '%s' already exists, not added"%(field[0])
            continue
    if listnamefieldst1:
        if not point1:
            cursor.execute("insert into t1(%s, geometry) "\
                           "select %s, CastToMultiPolygon(geomfromwkb(geometry, %s)) as geometry from db1.%s;"%(", ".join(listnamefieldst1), \
                                                                                                                ", ".join(listnamefieldst1), \
                                                                                                                epsg, \
                                                                                                                layert1))
        else:
            cursor.execute("insert into t1(%s, geometry) "\
                           "select %s, CastToMultiPoint(geomfromwkb(geometry, %s)) as geometry from db1.%s;"%(", ".join(listnamefieldst1), \
                                                                                                              ", ".join(listnamefieldst1), \
                                                                                                              epsg, \
                                                                                                              layert1))            
    else:
        if not point1:
            cursor.execute("insert into t1(geometry) "\
                           "select CastToMultiPolygon(geomfromwkb(geometry, %s)) as geometry from db1.%s;"%(epsg, \
                                                                                                            layert1))
        else:
            cursor.execute("insert into t1(geometry) "\
                           "select CastToMultiPoint(geomfromwkb(geometry, %s)) as geometry from db1.%s;"%(epsg, \
                                                                                                          layert1))            
    if listnamefieldst2:
        if not point2:
            cursor.execute("insert into t2(%s, geometry) "\
                           "select %s, CastToMultiPolygon(geomfromwkb(geometry, %s)) as geometry from db2.%s;"%(", ".join(listnamefieldst2), \
                                                                                                                ", ".join(listnamefieldst2), \
                                                                                                                epsg, \
                                                                                                                layert2))
        else:
            cursor.execute("insert into t2(%s, geometry) "\
                           "select %s, CastToMultiPoint(geomfromwkb(geometry, %s)) as geometry from db2.%s;"%(", ".join(listnamefieldst2), \
                                                                                                              ", ".join(listnamefieldst2), \
                                                                                                              epsg, \
                                                                                                              layert2))
    else:
        if not point2:
            cursor.execute("insert into t2(geometry) "\
                           "select CastToMultiPolygon(geomfromwkb(geometry, %s)) as geometry from db2.%s;"%(epsg, \
                                                                                                            layert2))
        else:
            cursor.execute("insert into t2(geometry) "\
                           "select CastToMultiPoint(geomfromwkb(geometry, %s)) as geometry from db2.%s;"%(epsg, \
                                                                                                          layert2))
            
    duplicates = set(listnamefieldst1) & set(listnamefieldst2)
    for namefield1 in listnamefieldst1:
        if namefield1 in duplicates:
            listnamefieldst1[listnamefieldst1.index(namefield1)] = "t1." +  str(namefield1) + " as " + "t1_" + str(namefield1)
        else:
            listnamefieldst1[listnamefieldst1.index(namefield1)] = "t1." +  str(namefield1)

    for namefield2 in listnamefieldst2:
        if namefield2 in duplicates:
            listnamefieldst2[listnamefieldst2.index(namefield2)] = "t2." +  str(namefield2) + " as " + "t2_" + str(namefield2)
        else:
            listnamefieldst2[listnamefieldst2.index(namefield2)] = "t2." +  str(namefield2)

    cursor.execute("select CreateSpatialIndex('t1', 'geometry');")
    cursor.execute("select CreateSpatialIndex('t2', 'geometry');")
    listnamefinal = listnamefieldst1 + listnamefieldst2
    if listnamefinal:
        if point1 or point2:
            cursor.execute("CREATE TABLE '%s' AS SELECT %s, CastToMultiPoint(ST_Multi(ST_%s(t1.geometry, t2.geometry))) AS 'geometry' "\
                           "FROM t1, t2 WHERE ST_Intersects(t1.geometry, t2.geometry) and "\
                           "IsValid(CastToMultiPoint(ST_Multi(ST_%s(t1.geometry, t2.geometry))));"%(layerout, \
                                                                                                    ", ".join(listnamefinal), \
                                                                                                    operation, \
                                                                                                    operation))
        else:
            cursor.execute("CREATE TABLE '%s' AS SELECT %s, CastToMultiPolygon(ST_Multi(ST_%s(t1.geometry, t2.geometry))) AS 'geometry' "\
                           "FROM t1, t2 WHERE ST_Intersects(t1.geometry, t2.geometry) and "\
                           "IsValid(CastToMultiPolygon(ST_Multi(ST_%s(t1.geometry, t2.geometry))));"%(layerout, \
                                                                                                      ", ".join(listnamefinal), \
                                                                                                      operation, \
                                                                                                      operation))
            
    else:
        if point1 or point2:        
            cursor.execute("CREATE TABLE '%s' AS SELECT CastToMultiPoint(ST_Multi(ST_%s(t1.geometry, t2.geometry))) AS 'geometry' "\
                           "FROM t1, t2 WHERE ST_Intersects(t1.geometry, t2.geometry) and "\
                           "IsValid(CastToMultiPoint(ST_Multi(ST_%s(t1.geometry, t2.geometry))));"%(layerout,
                                                                                                    operation,
                                                                                                    operation))
        else:
            cursor.execute("CREATE TABLE '%s' AS SELECT CastToMultiPolygon(ST_Multi(ST_%s(t1.geometry, t2.geometry))) AS 'geometry' "\
                           "FROM t1, t2 WHERE ST_Intersects(t1.geometry, t2.geometry) and "\
                           "IsValid(CastToMultiPolygon(ST_Multi(ST_%s(t1.geometry, t2.geometry))));"%(layerout,
                                                                                                      operation,
                                                                                                      operation))
            
    database.commit()
    

    if os.path.splitext(os.path.basename(output))[1] == '.shp' and vectformat == 'SQLite':
        vectformat = "ESRI Shapefile"

    cursor.execute("pragma table_info({})".format(layerout))
    cursor.execute("select * from {} limit 1".format(layerout))
    nb_features = cursor.fetchall()
    
    #check if there is intersection, if not return False and remove tmp files
    if not len(nb_features) > 0:
        os.remove(os.path.join(tmp, 'tmp%s.sqlite'%(layerout)))
        for files in tmpfile:
            os.remove(files)
        return False

    database = cursor = None
    if point1 or point2:        
        os.system('ogr2ogr -explodecollections -nlt POINT -f "%s" -sql "select * from %s" %s %s -nln %s'%(vectformat,
                                                                                                            layerout,
                                                                                                            output,
                                                                                                            os.path.join(tmp, 'tmp%s.sqlite'%(layerout)),
                                                                                                            layerout))
    else:
        os.system('ogr2ogr -explodecollections -nlt POLYGON -f "%s" -sql "select * from %s" %s %s -nln %s'%(vectformat,
                                                                                                            layerout,
                                                                                                            output,
                                                                                                            os.path.join(tmp, 'tmp%s.sqlite'%(layerout)),
                                                                                                            layerout))

    os.remove(os.path.join(tmp, 'tmp%s.sqlite'%(layerout)))
    for files in tmpfile:
        os.remove(files)
    return True

if __name__ == "__main__":
    if len(sys.argv) == 1:
	prog = os.path.basename(sys.argv[0])
	print '      '+sys.argv[0]+' [options]' 
	print "     Help : ", prog, " --help"
	print "        or : ", prog, " -h"
	sys.exit(-1)  
    else:
	usage = "usage: %prog [options] "
	parser = argparse.ArgumentParser(description = "Execute spatial operation (intersection or difference or union) "\
                                         "on two vector files (ESRI Shapefile or sqlite formats)")
        parser.add_argument("-s1", dest="s1", action="store", \
                            help="first sqlite vector file", required = True)
        parser.add_argument("-s2", dest="s2", action="store", \
                            help="second sqlite vector file", required = True)
        parser.add_argument("-tmp", dest="tmp", action="store", \
                            help="tmp folder", required = True)
        parser.add_argument("-output", dest="output", action="store", \
                            help="output path", required = True) 
        parser.add_argument("-format", dest="outformat", action="store", \
                            help="OGR format (ogrinfo --formats). Default : SQLite ")
        parser.add_argument("-epsg", dest="epsg", action="store", \
                            help="EPSG code for projection. Default : 2154 - Lambert 93 ", type = int, default = 2154)        
        parser.add_argument("-operation", dest="operation", action="store", \
                            help="spatial operation (intersection or difference or union). Default : intersection", default = "intersection")          
        parser.add_argument("-keepfields", dest="keepfields", action="store", nargs="*", \
                            help="list of fields to keep in resulted vector file. Default : All fields")
        args = parser.parse_args()
        
        if args.operation not in ['intersection', 'difference', 'union']:
            raise Exception("Only Intersection, Difference and Union permitted as Spatial Operation")
        
        if args.outformat is None:
            intersectSqlites(args.s1, args.s2, args.tmp, args.output, args.epsg, args.operation, args.keepfields)
        else:
            intersectSqlites(args.s1, args.s2, args.tmp, args.output, args.epsg, args.operation, args.keepfields, args.outformat)

