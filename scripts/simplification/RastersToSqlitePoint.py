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

"""
Convert raster to sqlite point (pixel centroid) containing raster(s) value
"""

import sys, os, argparse, time, shutil

try:
    from VectorTools import BufferOgr
except ImportError:
    raise ImportError('Vector tools not well configured / installed')

try:
    from Common import OtbAppBank
except ImportError:
    raise ImportError('Iota2 not well configured / installed')


def maskSampleSelection(path, raster, maskmer, ram):
    
    tifMasqueMer = os.path.join(path, 'masque_mer.tif')
    bmapp = OtbAppBank.CreateBandMathApplication({"il": raster,
                                                "exp": "im1b1*0",
                                                "ram": ram,
                                                "pixType": 'uint8',
                                                "out": tifMasqueMer})
    bmapp.ExecuteAndWriteOutput()

    maskmerbuff = os.path.join(path, os.path.splitext(os.path.basename(maskmer))[0] + '_buff.shp')
    BufferOgr.bufferPoly(maskmer, maskmerbuff, 500)

    tifMasqueMerRecode = os.path.join(path, 'masque_mer_recode.tif')
    rastApp = OtbAppBank.CreateRasterizationApplication(maskmerbuff, tifMasqueMer, 1, tifMasqueMerRecode)
    rastApp.Execute()
    #command = "gdal_rasterize -burn 1 %s %s"%(maskmerbuff, tifMasqueMer)
    #os.system(command) 

    out = os.path.join(path, 'mask.tif')
    bmapp = OtbAppBank.CreateBandMathApplication({"il": [raster, rastApp],
                                                "exp": "((im1b1==0) || (im1b1==51)) && (im2b1==0)?0:1",
                                                "ram": ram,
                                                "pixType": 'uint8', 
                                                "out": out})
    bmapp.ExecuteAndWriteOutput()

    return out

def sampleSelection(path, raster, vecteur, field, ram='128', split=None, mask=None):

    timeinit = time.time()
    
    # polygon class stats (stats.xml)
    outxml = os.path.join(path, 'stats' + str(split) + '.xml')
    otbParams = {'in':raster, 'vec':vecteur, 'field':field, 'out':outxml, 'ram':ram}
    statsApp = OtbAppBank.CreatePolygonClassStatisticsApplication(otbParams)
    statsApp.ExecuteAndWriteOutput()

    shutil.copy(os.path.join(path, 'stats.xml'), '/work/OT/theia/oso/vincent/vectorisation/')
    
    timestats = time.time()     
    print " ".join([" : ".join(["Stats calculation", str(timestats - timeinit)]), "seconds"])
    if mask is not None:
        mask = maskSampleSelection(path, raster, mask, ram)
    else:
        mask = None
    
    # Sample selection
    outsqlite =  os.path.join(path, 'sample_selection' + str(split) + '.sqlite')
    if mask is None:
        otbParams = {'in':raster, 'vec':vecteur, 'field':field, 'instats': outxml, \
                     'out':outsqlite, 'ram':ram, 'strategy':'all', 'sampler':'random'}
    else:
        otbParams = {'in':raster, 'vec':vecteur, 'field':field, 'instats': outxml, \
                     'out':outsqlite, 'mask':mask, 'ram':ram, 'strategy':'all', 'sampler':'random'}
    sampleApp = OtbAppBank.CreateSampleSelectionApplication(otbParams)
    sampleApp.ExecuteAndWriteOutput()

    shutil.copy(os.path.join(path, outsqlite), '/work/OT/theia/oso/vincent/vectorisation/')                    

    timesample = time.time()     
    print " ".join([" : ".join(["Sample selection", str(timesample - timestats)]), "seconds"])

    return outsqlite

def sampleExtraction(raster, sample, field, outname, split, ram='128'):

    timesample = time.time()
    
    # Sample extraction
    outfile = os.path.splitext(str(outname))[0] + split + os.path.splitext(str(outname))[1]
    otbParams = {'in':raster, 'vec':sample, 'field':field.lower(), 'out':outfile, 'ram':ram}
    extractApp = OtbAppBank.CreateSampleExtractionApplication(otbParams)
    extractApp.ExecuteAndWriteOutput()

    timeextract = time.time()     
    print " ".join([" : ".join(["Sample extraction", str(timeextract - timesample)]), "seconds"])

def RastersToSqlitePoint(path, vecteur, field, outname, ram, rtype, rasters, maskmer=None, split=None):

    timeinit = time.time()
    # Rasters concatenation
    if len(rasters) > 1:
        concatApp = OtbAppBank.CreateConcatenateImagesApplication({"il" : rasters,
                                                                 "ram" : ram,
                                                                 "pixType" : rtype})
        concatApp.Execute()
        classif = OtbAppBank.CreateBandMathApplication({"il": rasters[0],
                                                      "exp": "im1b1",
                                                      "ram": ram,
                                                      "pixType": rtype})
        classif.Execute()
    else:
        concatApp = OtbAppBank.CreateBandMathApplication({"il": rasters,
                                                        "exp": "im1b1",
                                                        "ram": ram,
                                                        "pixType": rtype})
        concatApp.Execute()
        
    timeconcat = time.time()     
    print " ".join([" : ".join(["Raster concatenation", str(timeconcat - timeinit)]), "seconds"])

    # Stats and sample selection
    if len(rasters) == 1:
        classif = concatApp
        
    outsqlite = sampleSelection(path, classif, vecteur, field, ram, split, maskmer)

    # Stats extraction
    outtmp = os.path.join(path, os.path.basename(outname))
    sampleExtraction(concatApp, outsqlite, field, outtmp, split, ram)

    shutil.copyfile(outtmp, outname)
    
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
                            help="Working directory", required = True)

        parser.add_argument("-zone", dest="zone", action="store", \
                            help="zonal entitites (shapefile)", required = True)

	parser.add_argument("-field", dest="field", action="store", \
                            help="field name", default = "value", required = False)        
                            
        parser.add_argument("-nbcore", dest="core", action="store", \
                            help="Number of cores to use for OTB applications", required = True)
                            
        parser.add_argument("-ram", dest="ram", action="store", \
                            help="Ram for otb processes", required = True)
                            
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
    
        RastersToSqlitePoint(args.path, \
                             args.zone, \
                             args.field, \
                             args.out, \
                             args.ram, \
                             args.rtype, \
                             args.listRast, \
                             args.sea, \
                             args.split)
