#!/usr/bin/python
#-*- coding: utf-8 -*-
"""

"""

import sys
import os
import argparse
import BufferOgr
import otbAppli
import time

def maskSampleSelection(path, raster, maskmer):

    tifMasqueMer = os.path.join(path, 'masque_mer.tif')
    bmapp = otbAppli.CreateBandMathApplication(raster, "im1b1*0", ram, 'uint8', tifMasqueMer)
    bmapp.ExecuteAndWriteOutput()
    
    maskmerbuff = os.path.join(path, os.path.splitext(maskmer)[0] + 'buff.shp')
    BufferOgr.bufferPoly(maskmer, maskmerbuff, 500)

    tifMasqueMerRecode = os.path.join(path, 'masque_mer_recode.tif')
    rastApp = otbAppli.CreateRasterizationApplication(maskmerbuff, tifMasqueMer, 1, tifMasqueMerRecode)
    rastApp.ExecuteAndWriteOutput()
    #command = "gdal_rasterize -burn 1 %s %s"%(maskmerbuff, tifMasqueMer)
    #os.system(command) 

    out = os.path.join(path, 'mask.tif')
    bmapp = otbAppli.CreateBandMathApplication([raster, tifMasqueMerRecode], \
                                               "((im1b1==0) || (im1b1==51)) && (im2b1==0)?0:1", \
                                               ram, 'uint8', out)
    bmapp.ExecuteAndWriteOutput()

    return out

def sampleSelection(path, raster, vecteur, field, split="", mask=""):

    timeinit = time.time()
    
    # polygon class stats (stats.xml)
    outxml = os.path.join(path, 'stats' + str(split) + '.xml')    
    statsApp = otbAppli.CreatePolygonClassStatisticsApplication(raster, vecteur, field, outxml, split)
    statsApp.ExecuteAndWriteOutput()

    timestats = time.time()     
    print " ".join([" : ".join(["Stats calculation", str(timestats - timeinit)]), "seconds"])

    if mask != '':
        mask = maskSampleSelection(path, raster, mask)
    else:
        mask = ''
    
    # Sample selection
    outsqlite =  os.path.join(path, 'sample_selection' + str(split) + '.sqlite')
    sampleApp = otbAppli.CreateSampleSelectionApplication(raster, vecteur, field, outxml, outsqlite, split, mask)
    sampleApp.ExecuteAndWriteOutput()

    timesample = time.time()     
    print " ".join([" : ".join(["Sample selection", str(timesample - timestats)]), "seconds"])

    return outsqlite

def sampleExtraction(raster, sample, field, out, split):

    timesample = time.time()
    
    # Sample extraction
    outname =  os.path.join(out, 'sample_extraction' + str(split) + '.sqlite')
    extractApp = otbAppli.CreateSampleExtractionApplication(raster, sample, field.lower(), outname, split)
    extractApp.ExecuteAndWriteOutput()

    timeextract = time.time()     
    print " ".join([" : ".join(["Sample extraction", str(timeextract - timesample)]), "seconds"])
    
    return outname

def RastersToSqlitePoint(path, vecteur, field, out, ram, rtype, maskmer="", split="", *rasters):

    timeinit = time.time()
    
    # Rasters concatenation
    if len(rasters[0]) > 1:
        concatApp = otbAppli.CreateConcatenateImagesApplication(rasters[0], ram, rtype)
        concatApp.Execute()
    else:
        concatApp = otbAppli.CreateBandMathApplication(rasters[0], "im1b1", ram, rtype)
        concatApp.Execute()
        
    timeconcat = time.time()     
    print " ".join([" : ".join(["Raster concatenation", str(timeconcat - timeinit)]), "seconds"])

    # Stats and sample selection
    outsqlite = sampleSelection(path, concatApp, vecteur, field, split, maskmer)

    # Stats extraction
    outname = sampleExtraction(concatApp, outsqlite, field, out, split)        
    
    return outname
    
if __name__ == "__main__":
    if len(sys.argv) == 1:
	prog = os.path.basename(sys.argv[0])
	print '      '+sys.argv[0]+' [options]' 
	print "     Help : ", prog, " --help"
	print "        or : ", prog, " -h"
	sys.exit(-1)  
 
    else:
	usage = "usage: %prog [options] "
	parser = argparse.ArgumentParser(description = "Regulararize a raster")
        parser.add_argument("-wd", dest="path", action="store", \
                            help="Input path where classification is located", required = True)

        parser.add_argument("-zone", dest="zone", action="store", \
                            help="zonal entitites (shapefile)", required = True)

	parser.add_argument("-field", dest="field", action="store", \
                            help="field name", default = "value", required = False)        
                            
        parser.add_argument("-nbcore", dest="core", action="store", \
                            help="Number of cores to use for OTB applications", required = True)
                            
        parser.add_argument("-ram", dest="ram", action="store", \
                            help="Number of strippe for otb process", required = True)
                            
        parser.add_argument("-out", dest="out", action="store", \
                            help="output path ", required = True)                            

        parser.add_argument("-sea", dest="sea", action="store", \
                            help="terrestrial mask (to separate sea and inland waters)", required = False)
        
	parser.add_argument("-split", dest="split", action="store", \
                            help="split index",default = "",required = False)

        parser.add_argument("-listRast", dest="listRast", nargs='+', \
                            help="list of rasters to extract stats (first one have to be classification raster" \
                            "and rasters must have the same resolution)")
        
        parser.add_argument("-rtype", dest="rtype", action="store", \
                            help="Rasters pixel format (OTB style)", required = True)
        
        args = parser.parse_args()
        os.environ["ITK_GLOBAL_DEFAULT_NUMBER_OF_THREADS"]= str(args.core)
    
        sample_extract, time_poly_class_stats, \
        time_sample_selection, time_sample_extract = zonal_stats_otb(args.path, \
                                                                     args.zone, \
                                                                     args.field, \
                                                                     args.out, \
                                                                     args.ram, \
                                                                     args.rtype, \
                                                                     args.sea, \
                                                                     args.split, \
                                                                     args.rasters)
