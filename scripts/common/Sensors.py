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
import logging
import glob

from GenSensors import Sensor
from GenSensors import MonException
from collections import OrderedDict
import logging

logger = logging.getLogger(__name__)

#in order to avoid issue 'No handlers could be found for logger...'
logger.addHandler(logging.NullHandler())


class Landsat5(Sensor):

    def __init__(self,path_image,opath,fconf,workRes,createFolder = "Create",
                 dicoBands={"B1":1 ,"B2":2 ,"B3":3 ,"B4":4 ,"B5":5 ,"B6":6},
                 logger=logger):
        Sensor.__init__(self)

        logger = logging.getLogger(__name__)

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

        # Users parameters
        cfg = Config(fconf)
        conf = cfg.Landsat5
        conf2 = cfg.GlobChain

        sensorEnable = (self.path is not None and len(self.path) > 0 and 'None' not in self.path)

        #bands definitions
        self.bands["BANDS"] = OrderedDict([(key, value) for key, value in sorted(dicoBands.iteritems(), key=lambda (k,v): (v,k))])
        self.red = self.bands["BANDS"]['B3']
        self.nir = self.bands["BANDS"]['B4']
        self.swir = self.bands["BANDS"]['B5']

        if sensorEnable and cfg.iota2FeatureExtraction.extractBands == True:
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
        if conf.nodata_Mask == False:
            self.nodata_MASK = False
        elif conf.nodata_Mask == True:
            self.nodata_MASK = True
        else:
            if sensorEnable:
                logger.warning("[Landsat5] Invalid value for No Data Mask flag in configuration file. NoDataMask not considered")
            self.nodata_MASK = False

        self.borderMask = self.borderMaskN

        try:
            self.liste = []
            if createFolder and sensorEnable :
                self.liste = self.getImages(opath)
                if len(self.liste) == 0:
                    logger.warning('[Landsat5] No valid images found in {}'.format(self.path))
                else:
                    logger.debug('[Landsat5] Found the following images: {}'.format(self.liste))
                    self.imRef = self.liste[0]
        except MonException, mess:
            logger.error('[Landsat5] Exception caught: {}'.format(mess))


    def getDateFromName(self,nameIm):

        imagePath = nameIm.split("/")
        nameimage = imagePath[-1].split("_")
        date = nameimage[3]
        return date

    def getTypeMask(self,name):
        chaine = name.split(".")
        typeMask = chaine[0].split('_')[-1]
        return typeMask

class Landsat8(Sensor):

    def __init__(self,path_image,opath,fconf,workRes,createFolder = "Create",
                 dicoBands={"B1":1 ,"B2":2 ,"B3":3 ,"B4":4 ,"B5":5 ,"B6":6 ,"B7":7},
                 logger=logger):
        Sensor.__init__(self)

        logger = logging.getLogger(__name__)

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

        # Users parameters
        cfg = Config(fconf)
        conf = cfg.Landsat8
        conf2 = cfg.GlobChain

        sensorEnable = (self.path is not None and len(self.path) > 0 and 'None' not in self.path)
        
        #bands definitions
        self.bands["BANDS"] = OrderedDict([(key, value) for key, value in sorted(dicoBands.iteritems(), key=lambda (k,v): (v,k))])
        self.red = self.bands["BANDS"]['B4']
        self.nir = self.bands["BANDS"]['B5']
        self.swir = self.bands["BANDS"]['B6']

        if sensorEnable and cfg.iota2FeatureExtraction.extractBands == True:
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

        if conf.nodata_Mask == False:
            self.nodata_MASK = False
        elif conf.nodata_Mask == True:
            self.nodata_MASK = True
        else:
            if sensorEnable:
                logger.warning("[Landsat8] Invalid value for No Data Mask flag in configuration file. NoDataMask not considered")
            self.nodata_MASK = False

        self.borderMask = self.borderMaskN

        try:
            self.liste = []
            if createFolder and sensorEnable :
                self.liste = self.getImages(opath)
                if len(self.liste) == 0:
                    logger.warning('[Landsat8] No valid images found in {}'.format(self.path))
                else:
                    logger.debug('[Landsat8] Found the following images: {}'.format(self.liste))
                    self.imRef = self.liste[0]
        except MonException, mess:
            logger.error('[Landsat8] Exception caught: {}'.format(mess))

    def getDateFromName(self,nameIm):

        imagePath = nameIm.split("/")
        nameimage = imagePath[-1].split("_")
        date = nameimage[3]
        return date

    def getTypeMask(self,name):
        chaine = name.split(".")
        typeMask = chaine[0].split('_')[-1]
        return typeMask

