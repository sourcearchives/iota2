#!/usr/bin/python
from osgeo import ogr
import os
import glob
from sys import argv
import gdal
import ConfigClassifN as Config
import Dico as dico


maskCshp = dico.maskLshp
expression = dico.expr
random = dico.random
bound = dico.bound
pixelo = dico.pixelotb
pixelg = dico.pixelgdal
#pathmetrics = "/mnt/data/home/ariasm/otb-ml-validation/otb-ml-validation/src/applications/confusion-matrix-metrics.py"
#pathmetrics = "/mnt/data/home/ariasm/croptypeNational/confusionmatrixmetricsNational.py"
pathmetrics = "/mnt/data/home/ariasm/croptypeNational/confusionmatrixmetricsNational.py"


def GetSerieList(*SerieList):
   """
   Returns a list of images likes a character chain.
   ARGs:
       INPUT:
            -SerieList: the list of different series
       OUTPUT:
   """  
   ch = ""
   for serie in SerieList:
     name = serie.split('.')
     ch = ch+serie+" "
   return ch


#--------------------------------------------------------------
def BuildName(opath, *SerieList):
   """
   Returns a name for an output using as input several images series.
   ARGs:
       INPUT:
            -SerieList:  the list of different series
            -opath : output path
   """  
   
   chname = ""
   for serie in SerieList:
      feat = serie.split(' ') 
      for f in feat:
         name = f.split('.')
         feature = name[0].split('/')
         chname = chname+feature[-1]+"_"
   return chname

#--------------------------------------------------------------
def ConcatenateAllData(opath, *SerieList):
   """
   Concatenates all data: Reflectances, NDVI, NDWI, Brightness
   ARGs:
       INPUT:
            -SerieList: the list of different series
            -opath : output path
       OUTPUT:
            - The concatenated data
   """
   ch = GetSerieList(*SerieList)
   name = BuildName(opath, *SerieList)
   ConcFile = opath+"/"+name+".tif"
   Concatenation = "otbcli_ConcatenateImages -il "+ch+" -out "+ConcFile+" "+pixelo
   print Concatenation
   os.system(Concatenation)

#--------------------------------------------------------------
def ClipVectorData(vectorFile, opath):
   """
   Cuts a shapefile with another shapefile
   ARGs:
       INPUT:
            -vectorFile: the shapefile to be cut
            -shpMask: the other shapefile 
       OUTPUT:
            -the vector file cut
   """
   
   nameV = vectorFile.split('.')
   nameF = nameV[0].split('/') 
   outname = opath+"/"+nameF[-1]+"_CLIPPED."+nameV[1]
   if os.path.exists(outname):
      os.remove(outname)
   Clip = "ogr2ogr -clipsrc "+opath+"/"+maskCshp+" "+outname+" "+vectorFile+" -progress"
   print Clip
   os.system(Clip)
   return outname

#--------------------------------------------------------------
def BuildCropMask(vectorFile, image, opath):
   """
   With a vector file builds the crop mask, used for national cases where the RPG is used as the crop mask
   """
   rast = "otbcli_Rasterization -in "+vectorFile+" -out "+opath+"/CropMask.tif -im "+image+" -mode.binary.foreground 1"
   os.system(rast)
   
#--------------------------------------------------------------
def ComputeImageStats(opath, DataSeries):
   """
   Computes the statistics of a serie
    ARGs:
       INPUT:
            - SerieList: list of image series 
       OUTPUT:
            - xml file
   """
   print DataSeries
   name = DataSeries.split('.')
   statfile = name[0]+".xml"
   Stat = "otbcli_ComputeImagesStatistics -il "+DataSeries+" -out "+statfile+" -bv -10000"
   print Stat
   os.system(Stat)
   return statfile
#--------------------------------------------------------------
def getListValsamples(ipath):
   """
   Returns the list of samples to the validation according to the established naming
   """
   sampList = []
   for shpfile in glob.glob(ipath+"/*val.shp"):
      sampList.append(shpfile)
   sampList.sort()
   return sampList

#--------------------------------------------------------------
def getListLearnsamples(ipath):
   """
   Returns the list of samples to the learning according to the established naming
   """
   sampList = []
   for shpfile in glob.glob(ipath+"/*learn.shp"):
      sampList.append(shpfile)
   sampList.sort()
   return sampList
