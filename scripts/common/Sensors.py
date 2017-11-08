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

from config import Config
import glob

from GenSensors import Sensor
from GenSensors import MonException
from collections import OrderedDict

class Landsat5(Sensor):

    def __init__(self,path_image,opath,fconf,workRes,createFolder = "Create",
                 dicoBands={"B1":1 ,"B2":2 ,"B3":3 ,"B4":4 ,"B5":5 ,"B6":6}):
        Sensor.__init__(self)
        #Invariant Parameters
        if not createFolder:
            tmpPath = ""
        else:
            tmpPath = opath.opathT

        self.name = 'Landsat5'
        self.DatesVoulues = None
        self.path = path_image
        self.bands["BANDS"] = dicoBands
        self.nbBands = len(self.bands['BANDS'].keys())
        self.posDate = 3
        self.fimages = tmpPath+"/"+self.name+"imagesList.txt"
        self.fdates = tmpPath+""+self.name+"imagesDateList.txt"
        self.fImResize = tmpPath+"/"+self.name+"ImageResList.txt"
        self.fdatesRes = tmpPath+"/"+self.name+"ImageDateResList.txt"
        self.work_res = workRes

        # Users parameters
        cfg = Config(fconf)
        conf = cfg.Landsat5
        conf2 = cfg.GlobChain

        #bands definitions
        self.bands["BANDS"] = OrderedDict([(key, value) for key, value in sorted(dicoBands.iteritems(), key=lambda (k,v): (v,k))])
        self.red = self.bands["BANDS"]['B3']
        self.nir = self.bands["BANDS"]['B4']
        self.swir = self.bands["BANDS"]['B5']

        if cfg.iota2FeatureExtraction.extractBands == 'True':
            self.keepBands = OrderedDict([(k, v) for k, v in self.bands["BANDS"].items() if k in conf.keepBands])
            if cfg.GlobChain.features:
                try:
                    self.red = self.keepBands.keys().index('B3')
                except:
                    raise Exception ("red band is needed to compute features")
                try:
                    self.nir = self.keepBands.keys().index('B4')
                except:
                    raise Exception ("nir band is needed to compute features")
                try:
                    self.swir = self.keepBands.keys().index('B5')
                except:
                    raise Exception ("swir band is needed to compute features")
            else:
                self.red = self.nir = self.swir = -1
        #MASK
        self.sumMask = tmpPath+"/"+self.name+"_Sum_Mask.tif"
        self.borderMaskN = tmpPath+"/"+self.name+"_Border_MaskN.tif"
        self.borderMaskR = tmpPath+"/"+self.name+"_Border_MaskR.tif"

        #Time series
        self.serieTemp = tmpPath+"/"+self.name+"_ST_REFL.tif"
        self.serieTempMask = tmpPath+"/"+self.name+"_ST_MASK.tif"
        self.serieTempGap = tmpPath+"/"+self.name+"_ST_REFL_GAP.tif"
        #Indices
        self.indices = "NDVI","NDWI","Brightness"

        #DATA INFO
        self.struct_path = conf.arbo
        self.native_res = int(conf.nativeRes)
        self.imType = conf.imtype
        self.pathRes = tmpPath+"/LandRes_%sm/"%workRes
        self.proj = conf2.proj

        self.addFeatures = (conf.additionalFeatures).split(",")
        #MASK INFO
        self.nuages = conf.nuages
        self.saturation = conf.saturation
        self.div = conf.div
        self.nodata = conf.nodata
        self.pathmask = self.path+conf.arbomask
        if conf.nodata_Mask == 'False':
            self.nodata_MASK = False
        elif conf.nodata_Mask == "True":
            self.nodata_MASK = True
        else:
            print "Value Error for No Data Mask flag. NoDataMask not considered"
            self.nodata_MASK = False

        if self.native_res == self.work_res:
            self.borderMask = self.borderMaskN
        else:
            self.borderMask = self.borderMaskR
        try:
            liste = []
            if createFolder :
                liste = self.getImages(opath)
                print liste
            if len(liste) == 0:
                print "WARNING : No valid images in "+self.path
            else:
                self.imRef = liste[0]
        except MonException, mess:
            print mess

    def getDateFromName(self,nameIm):

        imagePath = nameIm.split("/")
        #print nameIm
        nameimage = imagePath[-1].split("_")
        #print nameimage
        date = nameimage[3]

        return date

    def getTypeMask(self,name):
        chaine = name.split(".")
        typeMask = chaine[0].split('_')[-1]
        return typeMask

