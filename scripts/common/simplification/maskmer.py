# -*- coding: utf-8 -*-
#!/usr/bin/python

import OSO_functions as osof
import os
import shutil
import sys
import argparse

def maskmer(classifRegularisee, shapemer, MasqueMer):
    tifMasqueMer = osof.otb_bandmath_ram([classifRegularisee], \
                                         "im1b1*0", \
                                         2, \
                                         8, False, True, \
                                         MasqueMer)
    command = "gdal_rasterize -burn 1 %s %s"%(shapemer, tifMasqueMer)
    os.system(command)

if __name__ == "__main__":
    if len(sys.argv) == 1:
	prog = os.path.basename(sys.argv[0])
	print '      '+sys.argv[0]+' [options]' 
	print "     Help : ", prog, " --help"
	print "        or : ", prog, " -h"
	sys.exit(-1)  
 
    else:
	usage = "usage: %prog [options] "
	parser = argparse.ArgumentParser(description = "sea mask creation") 
        parser.add_argument("-classif", dest="path", action="store", \
                            help="raster template", required = True)
        parser.add_argument("-masque", dest="mask", action="store", \
                            help="sea mask", required = True)
        parser.add_argument("-out", dest="out", action="store", \
                            help="sea mask output raster path", required = True)

        maskmer(args.classif, args.mask, args.out)

#python maskmer('/home/thierionv/work_cluster/classifications/Simplification/FranceEntiere/otb/5101/double/classif_clump_regularisee.tif', '/home/thierionv/work_cluster/classifications/Simplification/masque_mer.shp', '/home/thierionv/work_cluster/classifications/Simplification/FranceEntiere/otb/5101/double/masque_mer.tif')
