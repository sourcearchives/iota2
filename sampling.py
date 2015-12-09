#!/usr/bin/python
#-*- coding: utf-8 -*-

import argparse
import sys,os,random
from osgeo import gdal, ogr,osr

#############################################################################################################################

def RandomInSitu(vectorFile, field, nbdraws, opath,name):

   """
		
   """
   crop = 0
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
   #print count
   
# Find the number of polygons by class
   for feature in layer:
       pid = feature.GetFID()
       allFID.append(pid)
       cl =  feature.GetField(field)
       if cl not in classes:
          classes.append(cl)

   for tirage in range(0,nbtirage):
      listallid = []
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
         	for feat in layer:
            		_id = feat.GetFID()
            		listid.append(_id)
            		listid.sort()
         	listToChoice = random.sample(listid, int(polbysel))
         	#print listToChoice
         	for fid in listToChoice:
            		listallid.append(fid)  
      listallid.sort()
      #print listallid
      ch = ""
      listFid = []
      for fid in listallid:
         listFid.append("FID="+str(fid))

      resultA = []
      for e in listFid:
          resultA.append(e)
          resultA.append(' OR ')
      resultA.pop()

      chA =  ''.join(resultA)
      layer.SetAttributeFilter(chA)
      outShapefile = opath+"/"+name+"_seed"+str(tirage)+"_learn.shp"
 
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
      outShapefile2 = opath+"/"+name+"_seed"+str(tirage)+"_val.shp"
      CreateNewLayer(layer, outShapefile2)

#############################################################################################################################

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
        	outLayer.CreateFeature(outFeature)

#############################################################################################################################

def ExtractData(pathToClip,shapeData,pathOut):
	
	"""
		Clip the shapeFile pathToClip with the shapeFile shapeData and store it in pathOut
	"""

	pathToTmpFiles = pathOut+"/AllTMP"
	driver = ogr.GetDriverByName('ESRI Shapefile')
	dataSource = driver.Open(pathToClip, 0) # 0 means read-only. 1 means writeable.
	# Check to see if shapefile is found.
	if dataSource is None:
    		print 'Could not open %s' % (pathToClip)
	else:
    		layer = dataSource.GetLayer()
    		featureCount = layer.GetFeatureCount()
		if featureCount!=0:
			path = ClipVectorData(shapeData, pathToClip, pathToTmpFiles)
			#check if shapeFile is empty
			dataSource_poly = driver.Open(path, 0)
			layer_poly = dataSource_poly.GetLayer()
			featureCount_poly = layer_poly.GetFeatureCount()
			if featureCount_poly != 0:
				return path

#############################################################################################################################

def FileSearch_AND(PathToFolder,*names):
	"""
		search all files in a folder or sub folder which contains all names in their name
		
		IN :
			- PathToFolder : target folder 
					ex : /xx/xxx/xx/xxx 
			- *names : target names
					ex : "target1","target2"
		OUT :
			- out : a list containing all path to the file which are containing all name 
	"""
	out = []
	for path, dirs, files in os.walk(PathToFolder):
   		 for i in range(len(files)):
			flag=0
			for name in names:
				if files[i].count(name)!=0 and files[i].count(".aux.xml")==0:
					flag+=1

			if flag == len(names):
				pathOut = path+'/'+files[i]
       				out.append(pathOut)
	return out

#############################################################################################################################

def ClipVectorData(vectorFile, cutFile, opath):
   """
   Cuts a shapefile with another shapefile
   ARGs:
       INPUT:
            -vectorFile: the shapefile to be cut
            -shpMask: the other shapefile 
       OUTPUT:
            -the vector file clipped
   """
   
   nameVF = vectorFile.split("/")[-1].split(".")[0]
   nameCF = cutFile.split("/")[-1].split(".")[0]
   outname = opath+"/"+nameVF+"_"+nameCF+".shp"
   if os.path.exists(outname):
      os.remove(outname)
   Clip = "ogr2ogr -clipsrc "+cutFile+" "+outname+" "+vectorFile+" -progress"
   print Clip
   os.system(Clip)
   return outname

#############################################################################################################################

