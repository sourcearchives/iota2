#!/usr/bin/python
#-*- coding: utf-8 -*-

import sys
import os
import argparse
import ConditionalFieldRecode
import csv
import ogr

def harmonisationCodeIota(shapefile, csvfile, delimiter, fieldin, fieldout):

    with open(csvfile, 'rb') as csvfile:
        csvreader = csv.DictReader(csvfile, delimiter = delimiter)
        for row in csvreader:
            ConditionalFieldRecode.conFieldRecode(shapefile, fieldin, fieldout, row[fieldin], row[fieldout])

    # remove uncoded features
    ds = ogr.Open(shapefile, 1)
    lyr = ds.GetLayer()
    lyr.ResetReading()        
    lyr.SetAttributeFilter(fieldout + "=0 or " + fieldout + " IS NULL")
    for feat in lyr:
        lyr.DeleteFeature(feat.GetFID())

if __name__ == "__main__":
    if len(sys.argv) == 1:
	prog = os.path.basename(sys.argv[0])
	print '      '+sys.argv[0]+' [options]' 
	print "     Help : ", prog, " --help"
	print "        or : ", prog, " -h"
	sys.exit(-1)  
    else:
	usage = "usage: %prog [options] "
	parser = argparse.ArgumentParser(description = "Parse recode rules CSV file" \
        "and modify input shapefile by creating a new field and populate it with each" \
        "occurence of csv file")
        parser.add_argument("-s", dest="shapefile", action="store", \
                            help="Input shapefile", required = True)
        parser.add_argument("-csv", dest="csv", action="store", \
                            help="CSV or recode rules", required = True)
        parser.add_argument("-d", dest="delimiter", action="store", \
                            help="CSV delimiter", required = True)
        parser.add_argument("-if", dest="ifield", action="store", \
                            help="Existing field for rules condition", required = True) 
        parser.add_argument("-of", dest="ofield", action="store", \
                            help="Field to create and populate", required = True)
	args = parser.parse_args()
        harmonisationCodeIota(args.shapefile, args.csv, args.delimiter, args.ifield, args.ofield)
    
# python ../echantillons/harmonisation_code_iota2.py -s /home/thierion/Documents/OSO/iota2/Echantillons/references_2016/preparation/OSO_2016_dynafor.shp -csv /home/thierion/Documents/OSO/iota2/Echantillons/references_2016/preparation/Agrosolutions.csv -d , -if ros2016 -of CODE
