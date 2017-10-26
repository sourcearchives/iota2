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
import string

def get_sqlite_table(sqlitefile):

    defaulttables = ['geometry_columns', 'spatial_ref_sys', 'sqlite_sequence']
    connfile = lite.connect(sqlitefile)
    cursorfile = connfile.cursor()
    cursorfile.execute("SELECT name FROM sqlite_master WHERE type='table';")
    table = [x[0] for x in cursorfile.fetchall() if x[0] not in defaulttables]
    cursorfile = connfile = None
    
    return table[0]

def join_sqlites(basefile, ofield, dfield, sqlites, fieldsnames = None):
    
    if len(sqlites) > 10:
        """ Limitation of sqlite 
        OperationalError: too many attached databases - max 10
        """
        raise Exception("A maximum number of 10 files can be joint")
    conn = lite.connect(basefile)
    cursor = conn.cursor()
    tablebase = get_sqlite_table(basefile)
    addindex = "CREATE INDEX idx ON [%s](%s);"%(tablebase, ofield)
    cursor.execute(addindex)

    fields_for_join = '*'
    if fieldsnames is not None:
        fields_for_join = dfield+', '+string.join(fieldsnames, ', ')

    for (filesqlite, fid) in zip(sqlites, range(len(sqlites))):
        if os.path.exists(filesqlite):
            db_name = 'db_'+str(fid)
            table = get_sqlite_table(filesqlite)
            cursor.execute("ATTACH '%s' as %s;"%(filesqlite,db_name))
            cursor.execute("CREATE TABLE datatojoin AS SELECT "+fields_for_join+" FROM %s.[%s];"%(db_name,table))
            AddIndex = "CREATE INDEX idx_table ON datatojoin(%s);"%(dfield)  
            cursor.execute(AddIndex)
            
            # Join shapefile and stats tables
            sqljoin = "create table datajoin as SELECT * FROM [%s] LEFT JOIN datatojoin ON [%s].%s = datatojoin.%s;"%(tablebase, tablebase, ofield, dfield)
            cursor.execute(sqljoin)
            cursor.execute("DROP TABLE [%s];"%(tablebase))
            cursor.execute("ALTER TABLE datajoin RENAME TO [%s];"%(tablebase))
            cursor.execute("DROP TABLE datatojoin;")

            
        else:
            print filesqlite + "does not exist. Skipping file."


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
                            help="Base sqlite file to which other sqlite files are joined",\
                            required=True)
        PARSER.add_argument("-ofield", dest="ofield", action="store",\
                            help="field name of base file to join tables ()", required=True)
        PARSER.add_argument("-dfield", dest="dfield", action="store",\
                            help="field name of joined files to join tables ()", required=True)
        PARSER.add_argument("-sqlites", dest="sqlites", nargs="+",\
                            help="List of sqlite files to join", required=True)
        PARSER.add_argument("-fields.names", dest="fieldsn", nargs="+",\
                            help="Field indexes to copy from joined files")        
        ARGS = PARSER.parse_args()

        join_sqlites(ARGS.base, ARGS.ofield, ARGS.dfield, ARGS.sqlites, ARGS.fieldsn)
