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
    """ Get the table containing the useful data """
    defaulttables = ['geometry_columns', 'spatial_ref_sys', 'sqlite_sequence']
    connfile = lite.connect(sqlitefile)
    cursorfile = connfile.cursor()
    cursorfile.execute("SELECT name FROM sqlite_master WHERE type='table';")
    table = [x[0] for x in cursorfile.fetchall() if x[0] not in defaulttables]
    cursorfile = connfile = None
    
    return table[0]

def rename_field(field, pattern="", index=0):
    """ rename field ad pattern_index """
    if(field[:len(pattern)] != pattern or pattern==""):
       return field
    else:
       return pattern+'_'+str(index)

def build_fields_to_select(base_fields, fieldsnames, dfield, renaming, renaming_index):
    """ builds the association between the fields in the files and the new
    names for the joined file"""
    fields_as = [dfield+' AS '+dfield]
    if renaming is not None:
        (rename_pat, rename_off) = renaming
        fields_as += [fn+' AS '+rename_field(fn,rename_pat,rename_off+idx+renaming_index)
                      for (fn,idx) in zip(fieldsnames,range(len(fieldsnames)))]
        final_fields = ['datatojoin.'+rename_field(fn,rename_pat,rename_off+idx+renaming_index)
                        for (fn,idx) in zip(fieldsnames,range(len(fieldsnames)))]
        renaming_index += len(fieldsnames)
    else:
        fields_as += [fn+' AS '+fn+'_'+str(renaming_index) for fn in fieldsnames]
        final_fields = ['datatojoin.'+fn+'_'+str(renaming_index) for fn in fieldsnames]
    fields_as = string.join(fields_as,', ')
    final_fields = base_fields+', '+string.join(final_fields, ', ')
    return (fields_as, final_fields, renaming_index)

def join_sqlites(basefile, sqlites, ofield, fieldsnames = None, dfield=None,
                 renaming=None):
    """Update a base sqlite file by adding columns coming from other
    sqlite files. The join of the files is done using ofield from the
    base file and dfield from the other files. fieldsnames is the list
    of the fields to copy to the base file from the others. We assume
    that these are the same names for all the secondary files. These
    fields are renamed by adding '_N' to the original field name, with
    N=0 for the first secondary file, N=1 for the second, etc. If
    provided, triple (string, int) used to rename the fields which are
    suposed to match the pattern "string_value". They will be renamed
    increasing the value starting from the provided int.

    For example, if the fields follow the pattern value_x value_y
    value_z and renaming is ('value', 11), they will be renamed as
    value_11 value_12 value_13,etc.

    """

    if dfield is None:
        dfield = ofield
    conn = lite.connect(basefile)
    cursor = conn.cursor()
    tablebase = get_sqlite_table(basefile)
    addindex = "CREATE INDEX idx ON [%s](%s);"%(tablebase, ofield)
    cursor.execute(addindex)
    renaming_index = 0
    for (filesqlite, fid) in zip(sqlites, range(len(sqlites))):
        if os.path.exists(filesqlite):
            base_fields = ["[%s]."%(tablebase)+d[0] 
                           for d in 
                           cursor.execute("SELECT * FROM [%s]"%(tablebase)).description]
            base_fields = string.join(base_fields,', ')
            db_name = 'db_'+str(fid)
            fields_as = "*"
            final_fields = "*"
            if fieldsnames is not None:
                (fields_as, 
                 final_fields, 
                 renaming_index) = build_fields_to_select(base_fields, 
                                                          fieldsnames, dfield, 
                                                          renaming, renaming_index)
            table = get_sqlite_table(filesqlite)
            cursor.execute("ATTACH '%s' as %s;"%(filesqlite,db_name))
            selection = """CREATE TABLE datatojoin AS 
                           SELECT %s FROM  %s.[%s];"""%(fields_as,db_name,table)
            cursor.execute(selection)
            AddIndex = "CREATE INDEX idx_table ON datatojoin(%s);"%(dfield)  
            cursor.execute(AddIndex)
            # Join shapefile and stats tables
            sqljoin = """create table datajoin as 
                         SELECT %s FROM [%s] LEFT JOIN datatojoin ON 
                         [%s].%s = datatojoin.%s;"""%(final_fields,tablebase, 
                                                      tablebase, ofield, dfield)
            cursor.execute(sqljoin)
            cursor.execute("DROP TABLE [%s];"%(tablebase))
            cursor.execute("ALTER TABLE datajoin RENAME TO [%s];"%(tablebase))
            cursor.execute("DROP TABLE datatojoin;")
            cursor.execute("DETACH '%s';"%(db_name))
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

        join_sqlites(ARGS.base, ARGS.sqlites, ARGS.ofield, ARGS.fieldsn, ARGS.dfield)