def splitVectorLayer(shp_in, attribute, attribute_type,field_vals,pathOut):
	"""
		Split a vector layer in function of its attribute
		ARGs:
			INPUT:
				- shp_in: input shapefile
				- attribute: attribute to look for
				- attribute_type: attribute type which could be "string" or "int"
			OUTPUT
				- shp_out_list: list of shapefile names
	"""
	short_shp_in = shp_in.split('.')
	shp_out_list = []
	name = shp_in.split("/")[-1].split(".")[0]
	print name

	if attribute_type == "string":
		for val in field_vals:
			if val!= "None":
				shp_out = pathOut+"/"+name+"_region_"+str(val)+".shp"
				if ( not os.path.isfile(shp_out) ):
					cmd = "ogr2ogr "
					cmd += "-where '" + attribute + ' = "' + val + '"' + "' "					
					cmd += shp_out + " "
					cmd += shp_in + " "
					print cmd
					os.system(cmd)
				shp_out_list.append(shp_out)

	elif attribute_type == "int":
		for val in field_vals:
			shp_out = pathOut+"/"+name+"_region_"+str(val)+".shp"

			if ( not os.path.isfile(shp_out) ):
				cmd = "ogr2ogr "			
				cmd += "-where '" + attribute + " = " + str(val) + "' "
				cmd += shp_out + " "
				cmd += shp_in + " "
				print cmd
				os.system(cmd)
			shp_out_list.append(shp_out)
	else:
		print "Error for attribute_type ", attribute_type, '! Should be "string" or "int"'
		sys.exit(1)
	return shp_out_list

#############################################################################################################################

def createRegionsByTiles(shapeRegion,field_Region,pathToTiles,pathOut):

	"""
		create a shapeFile into tile's envelope for each regions in shapeRegion and for each tiles

		IN :
			- shapeRegion : the shape which contains all regions
			- field_Region : the field into the region's shape which describes each tile belong to which model
			- pathToTiles : path to the tile's envelope with priority
			- pathOut : path to store all resulting shapeFile

	"""
	pathToTmpFiles = pathOut+"/AllTMP"

	if not os.path.exists(pathToTmpFiles):
		os.system("mkdir "+pathToTmpFiles)

	#getAllTiles
	AllTiles = FileSearch_AND(pathToTiles,".shp")

	#get all region possible in the shape
	regionList = []
	driver = ogr.GetDriverByName("ESRI Shapefile")
	dataSource = driver.Open(shapeRegion, 0)
	layer = dataSource.GetLayer()
	for feature in layer:
		currentRegion = feature.GetField(field_Region)
    		try:
			ind = regionList.index(currentRegion)
		except ValueError :
			regionList.append(currentRegion)

	shpRegionList = splitVectorLayer(shapeRegion, field_Region,"int",regionList,pathToTmpFiles)

	AllClip = []
	for shp in shpRegionList :
		for tile in AllTiles:
			pathToClip = ClipVectorData(shp, tile, pathToTmpFiles)
			AllClip.append(pathToClip)
	return AllClip

#############################################################################################################################

def generateSampling(dataShape,dataField,region,regionField,pathToTiles,N,pathOut):

	"""
		for each region in the shapeFile "region", generate by tiles, learning and validation set for the classification

		IN :
			- dataShape : the shapeFile containing datas (ground truth)
			- dataField : the field into the data shapeFile which contains all class 
			- region : the shapeFile containing regions
			- regionField : the field into the region shapeFile which describe the model
			- pathToTiles : path where are store the tile's envelope
			- N : the number of random sample [int]
			- pathOut : path where to store all resulting shape
	"""
	AllClip = createRegionsByTiles(region,regionField,pathToTiles,pathOut)
	AllPath = []

	####################### // ####################### must me parallelized
	for clip in AllClip :
		print "---------------------> Extracting datas <---------------------"
		path = ExtractData(clip,dataShape,pathOut)
		if path != None:
			AllPath.append(path)
	####################### // #######################

	####################### // ####################### must me parallelized
	for path_mod_tile in AllPath:
		name = path_mod_tile.split("/")[-1].split("_")[-1].replace(".shp","")+"_Area_"+path_mod_tile.split("/")[-1].split("_")[-2]
		RandomInSitu(path_mod_tile, dataField, N, pathOut,name)
	####################### // #######################

#############################################################################################################################

if __name__ == "__main__":

	parser = argparse.ArgumentParser(description = "This function allow you to create N training and N validation shapes by regions cut by tiles")

	parser.add_argument("-region.shape",dest = "region",help ="path to the region shape (mandatory)",metavar = "")
	parser.add_argument("-region.field",dest = "regionField",help ="region's field into shapeFile, must be an integer field (mandatory)",metavar = "")
	parser.add_argument("-data.shape",dest = "data",help ="path to the shapeFile which contains datas (mandatory)",metavar = "")
	parser.add_argument("-data.field",dest = "dataField",help ="data's field into shapeFile (mandatory)",metavar = "")
	parser.add_argument("-tiles.path",dest = "pathToTiles",help ="path where tiles are stored (mandatory)",metavar = "")
	parser.add_argument("--sample",dest = "N",help ="number of random sample (default = 1)",default = 1,type = int,metavar = "")
	parser.add_argument("-out",dest = "pathOut",help ="path where to store all shapes by tiles (mandatory)",metavar = "")
	args = parser.parse_args()

	generateSampling(args.data,args.dataField,args.region,args.regionField,args.pathToTiles,args.N,args.pathOut)
	


































