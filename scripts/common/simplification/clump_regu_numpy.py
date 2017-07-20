# -*- coding: utf-8 -*-
#!/usr/bin/python

import OSO_functions as osof
#import clump
import os
from skimage.measure import label

classif_regularisee = "/work/OT/theia/oso/classifications/Simplification/FranceEntiere/otb/5101/double/classification_regul_adaptative_majoritaire_3.tif"
osof.otb_bandmaths([classif_regularisee], "/work/OT/theia/oso/classifications/Simplification/masque_mer.tif", "im1b1*0", 2, 8)
command = "gdal_rasterize -burn 1 %s %s/masque_mer.tif"%("/work/OT/theia/oso/classifications/Simplification/masque_mer.shp", "/work/OT/theia/oso/classifications/Simplification/FranceEntiere/otb/5101/double/")
os.system(command)
osof.otb_bandmath_2(classif_regularisee, "/work/OT/theia/oso/classifications/Simplification/FranceEntiere/otb/5101/double/masque_mer.tif", "/work/OT/theia/oso/classifications/Simplification/FranceEntiere/otb/5101/double/classification_regularisee.tif","(im1b1==51) && (im2b1==0)?255:im1b1", 2, 8)                 
classif_regularisee2 = "/work/OT/theia/oso/classifications/Simplification/FranceEntiere/otb/5101/double/classification_regularisee.tif"
clump.otb_segmentation(classif_regularisee2, args.path+"/clump.tif", args.ram)

dsClump = gdal.Open(args.path+"/clump.tif")
arrayClump = np.array(dsClump.GetRasterBand(1).ReadAsArray())
arrayClump300 = arrayClump + 300
rows = dsClump.RasterYSize
cols = dsClump.RasterXSize
projection = dsClump.GetProjectionRef()
osof.raster_save(args.path+"/clump_300.tif", cols, rows, dsClump.GetGeoTransform(), arrayClump300, projection, gdal.GDT_UInt32)

print "ouverture"





datas,xsize,ysize,projection,transform,raster_band = osof.raster_open("/work/OT/theia/oso/classifications/Simplification/FranceEntiere/otb/5101/double/classification_regularisee.tif",1)
print "Clump"
#clump, nb_features = label(datas, connectivity = 2, background = -1, return_num = True)
print "+300"
clump  = clump + 300
print "sauvegarde"
osof.raster_save("/work/OT/theia/oso/classifications/Simplification/FranceEntiere/scikit//clump.tif", xsize, ysize, transform, clump, projection, gdal.GDT_UInt32)
#clump_file, time_clump = clump.clump("/work/OT/theia/oso/classifications/Simplification/FranceEntiere/scikit/", "/work/OT/theia/oso/classifications/Simplification/FranceEntiere/scikit/classification_regularisee.tif") 
#clump.otb_concatenate_image("/work/OT/theia/oso/classifications/Simplification/FranceEntiere/scikit/classification_regularisee.tif", clump_file, "/work/OT/theia/oso/classifications/Simplification/FranceEntiere/scikit/classif_clump_regularisee.tif")
