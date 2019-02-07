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
import os

from GenSensors import Sensor
from GenSensors import MonException
from collections import OrderedDict

logger = logging.getLogger(__name__)

#in order to avoid issue 'No handlers could be found for logger...'
logger.addHandler(logging.NullHandler())


class Landsat5(Sensor):

    def __init__(self, path_image, opath, fconf, workRes, createFolder="Create",
                 dicoBands={"B1":1, "B2":2, "B3":3, "B4":4, "B5":5, "B6":6},
                 logger=logger):
        from Common import ServiceConfigFile as SCF

        Sensor.__init__(self)

        logger = logging.getLogger(__name__)

        #Invariant Parameters
        if not createFolder:
            tmpPath = ""
        else:
            tmpPath = opath.opathT

        cfg_IOTA2 = SCF.serviceConfigFile(fconf)
        sensorConfig = os.path.join(os.environ.get('IOTA2DIR'), "config", "sensors.cfg")
        cfg_sensors = SCF.serviceConfigFile(sensorConfig, iota_config=False)

        self.name = 'Landsat5'
        self.red = 3
        self.nir = 4
        self.swir = 5
        self.DatesVoulues = None
        self.path = path_image
        self.bands["BANDS"] = dicoBands
        self.nbBands = len(self.bands['BANDS'].keys())
        self.posDate = 3
        self.fimages = tmpPath+"/"+self.name+"imagesList.txt"
        self.fdates = tmpPath+""+self.name+"imagesDateList.txt"

        #MASK
        self.sumMask = tmpPath+"/"+self.name+"_Sum_Mask.tif"
        self.borderMaskN = tmpPath+"/"+self.name+"_Border_MaskN.tif"

        #Time series
        self.serieTemp = tmpPath+"/"+self.name+"_ST_REFL.tif"
        self.serieTempMask = tmpPath+"/"+self.name+"_ST_MASK.tif"
        self.serieTempGap = tmpPath+"/"+self.name+"_ST_REFL_GAP.tif"
        #Indices
        self.indices = "NDVI", "NDWI", "Brightness"

        #DATA INFO
        self.struct_path = cfg_sensors.getParam("Landsat5", "arbo")
        self.native_res = int(cfg_sensors.getParam("Landsat5", "nativeRes"))
        self.imType = cfg_sensors.getParam("Landsat5", "imtype")
        if not "none" in cfg_IOTA2.getParam("coregistration", "VHRPath").lower() and len(glob.glob(self.path + self.struct_path + '*COREG*' + os.path.splitext(self.imType)[1])) > 0 :
            imType = os.path.splitext(self.imType)
            self.imType = imType[0]+'_COREG'+imType[1]
        self.pathRes = tmpPath+"/LandRes_%sm/"%workRes
        self.proj = cfg_IOTA2.getParam("GlobChain", "proj")

        self.addFeatures = (cfg_IOTA2.getParam("Landsat5", "additionalFeatures")).split(",")
        #MASK INFO
        self.nuages = cfg_sensors.getParam("Landsat5", "nuages")
        self.saturation = cfg_sensors.getParam("Landsat5", "saturation")
        self.div = cfg_sensors.getParam("Landsat5", "div")
        self.nodata = cfg_sensors.getParam("Landsat5", "nodata")
        self.pathmask = self.path + cfg_sensors.getParam("Landsat5", "arbomask")
        if not "none" in cfg_IOTA2.getParam("coregistration", "VHRPath").lower() and len(glob.glob(self.pathmask + '*COREG*' + os.path.splitext(self.imType)[1])) > 0 :
            nuages = os.path.splitext(self.nuages)
            saturation = os.path.splitext(self.saturation)
            div = os.path.splitext(self.div)
            self.nuages = nuages[0] + '_COREG' + nuages[1]
            self.saturation = saturation[0] + '_COREG' + saturation[1]
            self.div = div[0] + '_COREG' + div[1]
        self.nodata_MASK = cfg_sensors.getParam("Landsat5", "nodata_Mask")
        self.borderMask = self.borderMaskN

        sensorEnable = (self.path is not None and len(self.path) > 0 and 'None' not in self.path)

        #bands definitions
        self.bands["BANDS"] = OrderedDict([(key, value) for key, value in sorted(dicoBands.iteritems(), key=lambda (k, v): (v, k))])
        self.red = self.bands["BANDS"]['B3']
        self.nir = self.bands["BANDS"]['B4']
        self.swir = self.bands["BANDS"]['B5']

        if sensorEnable and cfg_IOTA2.getParam("iota2FeatureExtraction", "extractBands") == True:
            self.keepBands = OrderedDict([(k, v) for k, v in self.bands["BANDS"].items() if k in cfg_IOTA2.getParam("Landsat5", "keepBands")])
            if cfg_IOTA2.getParam("GlobChain", "features"):
                try:
                    self.red = self.keepBands.keys().index('B3')
                except:
                    raise Exception("red band is needed to compute features")
                try:
                    self.nir = self.keepBands.keys().index('B4')
                except:
                    raise Exception("nir band is needed to compute features")
                try:
                    self.swir = self.keepBands.keys().index('B5')
                except:
                    raise Exception("swir band is needed to compute features")
            else:
                self.red = self.nir = self.swir = -1

        try:
            self.liste = []
            if createFolder and sensorEnable:
                self.liste = self.getImages(opath)
                if len(self.liste) == 0:
                    logger.warning('[Landsat5] No valid images found in {}'.format(self.path))
                else:
                    logger.debug('[Landsat5] Found the following images: {}'.format(self.liste))
                    self.imRef = self.liste[0]
        except MonException, mess:
            logger.error('[Landsat5] Exception caught: {}'.format(mess))


    def getDateFromName(self, nameIm):

        imagePath = nameIm.split("/")
        nameimage = imagePath[-1].split("_")
        date = nameimage[3]
        return date

    def getTypeMask(self, name):
        chaine = name.split(".")
        typeMask = chaine[0].split('_')[-1]
        return typeMask