class Landsat8(Sensor):

    def __init__(self,path_image,opath,fconf,workRes,createFolder = "Create",
                 dicoBands={"B1":1 ,"B2":2 ,"B3":3 ,"B4":4 ,"B5":5 ,"B6":6 ,"B7":7}):
        Sensor.__init__(self)
        #Invariant Parameters
        if not createFolder:
            tmpPath = ""
        else:
            tmpPath = opath.opathT

        self.name = 'Landsat8'
        self.DatesVoulues = None
        self.path = path_image
        self.bands["BANDS"] = dicoBands
        self.nbBands = len(self.bands['BANDS'].keys())
        self.posDate = 3
        self.fimages = tmpPath+"/"+self.name+"imagesList.txt"
        self.fdates = tmpPath+"/"+self.name+"imagesDateList.txt"
        self.fImResize = tmpPath+"/"+self.name+"ImageResList.txt"
        self.fdatesRes = tmpPath+"/"+self.name+"ImageDateResList.txt"
        self.work_res = workRes

        # Users parameters
        cfg = Config(fconf)
        conf = cfg.Landsat8
        conf2 = cfg.GlobChain

        #bands definitions
        self.bands["BANDS"] = OrderedDict([(key, value) for key, value in sorted(dicoBands.iteritems(), key=lambda (k,v): (v,k))])
        self.red = self.bands["BANDS"]['B4']
        self.nir = self.bands["BANDS"]['B5']
        self.swir = self.bands["BANDS"]['B6']

        if cfg.iota2FeatureExtraction.extractBands == 'True':
            self.keepBands = OrderedDict([(k, v) for k, v in self.bands["BANDS"].items() if k in conf.keepBands])
            if cfg.GlobChain.features:
                try:
                    self.red = self.keepBands.keys().index('B4')
                except:
                    raise Exception ("red band is needed to compute features")
                try:
                    self.nir = self.keepBands.keys().index('B5')
                except:
                    raise Exception ("nir band is needed to compute features")
                try:
                    self.swir = self.keepBands.keys().index('B6')
                except:
                    raise Exception ("swir band is needed to compute features")
            else:
                self.red = self.nir = self.swir = -1

        #MASK
        self.sumMask = tmpPath+"/"+self.name+"_Sum_Mask.tif"
        self.borderMaskN = tmpPath+"/"+self.name+"_Border_MaskN.tif"
        self.borderMaskR = tmpPath+"/"+self.name+"_Border_MaskR.tif"

        #Time series
        self.serieTemp = tmpPath+"/"+self.name+"_ST_REFL.tif"
        self.serieTempMask = tmpPath+"/"+self.name+"_ST_MASK.tif"
        self.serieTempGap = tmpPath+"/"+self.name+"_ST_REFL_GAP.tif"
        #Indices
        self.indices = "NDVI","NDWI","Brightness"

        #DATA INFO
        self.struct_path = conf.arbo
        self.native_res = int(conf.nativeRes)
        self.imType = conf.imtype
        self.pathRes = tmpPath+"/LandRes_%sm/"%workRes
        self.proj = conf2.proj
        self.addFeatures = (conf.additionalFeatures).split(",")
        #MASK INFO
        self.nuages = conf.nuages
        self.saturation = conf.saturation
        self.div = conf.div
        self.nodata = conf.nodata
        self.pathmask = self.path+conf.arbomask

        if conf.nodata_Mask == 'False':
            self.nodata_MASK = False
        elif conf.nodata_Mask == "True":
            self.nodata_MASK = True
        else:
            print "Value Error for No Data Mask flag. NoDataMask not considered"
            self.nodata_MASK = False

        if self.native_res == self.work_res:
            self.borderMask = self.borderMaskN
        else:
            self.borderMask = self.borderMaskR
        try:
            liste = []
            if createFolder :
		liste = self.getImages(opath)
            if len(liste) == 0:
                print "WARNING : No valid images in "+self.path
            else:
                self.imRef = liste[0]
        except MonException, mess:
            print mess

    def getDateFromName(self,nameIm):

        imagePath = nameIm.split("/")
        #print nameIm
        nameimage = imagePath[-1].split("_")
        #print nameimage
        date = nameimage[3]
        return date

    def getTypeMask(self,name):
        chaine = name.split(".")
        typeMask = chaine[0].split('_')[-1]
        return typeMask