#--------------------------------------------------------------
def RFClassif(perc, vectorFile, opathFcl, opathT, opathFim, *SerieList):
   """
   Computes the Random Forest classification, uses the ConfigClassif file
   which containts the classification parameters
    ARGs:
       INPUT:
            - samplesFile : the vector file containing the samples
            - SerieList: list of image series
       OUTPUT:
            - Text file with the model
            - Text file with the confusion matrix
   """
   args = Config.dicRF()
   ch = ""
   i=0
   bm = 0

   newpath = opathFcl+"/RF_"+str(perc)
   if not os.path.exists(newpath):
      os.mkdir(newpath)
  
   for key in args:
      ch = ch+"-"+key+" "+str(args[key])+" "

   name = BuildName(opathFim, *SerieList) 
   statFile = opathFim+"/"+name+".xml"
   dataSeries = opathFim+"/"+name+".tif"

   if not os.path.exists(dataSeries):
      dataSeries = ConcatenateAllData(opathFim, *SerieList)
      ComputeImageStats(opathFim, dataSeries)
   elif os.path.exists(dataSeries):
      if not os.path.exists(statFile):
         statFile = ComputeImageStats(opathFim, dataSeries)

   vectorPath = vectorFile.split('/')
   vectorName = vectorPath[-1].split('_')
   seed = vectorName[6]

   Classif = "otbcli_TrainImagesClassifier -io.il "+dataSeries+" -io.vd "+vectorFile\
   +" -io.imstat "+statFile+" -sample.bm "+str(bm)+" -io.confmatout "+newpath+"/RF_ConfMat_"+seed\
   +"_bm"+str(bm)+".csv -io.out "+newpath+"/RF_Classification_"+seed+"_bm"+str(bm)+".txt "+ch
   print Classif   
   os.system(Classif)
   return newpath+"/RF_ConfMat_"+seed+"_bm"+str(bm)+".csv"
   '''
   for value in random:
      for bm in bound: 
         Classif = "otbcli_TrainImagesClassifier -io.il "+dataSeries+" -io.vd "+vectorFile\
         +" -io.imstat "+statFile+" -rand "+str(value)+" -sample.bm "+str(bm)+" -io.confmatout "+newpath+"/RF_ConfMat_"+str(i)\
         +"_bm_"+str(bm)+".csv -io.out "+newpath+"/RF_Classification_"+str(i)+"_bm"+str(bm)+".txt "+ch
         os.system(Classif)
         print Classif
      i+=1
   '''

#--------------------------------------------------------------
def SelectByQuery(vectorFile, expression, outVectorFile, opath):
   """
   Using a query, does a selection.
   ARGs:
       INPUT:
            - vectorFile : the vector file containing the samples
            - expression: expression used to do the selection
            - outVectorFile: name of the output file, without the ".shp"
            - opath
       OUTPUT:
            - A vector file containig the polygons selected
   """
   # Get the input Layer
   inDriver = ogr.GetDriverByName("ESRI Shapefile")
   inDataSource = inDriver.Open(vectorFile, 0)
   inLayer = inDataSource.GetLayer()
   inLayer.SetAttributeFilter(expression)
   outDriver = ogr.GetDriverByName("ESRI Shapefile")
   # Remove output shapefile if it already exists
   outShapefile = opath+"/"+outVectorFile+".shp"
   if os.path.exists(outShapefile):
        outDriver.DeleteDataSource(outShapefile)
   outDataset = inDriver.CreateDataSource(outShapefile)
   outLayer = outDataset.CopyLayer(inLayer, outVectorFile)


#--------------------------------------------------------------
def GetCropSamples(vectorFile, opath):
   """
   Used to select only the CROP classes of the vector file. Returns the file name
    ARGs:
       INPUT:
           - vectorFile : the vector file containing the samples
           - opath
   """
   vectorClip = ClipVectorData(vectorFile, opath)
   nameV = vectorFile.split('.')
   nameF = nameV[0].split('/')
   nameO = nameF[-1]+"_CROP"
   outname = opath+"/"+nameF[-1]+"_CROP."+nameV[1]
   print nameO
   crop = SelectByQuery(vectorClip, expression, nameO, opath)
   
   return outname

#--------------------------------------------------------------
def getListModel(ipath):
   """
   Returns the list of models of classifications in a path
   """
   modelList = []
   for model in glob.glob(ipath+"/*Classification*.txt"):
      modelList.append(model)
   modelList.sort()
   return modelList

#--------------------------------------------------------------
def imageClassification(model, image, opath, mask):
   """
   Performs a classification of the input image according to a model file.
   ARGs:
      INPUT:
          - model: model file
          - image: input image 
          - opath: output path
      OUTPUT:
          - Classification in TIFF format
   """
   if not os.path.exists(opath):
      os.mkdir(opath) 
   imPath = image.split('.')
   stats = imPath[0]+".xml"
   modelPath = model.split('.')
   modelName = modelPath[0].split('/')   
   classifName = opath+"/"+modelName[-1]+".tif"

   Classif = "otbcli_ImageClassifier -in "+image+" -imstat "+stats+" -model "+model\
   +" -out "+classifName+" int16 -ram 128 -mask "+mask
   print Classif
   os.system(Classif)
   return classifName