class Landsat8(Sensor):

    def __init__(self, path_image, opath, fconf, workRes, createFolder="Create",
                 dicoBands={"B1":1, "B2":2, "B3":3, "B4":4, "B5":5, "B6":6, "B7":7},
                 logger=logger):
        from Common import ServiceConfigFile as SCF
        
        Sensor.__init__(self)
        
        logger = logging.getLogger(__name__)

        #Invariant Parameters
        if not createFolder:
            tmpPath = ""
        else:
            tmpPath = opath.opathT

        self.name = 'Landsat8'
        self.red = 4
        self.nir = 5
        self.swir = 6
        self.DatesVoulues = None
        self.path = path_image
        self.bands["BANDS"] = dicoBands
        self.nbBands = len(self.bands['BANDS'].keys())
        self.posDate = 3
        self.fimages = tmpPath+"/"+self.name+"imagesList.txt"
        self.fdates = tmpPath+"/"+self.name+"imagesDateList.txt"
        
        sensorEnable = (self.path is not None and len(self.path) > 0 and 'None' not in self.path)

        cfg_IOTA2 = SCF.serviceConfigFile(fconf)
        sensorConfig = os.path.join(os.environ.get('IOTA2DIR'), "config", "sensors.cfg")
        cfg_sensors = SCF.serviceConfigFile(sensorConfig, iota_config=False)
        
        #MASK
        self.sumMask = tmpPath+"/"+self.name+"_Sum_Mask.tif"
        self.borderMaskN = tmpPath+"/"+self.name+"_Border_MaskN.tif"

        #Time series
        self.serieTemp = tmpPath+"/"+self.name+"_ST_REFL.tif"
        self.serieTempMask = tmpPath+"/"+self.name+"_ST_MASK.tif"
        self.serieTempGap = tmpPath+"/"+self.name+"_ST_REFL_GAP.tif"
        #Indices
        self.indices = "NDVI", "NDWI", "Brightness"

        #DATA INFO
        self.struct_path = cfg_sensors.getParam("Landsat8", "arbo")
        self.native_res = int(cfg_sensors.getParam("Landsat8", "nativeRes"))
        self.imType = cfg_sensors.getParam("Landsat8", "imtype")
        if not "none" in cfg_IOTA2.getParam("coregistration", "VHRPath").lower() and len(glob.glob(self.path + self.struct_path + '*COREG*' + os.path.splitext(self.imType)[1])) > 0 :
            imType = os.path.splitext(self.imType)
            self.imType = imType[0]+'_COREG'+imType[1]
        self.pathRes = tmpPath+"/LandRes_%sm/"%workRes
        self.proj = cfg_IOTA2.getParam("GlobChain", "proj")

        self.addFeatures = (cfg_IOTA2.getParam("Landsat8", "additionalFeatures")).split(",")
        #MASK INFO
        self.nuages = cfg_sensors.getParam("Landsat8", "nuages")
        self.saturation = cfg_sensors.getParam("Landsat8", "saturation")
        self.div = cfg_sensors.getParam("Landsat8", "div")
        self.nodata = cfg_sensors.getParam("Landsat8", "nodata")
        self.pathmask = self.path + cfg_sensors.getParam("Landsat8", "arbomask")
        if not "none" in cfg_IOTA2.getParam("coregistration", "VHRPath").lower() and len(glob.glob(self.pathmask + '*COREG*' + os.path.splitext(self.imType)[1])) > 0 :
            nuages = os.path.splitext(self.nuages)
            saturation = os.path.splitext(self.saturation)
            div = os.path.splitext(self.div)
            self.nuages = nuages[0] + '_COREG' + nuages[1]
            self.saturation = saturation[0] + '_COREG' + saturation[1]
            self.div = div[0] + '_COREG' + div[1]
        self.nodata_MASK = cfg_sensors.getParam("Landsat8", "nodata_Mask")
        self.borderMask = self.borderMaskN
        
        #bands definitions
        self.bands["BANDS"] = OrderedDict([(key, value) for key, value in sorted(dicoBands.iteritems(), key=lambda (k, v): (v, k))])
        self.red = self.bands["BANDS"]['B4']
        self.nir = self.bands["BANDS"]['B5']
        self.swir = self.bands["BANDS"]['B6']

        if sensorEnable and cfg_IOTA2.getParam("iota2FeatureExtraction", "extractBands") == True:
            self.keepBands = OrderedDict([(k, v) for k, v in self.bands["BANDS"].items() if k in cfg_IOTA2.getParam("Landsat8", "keepBands")])
            if cfg_IOTA2.getParam("GlobChain", "features"):
                try:
                    self.red = self.keepBands.keys().index('B4')
                except:
                    raise Exception("red band is needed to compute features")
                try:
                    self.nir = self.keepBands.keys().index('B5')
                except:
                    raise Exception("nir band is needed to compute features")
                try:
                    self.swir = self.keepBands.keys().index('B6')
                except:
                    raise Exception("swir band is needed to compute features")
            else:
                self.red = self.nir = self.swir = -1

        try:
            self.liste = []
            if createFolder and sensorEnable:
                self.liste = self.getImages(opath)
                if len(self.liste) == 0:
                    logger.warning('[Landsat8] No valid images found in {}'.format(self.path))
                else:
                    logger.debug('[Landsat8] Found the following images: {}'.format(self.liste))
                    self.imRef = self.liste[0]
        except MonException, mess:
            logger.error('[Landsat8] Exception caught: {}'.format(mess))

    def getDateFromName(self, nameIm):

        imagePath = nameIm.split("/")
        nameimage = imagePath[-1].split("_")
        date = nameimage[3]
        return date

    def getTypeMask(self, name):
        chaine = name.split(".")
        typeMask = chaine[0].split('_')[-1]
        return typeMask