class Sentinel_2(Sensor):
    def __init__(self,path_image,opath,fconf,workRes,createFolder = "Create",
                 dicoBands={"B2":1 ,"B3":2 ,"B4":3 ,"B5":4 ,"B6":5 ,"B7":6 ,"B8":7,"B8A":8,"B11":9,"B12":10}):
        Sensor.__init__(self)
        #Invariant Parameters

        if not createFolder:
            tmpPath = ""
        else:
            tmpPath = opath.opathT

        self.name = 'Sentinel2'
        # Users parameters
        cfg = Config(fconf)
        conf = cfg.Sentinel_2
        conf2 = cfg.GlobChain

        self.DatesVoulues = None
        self.path = path_image

        #bands definitions
        self.bands["BANDS"] = OrderedDict([(key, value) for key, value in sorted(dicoBands.iteritems(), key=lambda (k,v): (v,k))])
        self.red = self.bands["BANDS"]['B4']
        self.nir = self.bands["BANDS"]['B8']
        self.swir = self.bands["BANDS"]['B11']

        if cfg.iota2FeatureExtraction.extractBands == 'True':
            self.keepBands = OrderedDict([(k, v) for k, v in self.bands["BANDS"].items() if k in conf.keepBands])
            if cfg.GlobChain.features:
                try:
                    self.red = self.keepBands.keys().index('B4')
                except:
                    raise Exception ("red band is needed to compute features")
                try:
                    self.nir = self.keepBands.keys().index('B8')
                except:
                    raise Exception ("nir band is needed to compute features")
                try:
                    self.swir = self.keepBands.keys().index('B11')
                except:
                    raise Exception ("swir band is needed to compute features")
            else:
                self.red = self.nir = self.swir = -1

        self.nbBands = len(self.bands['BANDS'].keys())

        self.fimages = tmpPath+"/"+self.name+"imagesList.txt"
        self.fdates = tmpPath+"/"+self.name+"imagesDateList.txt"
        self.fImResize = tmpPath+"/"+self.name+"ImageResList.txt"
        self.fdatesRes = tmpPath+"/"+self.name+"ImageDateResList.txt"
        self.posDate = 1
        self.work_res = workRes

        #MASK
        self.sumMask = tmpPath+"/"+self.name+"_Sum_Mask.tif"
        self.borderMaskN = tmpPath+"/"+self.name+"_Border_MaskN.tif"
        self.borderMaskR = tmpPath+"/"+self.name+"_Border_MaskR.tif"

        #Time series
        self.serieTemp = tmpPath+"/"+self.name+"_ST_REFL.tif"

        self.serieTempMask = tmpPath+"/"+self.name+"_ST_MASK.tif"
        self.serieTempGap = tmpPath+"/"+self.name+"_ST_REFL_GAP.tif"
        #Indices
        self.indices = "NDVI","NDWI","Brightness"

        #DATA INFO
        self.struct_path = conf.arbo
        self.native_res = int(conf.nativeRes)
        self.imType = conf.imtype
        self.pathRes = tmpPath+"/LandRes_%sm/"%workRes
        self.proj = conf2.proj

        self.addFeatures = (conf.additionalFeatures).split(",")
        #MASK INFO
        self.nuages = conf.nuages
        self.saturation = conf.saturation
        self.div = conf.div

        if conf.nuages_reproj : self.nuages = conf.nuages_reproj
        if conf.saturation_reproj : self.saturation = conf.saturation_reproj
        if conf.div_reproj : self.div = conf.div_reproj

        self.nodata = conf.nodata
        self.pathmask = self.path+conf.arbomask
        if conf.nodata_Mask == 'False':
            self.nodata_MASK = False
        elif conf.nodata_Mask == "True":
            self.nodata_MASK = True
        else:
            print "Value Error for No Data Mask flag. NoDataMask not considered"
            self.nodata_MASK = False

        if self.native_res == self.work_res:
            self.borderMask = self.borderMaskN
        else:
            self.borderMask = self.borderMaskR

        try:
            liste = []
            if createFolder :
		liste = self.getImages(opath)
	    	print liste
            if len(liste) == 0:
                print "WARNING : No valid images in "+self.path
            else:
                self.imRef = liste[0]
        except MonException, mess:
            print mess

    def getDateFromName(self,nameIm):

        date = nameIm.split("_")[1].split("-")[0]
        return date

    def getTypeMask(self,name):
        chaine = name.split(".")
        typeMask = chaine[0].split('_')[-1]
        return typeMask

