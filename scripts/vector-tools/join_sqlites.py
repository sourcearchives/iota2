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

import sqlite3 as lite
import sys
import os
import argparse

def gettablesqlite(sqlitefile):

    defaulttables = ['geometry_columns', 'spatial_ref_sys', 'sqlite_sequence']
    connfile = lite.connect(sqlitefile)
    cursorfile = connfile.cursor()
    cursorfile.execute("SELECT name FROM sqlite_master WHERE type='table';")
    table = [x[0] for x in cursorfile.fetchall() if x[0] not in defaulttables]
    cursorfile = connfile = None
    
    return table[0]

def joinsqlites(basefile, ofield, dfield, sqlites, nfields='', fieldsnames = ''):

    conn = lite.connect(basefile)
    cursor = conn.cursor()
    tablebase = gettablesqlite(basefile)
    addindex = "CREATE INDEX idx ON [%s](%s);"%(tablebase, ofield)
    cursor.execute(addindex)

    for filesqlite in sqlites:
        if os.path.exists(filesqlite):
            table = gettablesqlite(filesqlite)
   
            cursor.execute("ATTACH '%s' as db;"%(filesqlite))
            cursor.execute("CREATE TABLE datatojoin AS SELECT * FROM db.[%s];"%(table))
            AddIndex = "CREATE INDEX idx_table ON datatojoin(%s);"%(dfield)  
            cursor.execute(AddIndex)
            
            # Join shapefile and stats tables
            sqljoin = "create table datajoin as SELECT * FROM [%s] LEFT JOIN datatojoin ON [%s].%s = datatojoin.%s;"%(tablebase, tablebase, ofield, dfield)
            cursor.execute(sqljoin)
            cursor.execute("DROP TABLE [%s];"%(tablebase))
            cursor.execute("ALTER TABLE datajoin RENAME TO [%s];"%(tablebase))
            cursor.execute("DROP TABLE datatojoin;")

            
        else:
            print filesqlite + "does not exist. skip file."


if __name__ == "__main__":
    if len(sys.argv) == 1:
        PROG = os.path.basename(sys.argv[0])
        print '      '+sys.argv[0]+' [options]'
        print "     Help : ", PROG, " --help"
        print "        or : ", PROG, " -h"
        sys.exit(-1)
    else:
        USAGE = "usage: %prog [options] "
        PARSER = argparse.ArgumentParser(description="Join sqlite files")
        PARSER.add_argument("-base", dest="base", action="store",\
                            help="Base sqlite file from which sqlite files are joined",\
                            required=True)
        PARSER.add_argument("-ofield", dest="ofield", action="store",\
                            help="field name of base file to join tables ()", required=True)
        PARSER.add_argument("-dfield", dest="dfield", action="store",\
                            help="field name of joined files to join tables ()", required=True)
        PARSER.add_argument("-sqlites", dest="sqlites", nargs="+",\
                            help="List of sqlite files to join", required=True)
        PARSER.add_argument("-nfield", dest="nfield", nargs="+",\
                            help="Field indexes to keep in joined files")
        PARSER.add_argument("-fields.names", dest="fieldsn", nargs="+",\
                            help="Field indexes to keep in joined files")        
        ARGS = PARSER.parse_args()

        joinsqlites(ARGS.base, ARGS.ofield, ARGS.dfield, ARGS.sqlites, ARGS.nfield, ARGS.fieldsn)
