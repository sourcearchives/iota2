# -*- coding: utf-8 -*-
"""
Script pour créer un raster avec un identifiant unique pour chacun des groupes de pixels
ayant une valeur identiques et adjacents. Permet d'effectuer des selections d'entites.

"""

import sys
import os
from osgeo import gdal,ogr,osr
from skimage.measure import label
import argparse
import OSO_functions as osof
import otbApplication as otb

#------------------------------------------------------------------------------
def otb_concatenate_image(raster1, raster2, outname):
    """
    Combine deux rasters en un seul a partir d'otb ConcatenateImages.
    in :
        raster 1 : raster name
        raster 2 : raster ame
        outname file : raster name
        
    out :
        raster file
    """    
    ConcaImage = otb.Registry.CreateApplication("ConcatenateImages")
    ConcaImage.SetParameterStringList("il",[raster1,raster2])
    ConcaImage.SetParameterString("out", outname)
    ConcaImage.SetParameterOutputImagePixelType("out", otb.ImagePixelType_uint32)
    ConcaImage.ExecuteAndWriteOutput()
   
def otb_segmentation(raster, output, strippe):
    """
    Cree un raster avec un identifiant unique pour chacun des groupes de pixels
    ayant la meme valeur et etant adjacents.
    
    in :
        raster : raster name
        output : result raster name
        ram : number of strippe
        
    out :
        clump.tif
    """

    bmApp = otb.Registry.CreateApplication("Segmentation")
    bmApp.SetParameterString("in",raster)
    bmApp.SetParameterString("mode","raster")
    bmApp.SetParameterString("filter","cc")
    bmApp.SetParameterString("filter.cc.expr","distance<1")
    bmApp.SetParameterString("mode.raster.out",output,"?&streaming:type=stripped \
    &streaming:sizemode=nbsplits&streaming:sizevalue=%s"%(strippe))
    bmApp.SetParameterOutputImagePixelType("mode.raster.out", otb.ImagePixelType_uint32)
    bmApp.ExecuteAndWriteOutput()
            
def clumpScikit(path, raster):
    """
    Cree un raster avec un identifiant unique pour chacun des groupes de pixels
    ayant la meme valeur et etant adjacents avec la bibliotheque scikit image.
    
        in : 
            raster : raster name
        
        out : 
            path + /clump.tif
    """
    
    timer = osof.Timer()
    
    #ouverture de la classification regularise
    print "ouverture classif"
    datas,xsize,ysize,projection,transform,raster_band = osof.raster_open(raster,1)
    
    #generation clump
    print "Debut generation clump"
    timer.start()
    
    #genere un tableau de groupe et compte le nombre de ceux-ci
    clump, nb_features = label(datas, connectivity = 2, background = -1, return_num = True)   
    
    timer.stop()
    print "Nombre d'entites de la classification regularisee :", nb_features
    print "Temps de generation du clump", timer.interval
    
    #ajoute une valeur de 300 a chacun des identifiants, pour distinguer les valeurs de la classe OSO lors de l'etape de simplification
    clump = clump + 300
    osof.raster_save(path + "/clump.tif", xsize, ysize, transform, clump, projection, gdal.GDT_UInt32)
    
    return path + "/clump.tif", timer.interval
            
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
                             
        parser.add_argument("-in", dest="raster", action="store", \
                            help="Name of raster", required = True)
                            
        parser.add_argument("-nbcore", dest="core", action="store", \
                            help="Number of cores to use for OTB applications", required = True)
        
        parser.add_argument("-strippe", dest="strippe", action="store", \
                            help="Name of raster", required = True)
                            
        parser.add_argument("-clump", dest="clump", action="store", \
                            help="Do clump with otb or scikit ?", required = True)
        
        parser.add_argument("-out", dest="out", action="store", \
                            help="out path", required = True)
        
        timer = osof.Timer()                        
        args = parser.parse_args()
        os.environ["ITK_GLOBAL_DEFAULT_NUMBER_OF_THREADS"]= str(args.core)
        
        if args.clump == "otb" :
            print "Clump via OTB"
            timer.start()
            otb_segmentation(args.raster, args.path+"/clump.tif", args.strippe)
            otb_concatenate_image(args.raster, args.path+"/clump.tif", args.out+"/classif_clump_regularisee.tif")
            timer.stop()
            print "TEMPS : %s secondes"%(round(timer.interval,2))
            
        elif args.clump == "scikit" :
            print "Clump via scikit image"
            outfile, time = clumpScikit(args.out, args.raster)
            print "TEMPS : %s secondes"%(round(time, 2))
            
        else :
            print "Methode pour effectuer le clump non assignee. Fin"
        