class Spot4(Sensor):

    def __init__(self,path_image,opath,fconf,workRes,createFolder = "Create",dicoBands={'green' : 1 , 'red' : 2, 'NIR' : 3, 'SWIR' : 4}):
        Sensor.__init__(self)
        #Invariant Parameters
        self.name = 'Spot4'
	self.DatesVoulues = None
        self.path = path_image
        self.bands["BANDS"] = dicoBands
        self.nbBands = len(self.bands['BANDS'].keys())
        self.posDate = 3
        self.fimages = opath.opathT+"/SPOTimagesList.txt"
        self.fdates = opath.opathT+"/SPOTimagesDateList.txt"
        self.fImResize = opath.opathT+"/SPOTImageResList.txt"
        self.fdatesRes = opath.opathT+"/SPOTImageDateResList.txt"
        self.work_res = workRes

        #MASK
        self.sumMask = opath.opathT+"/SPOT_Sum_Mask.tif"
        self.borderMaskN = opath.opathT+"/SPOT_Border_MaskN.tif"
        self.borderMaskR = opath.opath+"/SPOT_Border_MaskR.tif"

        #Time series
        self.serieTemp = opath.opathT+"/SPOT_ST_REFL.tif"
        self.serieTempMask = opath.opathT+"/SPOT_ST_MASK.tif"
        self.serieTempGap = opath.opathT+"/SPOT_ST_REFL_GAP.tif"

        #Indices
        self.indices = "NDVI","NDWI","Brightness"

        # Users parameters
        cfg = Config(fconf)
        conf = cfg.SPOT4
        conf2 = cfg.GlobChain
        #DATA INFO
        self.struct_path = conf.arbo
        self.native_res = int(conf.nativeRes)
        self.imType = conf.imtype
        self.pathRes = opath.opathT+"/SpotRes_%sm/"%workRes
        self.proj = conf2.proj
	self.keepBands =  sorted((dict(conf.keepBands)).iteritems(),key = lambda (v,k):(v,k))#dict sorted by band number
        self.addFeatures = conf.additionalFeatures
        #MASK INFO
        self.nuages = conf.nuages
        self.saturation = conf.saturation
        self.div = conf.div
        self.nodata = conf.nodata
        self.pathmask = self.path+conf.arbomask

        if conf.nodata_Mask == 'False':
            self.nodata_MASK = False
        elif conf.nodata_Mask == "True":
            self.nodata_MASK = True
        else:
            print "Value Error for No Data Mask flag. NoDataMask not considered"
            self.nodata_MASK = False

        if self.native_res == self.work_res:
            self.borderMask = self.borderMaskN
        else:
            self.borderMask = self.borderMaskR

        try:
            liste = []
            if createFolder : liste = self.getImages(opath)
            if len(liste) == 0:
                print "WARNING : No valid images in "+self.path
            else:
                self.imRef = liste[0]
        except MonException, mess:
            print mess

    def getDateFromName(self,nameIm):

        imagePath = nameIm.split("/")
        nameimage = imagePath[-1].split("_")
        date = nameimage[3]

        return date

    def getTypeMask(self,name):
        chaine = name.split(".")
        typeMask = chaine[0].split('_')[-1]
        return typeMask