class Sentinel_2(Sensor):
    def __init__(self, path_image, opath, fconf, workRes, createFolder="Create",
                 dicoBands={"B2":1, "B3":2, "B4":3, "B5":4, "B6":5, "B7":6, "B8":7, "B8A":8, "B11":9, "B12":10},
                 logger=logger):
        from Common import ServiceConfigFile as SCF
        Sensor.__init__(self)

        logger = logging.getLogger(__name__)

        if not createFolder:
            tmpPath = ""
        else:
            tmpPath = opath.opathT

        self.name = 'Sentinel2'
        
        if os.path.exists(fconf):
            cfg_IOTA2 = SCF.serviceConfigFile(fconf)
            self.DatesVoulues = None

            # check output target directory
            output_target_dir = cfg_IOTA2.getParam("chain", "S2_output_path")
            if output_target_dir :
                path_image = os.path.normpath(path_image)
                path_image = path_image.split(os.sep)[-1]
                path_image = os.path.join(output_target_dir, path_image)

            self.path = path_image
            sensorEnable = (self.path is not None and len(self.path) > 0 and 'None' not in self.path)
            sensorConfig = os.path.join(os.environ.get('IOTA2DIR'), "config", "sensors.cfg")
            cfg_sensors = SCF.serviceConfigFile(sensorConfig, iota_config=False)

            #consts
            self.struct_path = cfg_sensors.getParam("Sentinel_2", "arbo")
            self.imType = cfg_sensors.getParam("Sentinel_2", "imtype")
            if not "none" in cfg_IOTA2.getParam("coregistration", "VHRPath").lower() and len(glob.glob(self.path + self.struct_path + '*COREG*' + os.path.splitext(self.imType)[1])) > 0 :
                imType = os.path.splitext(self.imType)
                self.imType = imType[0]+'_COREG'+imType[1]
            self.fimages = tmpPath+"/"+self.name+"imagesList.txt"
            
            #masks
            self.pathmask = self.path + cfg_sensors.getParam("Sentinel_2", "arbomask")
            self.nuages = cfg_sensors.getParam("Sentinel_2", "nuages")
            self.nodata = cfg_sensors.getParam("Sentinel_2", "nodata")
            self.serieTempMask = tmpPath+"/"+self.name+"_ST_MASK.tif"
            self.sumMask = tmpPath+"/"+self.name+"_Sum_Mask.tif"
            self.saturation = cfg_sensors.getParam("Sentinel_2", "saturation")
            self.div = cfg_sensors.getParam("Sentinel_2", "div")
            self.nuages = cfg_sensors.getParam("Sentinel_2", "nuages_reproj")
            self.saturation = cfg_sensors.getParam("Sentinel_2", "saturation_reproj")
            self.div = cfg_sensors.getParam("Sentinel_2", "div_reproj")
            if not "none" in cfg_IOTA2.getParam("coregistration", "VHRPath").lower() and len(glob.glob(self.pathmask + '*COREG*' + os.path.splitext(self.imType)[1])) > 0 :
                nuages = os.path.splitext(self.nuages)
                saturation = os.path.splitext(self.saturation)
                div = os.path.splitext(self.div)
                self.nuages = nuages[0] + '_COREG' + nuages[1]
                self.saturation = saturation[0] + '_COREG' + saturation[1]
                self.div = div[0] + '_COREG' + div[1]
            self.borderMaskN = tmpPath+"/"+self.name+"_Border_MaskN.tif"
            self.borderMask = self.borderMaskN
            self.serieTemp = tmpPath+"/"+self.name+"_ST_REFL.tif"
            self.serieTempGap = tmpPath+"/"+self.name+"_ST_REFL_GAP.tif"
            self.nodata_MASK = cfg_sensors.getParam("Sentinel_2", "nodata_Mask")

            self.addFeatures = (cfg_IOTA2.getParam("Sentinel_2", "additionalFeatures")).split(",")
            
            self.indices = "NDVI", "NDWI", "Brightness"
            self.fdates = tmpPath+"/"+self.name+"imagesDateList.txt"
            self.posDate = 1
            self.native_res = int(cfg_sensors.getParam("Sentinel_2", "nativeRes"))
            self.pathRes = tmpPath+"/LandRes_%sm/"%workRes

            self.proj = cfg_IOTA2.getParam("GlobChain", "proj")
            
            self.imRef = None
            
            #bands definitions
            self.bands["BANDS"] = OrderedDict([(key, value) for key, value in sorted(dicoBands.iteritems(), key=lambda (k, v): (v, k))])
            self.red = self.bands["BANDS"]['B4']
            self.nir = self.bands["BANDS"]['B8']
            self.swir = self.bands["BANDS"]['B11']

            self.keepBands = None
            if sensorEnable and cfg_IOTA2.getParam("iota2FeatureExtraction", "extractBands") == True:
                self.keepBands = OrderedDict([(k, v) for k, v in self.bands["BANDS"].items() if k in cfg_IOTA2.getParam("Sentinel_2", "keepBands")])
                if cfg_IOTA2.getParam("GlobChain", "features"):
                    try:
                        self.red = self.keepBands.keys().index('B4')
                    except:
                        raise Exception("red band is needed to compute features")
                    try:
                        self.nir = self.keepBands.keys().index('B8')
                    except:
                        raise Exception("nir band is needed to compute features")
                    try:
                        self.swir = self.keepBands.keys().index('B11')
                    except:
                        raise Exception("swir band is needed to compute features")
                else:
                    self.red = self.nir = self.swir = -1

            self.nbBands = len(self.bands['BANDS'].keys())

            try:
                self.liste = []
                if createFolder and sensorEnable:
                    self.liste = self.getImages(opath)
                    if len(self.liste) == 0:
                        logger.warning('[Sentinel2] No valid images found in {}'.format(self.path))
                    else:
                        logger.debug('[Sentinel2] Found the following images: {}'.format(self.liste))
                        self.imRef = self.liste[0]
            except MonException, mess:
                logger.error('[Sentinel2] Exception caught: {}'.format(mess))

    def getDateFromName(self, nameIm):
        date = nameIm.split("_")[1].split("-")[0]
        return date

    def getTypeMask(self, name):
        chaine = name.split(".")
        typeMask = chaine[0].split('_')[-1]
        return typeMask

        logger = logging.getLogger(__name__)
        sensorEnable = (self.path is not None and len(self.path) > 0 and 'None' not in self.path)

        if sensorEnable:
            logger.warning("[Spot4] Invalid value for No Data Mask flag in configuration file. NoDataMask not considered")
        if createFolder and sensorEnable:
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

    def __init__(self, path_image, opath, fconf, workRes, createFolder="Create",
                 dicoBands={"B2":1 ,"B3":2 ,"B4":3 ,"B5":4 ,"B6":5 ,"B7":6 ,"B8":7,"B8A":8,"B11":9,"B12":10},
                 logger=logger):
        Sensor.__init__(self)

        from Common import ServiceConfigFile as SCF
        
        tmpPath = ""
        self.name = 'Sentinel2S2C'
        #date position in image's name if split by "_"
        self.posDate = 2

        if os.path.exists(fconf):
            cfg_IOTA2 = SCF.serviceConfigFile(fconf)
            # check output target directory
            output_target_dir = cfg_IOTA2.getParam("chain", "S2_S2C_output_path")
            if output_target_dir :
                path_image = os.path.normpath(path_image)
                path_image = path_image.split(os.sep)[-1]
                path_image = os.path.join(output_target_dir, path_image)

            self.path = path_image
            self.fdates = os.path.join(tmpPath, self.name + "imagesDateList.txt")
            self.imRef = None
            sensorEnable = (self.path is not None and len(self.path) > 0 and 'None' not in self.path)
            sensorConfig = os.path.join(os.environ.get('IOTA2DIR'), "config", "sensors.cfg")
            cfg_sensors = SCF.serviceConfigFile(sensorConfig, iota_config=False)

            self.struct_path = cfg_sensors.getParam("Sentinel_2_S2C", "arbo")
            self.imType = cfg_sensors.getParam("Sentinel_2_S2C", "imtype")
            if not "none" in cfg_IOTA2.getParam("coregistration", "VHRPath").lower() and len(glob.glob(self.path + self.struct_path + '*COREG*' + os.path.splitext(self.imType)[1])) > 0 :
                imType = os.path.splitext(self.imType)
                self.imType = imType[0]+'_COREG'+imType[1]

            if not createFolder:
                tmpPath = ""
            else:
                tmpPath = opath.opathT

            self.fimages = tmpPath+"/"+self.name+"imagesList.txt"
            self.borderMaskN = tmpPath+"/"+self.name+"_Border_MaskN.tif"
            self.serieTempMask = tmpPath+"/"+self.name+"_ST_MASK.tif"
            self.serieTemp = tmpPath+"/"+self.name+"_ST_REFL.tif"
            self.serieTempMask = tmpPath+"/"+self.name+"_ST_MASK.tif"
            self.serieTempGap = tmpPath+"/"+self.name+"_ST_REFL_GAP.tif"
            
            self.pathmask = self.path + cfg_sensors.getParam("Sentinel_2_S2C", "arbomask")
            self.nuages = cfg_sensors.getParam("Sentinel_2_S2C", "nuages")
            if not "none" in cfg_IOTA2.getParam("coregistration", "VHRPath").lower() and len(glob.glob(self.pathmask + '*COREG*' + os.path.splitext(self.imType)[1])) > 0 :
                nuages = os.path.splitext(self.nuages)
                self.nuages = nuages[0] + '_COREG' + nuages[1]
            self.nodata = cfg_sensors.getParam("Sentinel_2_S2C", "nodata")
            self.addFeatures = (cfg_IOTA2.getParam("Sentinel_2_S2C", "additionalFeatures")).split(",")
            
            self.bands["BANDS"] = OrderedDict([(key, value) for key, value in sorted(dicoBands.iteritems(), key=lambda (k,v): (v,k))])
            self.red = self.bands["BANDS"]['B4']
            self.nir = self.bands["BANDS"]['B8']
            self.swir = self.bands["BANDS"]['B11']

            self.keepBands = None
            if sensorEnable and cfg_IOTA2.getParam("iota2FeatureExtraction", "extractBands") == True:
                self.keepBands = OrderedDict([(k, v) for k, v in self.bands["BANDS"].items() if k in cfg_IOTA2.getParam("Sentinel_2_S2C", "keepBands")])
                if cfg_IOTA2.getParam("GlobChain", "features"):
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

    def getDateFromName(self, nameIm, complete_date=False):
        """ extract date from sen2cor image's name
        complete_date use also HH,MM,SS
        """
        import os
        date = os.path.splitext(os.path.basename(nameIm))[0].split("_")[self.posDate].split("T")[0]
        if complete_date:
            date = os.path.splitext(os.path.basename(nameIm))[0].split("_")[self.posDate]
        return date

    def CreateBorderMask_bindings(self, opath, wMode=False):
        """ usage : use to determine if a pixel if almost see one time by the sensor
        """
        from Common import OtbAppBank as otbApp
        mlist = self.getList_NoDataMask()
        border_exp = " + ".join(["im{}b1".format(i+1) for i in range(len(mlist))])
        border_app = otbApp.CreateBandMathApplication({"il": mlist,
                                                       "exp": "{}>0?1:0".format(border_exp),
                                                       "pixType" : "uint8"})
        return border_app, "", ""

    def createMaskSeries_bindings(self, opath, maskC, wMode=False, logger=logger):
        """ usage : create masks temporal serie ready to use for gapfilling
        """
        from Common import OtbAppBank as otbApp
        import otbApplication as otb
        #output 1 mean "to interpolate"
        mlist = self.getList_CloudMask()
        mask_serie = otbApp.CreateConcatenateImagesApplication({"il": mlist})
        mask_serie.Execute()
        mask_serie_common = otb.Registry.CreateApplication("BandMathX")
        mask_serie_common.AddParameterStringList("il", maskC)
        mask_serie_common.AddImageToParameterInputImageList("il",
                                                            mask_serie.GetParameterOutputImage("out"))
        mask_serie_common.SetParameterString("exp", "im1b1 * im2")
        mask_serie_common.SetParameterString("out", self.serieTempMask)

        return mask_serie_common, mask_serie