#------------------------------------------------------------------
def getValsamples(classification, samplesList):
   """
   Finds the samples file to do the validation using the number of the seed (Ex:RF_Classification_seed2_bm0.txt -> \n
   AR_SANT_LC_FO_2013_CROP_seed0_learn.shp
   """
   classPath = classification.split('.')
   nameClass = classPath[0].split('/')
   nameParts = nameClass[-1].split('_')
   seed = nameParts[2]
   for i in samplesList:
      name = i.split('_')
      for j in name:
         if j == seed:
            samplesVal = i
   return samplesVal
   
#------------------------------------------------------------------   
def ConfMatrix(classification, refdata, opath):
   """
   Computes the confusion matrix of a classification
   """
   classPath = classification.split('.')
   classname = classPath[0].split('/')
   algoname = classname[-1].split('_')
   confName = opath+"/"+algoname[0]+"_ConfMat_"+algoname[-2]+"_"+algoname[-1]+".csv"
   Compute = "otbcli_ComputeConfusionMatrix -in "+classification+" -out "+confName\
   +" -ref vector -ref.vector.field CODE -ref.vector.in "+refdata
   print Compute
   os.system(Compute)
   return confName

#------------------------------------------------------------------
def getListConfMat(ipath, keyword1, keyword2):
   """
   Get the list of the confusion matrix taking into account 2 keywords: (ex: RF bm0)
   """
   confMatList = []
   for confMat in glob.glob(ipath+"/*"+keyword1+"*"+keyword2+"*.csv"):
      confMatList.append(confMat)
   return confMatList

#------------------------------------------------------------------
def ComputeMetrics(ipath, opath, *ConfMList):
   """
   Takes a list of confusion matrix and computes the OA per matrix, mean OA, std OA,  minFScore
   """
   os.chdir(ipath)
   ch = ""
   for ConfMat in ConfMList[0]:
      path = ConfMat.split('/')
      ch = ch+path[-1]+" "
   outpath = ConfMList[0][0].split('/')  
   outname = outpath[-1].split('_')
   bm = outname[-1].split('.')
   outmetricsname = "Metrics_"+outname[0]+"_"+bm[0]+".txt"
   if os.path.exists(outmetricsname):
      os.remove(outmetricsname)
   metrics = "python "+pathmetrics+" "+ipath+" "+ch+" >> "+outmetricsname
   print metrics
   os.system(metrics)
   
#------------------------------------------------------------------   
def DFfusion(RFclassif, RFconfMat, SVMclassif, SVMconfMat, opath):
   """
   Fuses RF and SVM classifications using best RF and SVM classifications
   """
   pathClassifRF = RFclassif.split('.')
   nameClassifRF = pathClassifRF[0].split('/')
   pathClassifSVM = SVMclassif.split('.')
   nameClassifSVM = pathClassifSVM[0].split('/')
   outName = opath+"/"+nameClassifRF[-1]+"_"+nameClassifSVM[-1]+".tif"

   Fusion = "otbcli_FusionOfClassifications -il "+RFclassif+" "+SVMclassif\
   +" -method dempstershafer -method.dempstershafer.cmfl "+RFconfMat+" "+SVMconfMat\
   +" -out "+outName
   print Fusion
   os.system(Fusion)
   return outName

#---------------------------------------------------------------------
def getListFussamples(vectorFile, ipath, seed, keyword):
   """
   Returns the list of samples for the Dempster-Shafer fusion according to the established naming
   """
   sampList = []
   for shpfile in glob.glob(ipath+"/*seed"+str(seed)+"*"+keyword+".shp"):
      sampList.append(shpfile)
   sampList.sort()
   return sampList

#------------------------------------------------------------------   
def ConfMatrixFusion(classification, refdata, opath):
   """
   Computes the confusion matrix of a classification
   """
   classPath = classification.split('.')
   classname = classPath[0].split('/')
   algoname = classname[-1].split('_')
   confName = opath+"/"+algoname[0]+algoname[3]+"_ConfMat_"+algoname[2]+"_"+algoname[4]+algoname[-1]+".csv"
   Compute = "otbcli_ComputeConfusionMatrix -in "+classification+" -out "+confName\
   +" -ref vector -ref.vector.field CODE -ref.vector.in "+refdata
   print Compute
   os.system(Compute)
   return confName

#-----------------------------------------------------------------
def CountPixels(filein, sizePixel):
   """
   Count the numbers of pixels of a shapefile
   """

   source = ogr.Open(filein, 1)
   layer = source.GetLayer()
   layer_defn = layer.GetLayerDefn()
   field_names = [layer_defn.GetFieldDefn(i).GetName() for i in range(layer_defn.GetFieldCount())]

   areaTotal = 0	
   for i in layer:
      index = i.GetFieldAsInteger("ID")
      geom = i.GetGeometryRef()
      area = geom.GetArea()
      areaTotal = areaTotal + area 
   pixels = areaTotal/(int(sizePixel)*int(sizePixel))
   print pixels

   return pixels
#-----------------------------------------------------------------