class Sentinel_2(Sensor):
    def __init__(self, path_image, opath, fconf, workRes, createFolder = "Create",
                 dicoBands={"B2":1 ,"B3":2 ,"B4":3 ,"B5":4 ,"B6":5 ,"B7":6 ,"B8":7,"B8A":8,"B11":9,"B12":10},
                 logger=logger):
        Sensor.__init__(self)

        logger = logging.getLogger(__name__)

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

        sensorEnable = (self.path is not None and len(self.path) > 0 and 'None' not in self.path)
        #bands definitions
        self.bands["BANDS"] = OrderedDict([(key, value) for key, value in sorted(dicoBands.iteritems(), key=lambda (k,v): (v,k))])
        self.red = self.bands["BANDS"]['B4']
        self.nir = self.bands["BANDS"]['B8']
        self.swir = self.bands["BANDS"]['B11']

        self.keepBands = None
        if sensorEnable and cfg.iota2FeatureExtraction.extractBands == True:
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
        self.posDate = 1

        #MASK
        self.sumMask = tmpPath+"/"+self.name+"_Sum_Mask.tif"
        self.borderMaskN = tmpPath+"/"+self.name+"_Border_MaskN.tif"

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
        self.imRef = None
        if conf.nuages_reproj:
            self.nuages = conf.nuages_reproj
        if conf.saturation_reproj:
            self.saturation = conf.saturation_reproj
        if conf.div_reproj:
            self.div = conf.div_reproj

        self.nodata = conf.nodata
        self.pathmask = self.path+conf.arbomask
        if conf.nodata_Mask == False:
            self.nodata_MASK = False
        elif conf.nodata_Mask == True:
            self.nodata_MASK = True
        else:
            if sensorEnable:
                logger.warning("[Sentinel2] Invalid value for No Data Mask flag in configuration file. NoDataMask not considered")
            self.nodata_MASK = False

        self.borderMask = self.borderMaskN

        try:
            self.liste = []
            if createFolder and sensorEnable :
                self.liste = self.getImages(opath)
                if len(self.liste)==0:
                    logger.warning('[Sentinel2] No valid images found in {}'.format(self.path))
                else:
                    logger.debug('[Sentinel2] Found the following images: {}'.format(self.liste))
                    self.imRef = self.liste[0]
        except MonException, mess:
            logger.error('[Sentinel2] Exception caught: {}'.format(mess))

    def getDateFromName(self,nameIm):
        date = nameIm.split("_")[1].split("-")[0]
        return date

    def getTypeMask(self,name):
        chaine = name.split(".")
        typeMask = chaine[0].split('_')[-1]
        return typeMask

        logger = logging.getLogger(__name__)
        sensorEnable = (self.path is not None and len(self.path) > 0 and 'None' not in self.path)

        if sensorEnable:
                logger.warning("[Spot4] Invalid value for No Data Mask flag in configuration file. NoDataMask not considered")
        if createFolder and sensorEnable : 
            try:
                liste = self.getImages(opath)

                if len(liste) == 0:
                    logger.warning('[Spot4] No valid images found in {}'.format(self.path))
                else:
                    logger.debug('[Spot4] Found the following images: {}'.format(liste))
                    self.imRef = liste[0]
            except MonException, mess:
                logger.error('[Spot4] Exception caught: {}'.format(mess))


class Sentinel_2_S2C(Sensor):

    def __init__(self, path_image, opath, fconf, workRes, createFolder = "Create",
                 dicoBands={"B2":1 ,"B3":2 ,"B4":3 ,"B5":4 ,"B6":5 ,"B7":6 ,"B8":7,"B8A":8,"B11":9,"B12":10},
                 logger=logger):
        Sensor.__init__(self)
        
        #date position in image's name if split by "_"
        self.posDate = 2

    def getDateFromName(self, nameIm, complete_date=False):
        """ extract date from sen2cor image's name
        complete_date use also HH,MM,SS
        """
        import os
        date = os.path.splitext(os.path.basename(nameIm))[0].split("_")[self.posDate].split("T")[0]
        if complete_date:
            date = os.path.splitext(os.path.basename(nameIm))[0].split("_")[self.posDate]
        return date
                     
                     
                     
                     
                     