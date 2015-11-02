#!/usr/bin/python

import sys
from sys import argv
import os
import osr
from osgeo import ogr
import random
import string


def RandomInSitu(vectorFile, field, nbdraws, opath,crop):


   classes = []
   shapefile = vectorFile
   field = field
   dicoprop = {}
   allFID = []
   nbtirage = nbdraws
   nameshp = shapefile.split('.')
   namefile = nameshp[0].split('/')

   driver = ogr.GetDriverByName("ESRI Shapefile")
   dataSource = driver.Open(shapefile, 0)
   layer = dataSource.GetLayer()

# Count the total features of cropland
   if crop == 1:
   	layer.SetAttributeFilter("CROP =1")
   count = float(layer.GetFeatureCount())
   print count
   
# Find the number of polygons by class
   for feature in layer:
       pid = feature.GetFID()
       allFID.append(pid)
       cl =  feature.GetField(field)
       if cl not in classes:
          classes.append(cl)
   """
   if field == 'CODE':
      filein=open('/mnt/data/home/ariasm/croptype_bench/LegendDefinition.csv')
   elif field == 'CROP':
      filein=open('/mnt/data/home/ariasm/croptype_bench/CropDefinition.csv')
   codeCrops={}
   for line in filein:
      entry = line
      classeCod = entry.split(":")
      codeCrops[int(classeCod[1])]=(classeCod[0])
   filein.close()	
   """
   for tirage in range(0,nbtirage):
      listallid = []
      listonepol = []
      listValid = []
      for cl in classes:
         listid = []
         layer = dataSource.GetLayer()
         layer.SetAttributeFilter(field+" = "+str(cl))
         featureCount = float(layer.GetFeatureCount())
	 if featureCount == 1:
	 	for feat in layer:
           	   _id = feat.GetFID()
		   listallid.append(_id)
                   listValid.append(_id)
         else:
         	polbysel = round(featureCount / 2)
         	if polbysel <= 1:
	    		polbysel = 1
         		#print polbysel
         	prop = float((featureCount/count)*100)
         	dicoprop[cl] = prop
         	for feat in layer:
            		_id = feat.GetFID()
            		listid.append(_id)
            		listid.sort()
         	listToChoice = random.sample(listid, int(polbysel))
         	#print listToChoice
         	for fid in listToChoice:
            		listallid.append(fid)  
         """
         if (codeCrops.has_key(cl)):
            code = codeCrops[cl]
            #print "Class # %s %s ---------> %s features " % (str(cl), str(code), str(featureCount))
         """
      listallid.sort()
      #print listallid
      ch = ""
      listFid = []
      for fid in listallid:
         listFid.append("FID="+str(fid))

   #print listFid
      resultA = []
      for e in listFid:
          resultA.append(e)
          resultA.append(' OR ')
      resultA.pop()

      chA =  ''.join(resultA)
      layer.SetAttributeFilter(chA)
      outShapefile = opath+"/"+namefile[-1]+"_seed"+str(tirage)+"_learn.shp"
 
      CreateNewLayer(layer, outShapefile)


      for i in allFID:
         if i not in listallid:
            listValid.append(i)

      chV = ""
      listFidV = []
      for fid in listValid:
         listFidV.append("FID="+str(fid))

      resultV = []
      for e in listFidV:
          resultV.append(e)
          resultV.append(' OR ')
      resultV.pop()

      chV =  ''.join(resultV)
      layer.SetAttributeFilter(chV)
      outShapefile2 = opath+"/"+namefile[-1]+"_seed"+str(tirage)+"_val.shp"
      CreateNewLayer(layer, outShapefile2)



def CreateNewLayer(layer, outShapefile):
      field_name_target = ['ID', 'CROP', 'LC', 'CODE', 'IRRIG']
      outDriver = ogr.GetDriverByName("ESRI Shapefile")
      if os.path.exists(outShapefile):
        outDriver.DeleteDataSource(outShapefile)
      outDataSource = outDriver.CreateDataSource(outShapefile)
      out_lyr_name = os.path.splitext( os.path.split( outShapefile )[1] )[0]
      srsObj = layer.GetSpatialRef()
      outLayer = outDataSource.CreateLayer( out_lyr_name, srsObj, geom_type=ogr.wkbMultiPolygon )
      # Add input Layer Fields to the output Layer if it is the one we want
      inLayerDefn = layer.GetLayerDefn()
      for i in range(0, inLayerDefn.GetFieldCount()):
         fieldDefn = inLayerDefn.GetFieldDefn(i)
         fieldName = fieldDefn.GetName()
         if fieldName not in field_name_target:
             continue
         outLayer.CreateField(fieldDefn)
     # Get the output Layer's Feature Definition
      outLayerDefn = outLayer.GetLayerDefn()

     # Add features to the ouput Layer
      for inFeature in layer:
      # Create output Feature
         outFeature = ogr.Feature(outLayerDefn)

        # Add field values from input Layer
         for i in range(0, outLayerDefn.GetFieldCount()):
            fieldDefn = outLayerDefn.GetFieldDefn(i)
            fieldName = fieldDefn.GetName()
            if fieldName not in field_name_target:
                continue

            outFeature.SetField(outLayerDefn.GetFieldDefn(i).GetNameRef(),
                inFeature.GetField(i))
        # Set geometry as centroid
	 geom = inFeature.GetGeometryRef()
	 if geom:
         	outFeature.SetGeometry(geom.Clone())
        # Add new feature to output Layer
        	outLayer.CreateFeature(outFeature)
         #outFeature.SetGeometry(geom.Clone())
        # Add new feature to output Layer
        #outLayer.CreateFeature(outFeature)

def shpPercentageSelection(infile, field, percentage, opath, crop):
   classes = []
   shapefile = infile
   dicoprop = {}
   allFID = []
   nameshp = shapefile.split('.')
   namefile = nameshp[0].split('/')

   driver = ogr.GetDriverByName("ESRI Shapefile")
   dataSource = driver.Open(shapefile, 0)
   layer = dataSource.GetLayer()

# Count the total features of cropland
   if crop == 1:
   	layer.SetAttributeFilter("CROP =1")
   count = float(layer.GetFeatureCount())
   
   for feature in layer:
      pid = feature.GetFID()
      allFID.append(pid)
      cl =  feature.GetField(field)
      if cl not in classes:
         classes.append(cl)
   listallid = []
   for cl in classes:
      listid = []
      layer = dataSource.GetLayer()
      layer.SetAttributeFilter(field+" = "+str(cl))
      featureCount = float(layer.GetFeatureCount())
      polbysel = int((featureCount*float(percentage))/100)
      print polbysel
      for feat in layer:
         _id = feat.GetFID()
          #print _id
         listid.append(_id)
         listid.sort()
         #print listid
      listToChoice = random.sample(listid, int(polbysel))
         #print listToChoice
      for fid in listToChoice:
         listallid.append(fid)  
   listallid.sort()
   ch = ""
   listFid = []
   for fid in listallid:
      listFid.append("FID="+str(fid))
   resultA = []
   for e in listFid:
      resultA.append(e)
      resultA.append(' OR ')
   resultA.pop()
   per = string.replace(str(percentage),'.','p') 
   chA =  ''.join(resultA)
   layer.SetAttributeFilter(chA)
   
   outShapefile = opath+"/"+namefile[-1]+"-"+str(per)+"perc.shp"
   CreateNewLayer(layer, outShapefile)
   print "File created "+outShapefile
   return outShapefile

#RandomInSitu(argv[1], 'CODE',1 , argv[2], 0)
#shpPercentageSelection(argv[1], 'CODE', argv[2], argv[3],0)
