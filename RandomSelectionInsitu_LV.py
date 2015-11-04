#!/usr/bin/python

import sys
from sys import argv
import os
import osr
from osgeo import ogr
import random
import string

def RandomInSitu(shapefile, field, nbdraws, opath):
   """
   This function creates 2 * nbdraws new shapefiles by selecting 50% of polygons of each crop class present for \n
   a learning file and the remaining 50% for a validation file
       ARGs:
            -shapefile: the input shapefile
            -field: the name of the field in which selection will be based 
            -nbdraws: the number of random selections wanted
            -opath: the output path
           
       OUTPUT:
            -2 * nbdraws new shapefiles
    
   """

   classes = []
   allFID = []
   nameshp = shapefile.split('.')
   namefile = nameshp[0].split('/')

   driver = ogr.GetDriverByName("ESRI Shapefile")
   dataSource = driver.Open(shapefile, 0)
   layer = dataSource.GetLayer()

# Select the crop classes and count the total features of cropland

   layer.SetAttributeFilter("CROP =1")
   count = float(layer.GetFeatureCount())
   #print count

# Find the number of polygons by class
   for feature in layer:
       # Get the ID of the crop polygons and add them in a list
       pid = feature.GetFID()
       allFID.append(pid)
       # Get the list of codes of the crop class and add them in a list
       cl =  feature.GetField(field)
       if cl not in classes:
          classes.append(cl)
#Creates a dictionary of the codes and the name of the classes, this is only to display
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
	
#Crop classes are already selected, here after selects the individual classes of the crop classes
   for tirage in range(0,int(nbdraws)):
      listallid = []
      for cl in classes:
         listid = []
         layer = dataSource.GetLayer()
         #Selects the polygons of the individual crop class
         layer.SetAttributeFilter(field+" = "+str(cl))
         #Count the features of this class
         featureCount = float(layer.GetFeatureCount())
         #As we chose 50 percent, the total of features is divided by 2
         polbysel = featureCount / 2
         #Computes the proportion
         #Get all the IDs of the polygons of the class and add them in a list
         for feat in layer:
            _id = feat.GetFID()
            listid.append(_id)
            listid.sort()
         #From this list pick polbysel random ids and creates a list
         listToChoice = random.sample(listid, int(polbysel))
         #print listToChoice
         for fid in listToChoice:
            listallid.append(fid)  
         #print _id
         if (codeCrops.has_key(cl)):
            code = codeCrops[cl]
            print "Class # %s %s ---------> %s features " % (str(cl), str(code), str(featureCount))
      listallid.sort()

      #Process to create the SQL query
      ch = ""
      listFid = []
      #Add the word FID=
      for fid in listallid:
         listFid.append("FID="+str(fid))

      #Add the word OR
      resultA = []
      for e in listFid:
          resultA.append(e)
          resultA.append(' OR ')
      resultA.pop()
      #Creates the SQL chain
      chA =  ''.join(resultA)
      #Select polygons with the SQL query
      layer.SetAttributeFilter(chA)
      outShapefile = opath+"/"+namefile[-1]+"_seed"+str(tirage)+"_learn.shp"
      #Create a new layer with the selection
      CreateNewLayer(layer, outShapefile)

      #Process to create the 2nd SQL request by choosing the polygons that were not choose before

      listValid = []
      for i in allFID:
         if i not in listallid:
            listValid.append(i)

      chV = ""
      #Add the word FID=
      listFidV = []
      for fid in listValid:
         listFidV.append("FID="+str(fid))

      resultV = []
      #Add the word OR
      for e in listFidV:
          resultV.append(e)
          resultV.append(' OR ')
      resultV.pop()

      chV =  ''.join(resultV)
      #Select polygons with the SQL query
      layer.SetAttributeFilter(chV)
      outShapefile2 = opath+"/"+namefile[-1]+"_seed"+str(tirage)+"_val.shp"
      CreateNewLayer(layer, outShapefile2)


# 
def CreateNewLayer(layer, outShapefile):
      """
      This function creates a new shapefile
          ARGs:
            -layer: the input shapefile
            -outShapefile: the name of the output shapefile
    
      """

      #Warning: used to S2AGRI data model, next line to change, modify name of attributs
      field_name_target = ['ID', 'CROP', 'LC', 'CODE', 'IRRIG']
      outDriver = ogr.GetDriverByName("ESRI Shapefile")
      #if file already exists, delete it
      if os.path.exists(outShapefile):
        outDriver.DeleteDataSource(outShapefile)
      outDataSource = outDriver.CreateDataSource(outShapefile)
      out_lyr_name = os.path.splitext( os.path.split( outShapefile )[1] )[0]
      #Get the spatial reference of the input layer
      srsObj = layer.GetSpatialRef()
      #Creates the spatial reference of the output layer
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
         outFeature.SetGeometry(geom.Clone())
        # Add new feature to output Layer
         outLayer.CreateFeature(outFeature)


def shpPercentageSelection(infile, field, percentage, opath):
   """
   This function selects a percentage of polygons of an input layer and return the name of the output file
       ARGs:
            -infile: the input shapefile
            -field: the name of the field in which selection will be based 
            -percentage: the float value of the percentage to be selected 
            -opath: the output path

   """

   classes = []
   shapefile = infile
   allFID = []
   nameshp = shapefile.split('.')
   namefile = nameshp[0].split('/')

   driver = ogr.GetDriverByName("ESRI Shapefile")
   dataSource = driver.Open(shapefile, 0)
   layer = dataSource.GetLayer()

# Count the total features of cropland
   #For S2agri datamodel, select the crop classes. If all polygons wanted delete next line
   layer.SetAttributeFilter("CROP =1")
   count = float(layer.GetFeatureCount())
   #print count

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
      for feat in layer:
         _id = feat.GetFID()
         listid.append(_id)
         listid.sort()
      listToChoice = random.sample(listid, int(polbysel))
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
   return outShapefile

#RandomInSitu(argv[1], 'CODE', argv[2], argv[3])
#shpPercentageSelection(argv[1], 'CODE', argv[2], argv[3])
