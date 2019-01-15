# -*- coding: utf-8 -*-

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

    name = 'Landsat5'

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
        sensorConfig = (cfg_IOTA2.getParam("chain", "pyAppPath")).split(os.path.sep)
        sensorConfig = (os.path.sep).join(sensorConfig[0:-1] + ["config", "sensors.cfg"])
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
        self.pathRes = tmpPath+"/LandRes_%sm/"%workRes
        self.proj = cfg_IOTA2.getParam("GlobChain", "proj")

        self.addFeatures = (cfg_IOTA2.getParam("Landsat5", "additionalFeatures")).split(",")
        #MASK INFO
        self.nuages = cfg_sensors.getParam("Landsat5", "nuages")
        self.saturation = cfg_sensors.getParam("Landsat5", "saturation")
        self.div = cfg_sensors.getParam("Landsat5", "div")
        self.nodata = cfg_sensors.getParam("Landsat5", "nodata")
        self.pathmask = self.path + cfg_sensors.getParam("Landsat5", "arbomask")
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
    name = 'Landsat8'
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
        sensorConfig = (cfg_IOTA2.getParam("chain", "pyAppPath")).split(os.path.sep)
        sensorConfig = (os.path.sep).join(sensorConfig[0:-1] + ["config", "sensors.cfg"])
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
        self.pathRes = tmpPath+"/LandRes_%sm/"%workRes
        self.proj = cfg_IOTA2.getParam("GlobChain", "proj")

        self.addFeatures = (cfg_IOTA2.getParam("Landsat8", "additionalFeatures")).split(",")
        #MASK INFO
        self.nuages = cfg_sensors.getParam("Landsat8", "nuages")
        self.saturation = cfg_sensors.getParam("Landsat8", "saturation")
        self.div = cfg_sensors.getParam("Landsat8", "div")
        self.nodata = cfg_sensors.getParam("Landsat8", "nodata")
        self.pathmask = self.path + cfg_sensors.getParam("Landsat8", "arbomask")
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
    name = 'Sentinel2'
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
            sensorConfig = (cfg_IOTA2.getParam("chain", "pyAppPath")).split(os.path.sep)
            sensorConfig = (os.path.sep).join(sensorConfig[0:-1] + ["config", "sensors.cfg"])
            cfg_sensors = SCF.serviceConfigFile(sensorConfig, iota_config=False)

            #consts
            self.struct_path = cfg_sensors.getParam("Sentinel_2", "arbo")
            self.imType = cfg_sensors.getParam("Sentinel_2", "imtype")
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


class Sentinel_2_L3A(Sensor):

    name = 'Sentinel2L3A'

    def __init__(self, config_path, tile_name):
        from Common import ServiceConfigFile as SCF
        Sensor.__init__(self)

        if not os.path.exists(config_path):
            return

        cfg_IOTA2 = SCF.serviceConfigFile(config_path)
        cfg_sensors = (cfg_IOTA2.getParam("chain", "pyAppPath")).split(os.path.sep)
        cfg_sensors = (os.path.sep).join(cfg_sensors[0:-1] + ["config", "sensors.cfg"])
        cfg_sensors = SCF.serviceConfigFile(cfg_sensors, iota_config=False)
        
        # attributes
        self.s2_l3a_data = cfg_IOTA2.getParam("chain", "S2_L3A_Path")
        self.all_tiles = cfg_IOTA2.getParam("chain", "listTile")

        output_target_dir = cfg_IOTA2.getParam("chain", "S2_L3A_output_path")
        self.tile_name = tile_name
        self.tile_directory = os.path.join(self.s2_l3a_data, tile_name)
        self.target_proj = int(cfg_IOTA2.getParam("GlobChain", "proj").lower().replace(" ","").replace("epsg:",""))
        self.struct_path_data = cfg_sensors.getParam("Sentinel_2_L3A", "arbo")
        self.struct_path_masks = cfg_sensors.getParam("Sentinel_2_L3A", "arbomask")
        self.suffix = "STACK"
        self.suffix_mask = "BINARY_MASK"
        self.masks_pattern = "FLG_R1.tif"
        self.masks_values = [0, 1] # NODATA, CLOUD
        self.date_position = 1 # if date's name split by "_"
        self.features_dir = os.path.join(cfg_IOTA2.getParam("chain", "outputPath"),
                                         "features", tile_name)
        extract_bands = cfg_IOTA2.getParam("Sentinel_2_L3A", "keepBands")
        extract_bands_flag = cfg_IOTA2.getParam("iota2FeatureExtraction", "extractBands")

        # outputs
        self.footprint_name = "{}_{}_footprint.tif".format(self.__class__.name,
                                                           tile_name)
        self.time_series_name = "{}_{}_TS.tif".format(self.__class__.name,
                                                      tile_name)
        self.time_series_gapfilling_name = "{}_{}_TSG.tif".format(self.__class__.name,
                                                                  tile_name)
        self.time_series_masks_name = "{}_{}_MASKS.tif".format(self.__class__.name,
                                                               tile_name)
        self.features_names = "{}_{}_Features.tif".format(self.__class__.name,
                                                          tile_name)
        # bands order
        self.stack_band_position = ["B2", "B3", "B4", "B5", "B6",
                                    "B7", "B8", "B8A", "B11", "B12"]
        # TODO move into the base-class
        self.extracted_bands = None
        if extract_bands_flag:
            self.extracted_bands = [(band_name, band_position + 1) for band_position, band_name in enumerate(self.stack_band_position) if band_name in cfg_IOTA2.getParam("Sentinel_2_L3A", "keepBands")]

        # about gapFilling interpolations
        self.temporal_res = cfg_IOTA2.getParam("Sentinel_2_L3A", "temporalResolution")
        self.input_dates = "{}_{}_input_dates.txt".format(self.__class__.name,
                                                           tile_name)
        self.interpolated_dates = "{}_{}_interpolation_dates.txt".format(self.__class__.name,
                                                                         tile_name)
        if output_target_dir:
            self.output_preprocess_directory = os.path.join(output_target_dir, tile_name)
            if not os.path.exists(self.output_preprocess_directory):
                try:
                    os.mkdir(self.output_preprocess_directory)
                except:
                    pass
        else :
            self.output_preprocess_directory = self.tile_directory
        
    def get_available_dates(self):
        """
        return sorted available dates
        """
        from Common.FileUtils import FileSearch_AND

        stacks = sorted(FileSearch_AND(self.output_preprocess_directory, True, "{}.tif".format(self.suffix)),
                        key=lambda x : os.path.basename(x).split("_")[self.date_position].split("-")[0])
        return stacks

    def build_stack_date_name(self, date_dir):
        """
        """
        from Common.FileUtils import FileSearch_AND
        _, b2_name = os.path.split(FileSearch_AND(date_dir, True, "FRC_B2.tif")[0])
        return b2_name.replace("FRC_B2.tif", "FRC_{}.tif".format(self.suffix))

    def preprocess_date(self, date_dir, out_prepro, working_dir=None, ram=128,
                        logger=logger):
        """
        """
        import os
        import shutil
        from gdal import Warp
        from Common.FileUtils import getRasterProjectionEPSG
        from Common.FileUtils import FileSearch_AND
        from Common.OtbAppBank import CreateConcatenateImagesApplication

        # manage directories
        date_stack_name = self.build_stack_date_name(date_dir)
        logger.debug("preprocessing {}".format(date_dir))
        out_stack = os.path.join(date_dir, date_stack_name)
        if out_prepro:
            _, date_dir_name = os.path.split(date_dir)
            out_dir = os.path.join(out_prepro, date_dir_name)
            if not os.path.exists(out_dir):
                try:
                    os.mkdir(out_dir)
                except:
                    logger.warning("{} already exists".format(out_dir))
            out_stack = os.path.join(out_dir, date_stack_name)

        out_stack_processing = out_stack
        if working_dir:
            out_stack_processing = os.path.join(working_dir, date_stack_name)

        # get bands
        b2 = FileSearch_AND(date_dir, True, "FRC_B2.tif")[0]
        b3 = FileSearch_AND(date_dir, True, "FRC_B3.tif")[0]
        b4 = FileSearch_AND(date_dir, True, "FRC_B4.tif")[0]
        b5 = FileSearch_AND(date_dir, True, "FRC_B5.tif")[0]
        b6 = FileSearch_AND(date_dir, True, "FRC_B6.tif")[0]
        b7 = FileSearch_AND(date_dir, True, "FRC_B7.tif")[0]
        b8 = FileSearch_AND(date_dir, True, "FRC_B8.tif")[0]
        b8a = FileSearch_AND(date_dir, True, "FRC_B8A.tif")[0]
        b11 = FileSearch_AND(date_dir, True, "FRC_B11.tif")[0]
        b12 = FileSearch_AND(date_dir, True, "FRC_B12.tif")[0]

        # resample bands
        (b5_10m, b6_10m,
         b7_10m, b8a_10m,
         b11_10m, b12_10m) = [self.resample(band, 10, out_prepro, working_dir, ram) for band in [b5, b6, b7, b8a, b11, b12]]

        # stack bands
        logger.info("Creating : {}".format(out_stack))
        stack_bands = CreateConcatenateImagesApplication({"il": [b2, b3, b4, b5_10m,
                                                                 b6_10m, b7_10m, b8,
                                                                 b8a_10m, b11_10m, b12_10m],
                                                          "out": out_stack_processing,
                                                          "ram": str(ram)})
        if not os.path.exists(out_stack):
            stack_bands.ExecuteAndWriteOutput()
            if working_dir:
                shutil.copy(out_stack_processing, out_stack)
                os.remove(out_stack_processing)

        # reproject if needed
        stack_projection = getRasterProjectionEPSG(out_stack)
        if int(self.target_proj) != int(stack_projection):
            logger.info("Reprojecting {}".format(out_stack))
            ds = Warp(out_stack, out_stack,
                      multithread=True, format="GTiff", xRes=10, yRes=10,
                      srcSRS="EPSG:{}".format(stack_projection), dstSRS="EPSG:{}".format(self.target_proj),
                      options=["INIT_DEST=-10000"])
            logger.info("Reprojection succeed")
        logger.info("End preprocessing")

    def resample(self, band, out_size, out_prepro, working_dir, ram, logger=logger):
        """
        """
        import os
        import shutil
        from Common.OtbAppBank import CreateRigidTransformResampleApplication
        from Common.FileUtils import readRaster

        # manage directories
        out_band_name = os.path.split(band)[1].replace(".tif", "_10M.tif")
        _, date_dir_name = os.path.split(os.path.dirname(band))
        out_band = os.path.join(date_dir_name, out_band_name)
        if out_prepro:
            out_dir = os.path.join(out_prepro, date_dir_name)
            out_band = os.path.join(out_dir, out_band_name)
        out_band_processing = out_band
        if working_dir:
            out_band_processing = os.path.join(working_dir, out_band_name)

        # resampling
        if not os.path.exists(out_band):
            logger.info("Creating {}".format(out_band_processing))
            _, _, _, (_, x_res, _, _, _, y_res) = readRaster(band)
            rigid_app = CreateRigidTransformResampleApplication({"in":band, 
                                                                 "transform.type.id.scalex": float(x_res) / float(out_size),
                                                                 "transform.type.id.scaley": float(x_res) / float(out_size),
                                                                 "ram":ram,
                                                                 "out":out_band_processing})
            rigid_app.ExecuteAndWriteOutput()

            if working_dir:
                shutil.copy(out_band_processing, out_band)
                os.remove(out_band_processing)

        return out_band

    def preprocess_date_masks(self, date_dir, out_prepro,
                              working_dir=None, ram=128,
                              logger=logger):
        """
        """
        from gdal import Warp
        import shutil
        from Common.FileUtils import ensure_dir
        from Common.OtbAppBank import CreateBandMathApplication
        from Common.FileUtils import getRasterProjectionEPSG

        # TODO : throw Exception if no masks are found
        date_mask = glob.glob(os.path.join(date_dir, "{}{}".format(self.struct_path_masks, self.masks_pattern)))[0]

        # manage directories
        mask_dir = os.path.dirname(date_mask)
        logger.debug("preprocessing {} masks".format(mask_dir))
        mask_name = os.path.basename(date_mask).replace(self.masks_pattern,
                                                        "{}.tif".format(self.suffix_mask))
        out_mask = os.path.join(mask_dir, mask_name)
        if out_prepro:
            _, date_dir_name = os.path.split(mask_dir)
            out_mask_dir = mask_dir.replace(os.path.join(self.s2_l3a_data, self.tile_name), out_prepro)
            ensure_dir(out_mask_dir, raise_exe=False)
            out_mask = os.path.join(out_mask_dir, mask_name)

        out_mask_processing = out_mask
        if working_dir:
            out_mask_processing = os.path.join(working_dir, mask_name)

        # compute mask
        if not os.path.exists(out_mask):
            mask_exp = "?1:".join(["im1b1=={}".format(value) for value in self.masks_values])
            mask_exp = "{}?1:0".format(mask_exp)
            mask_gen = CreateBandMathApplication({"il": date_mask,
                                                  "ram": str(ram),
                                                  "exp": mask_exp, 
                                                  "pixType": "uint8",
                                                  "out":out_mask_processing})
            mask_gen.ExecuteAndWriteOutput()
            if working_dir:
                shutil.copy(out_mask_processing, out_mask)
                os.remove(out_mask_processing)

        # reproject if needed
        mask_projection = getRasterProjectionEPSG(out_mask)
        if int(self.target_proj) != int(mask_projection):
            logger.info("Reprojecting {}".format(out_mask))
            ds = Warp(out_mask_processing, out_mask,
                      multithread=True, format="GTiff", xRes=10, yRes=10,
                      srcSRS="EPSG:{}".format(mask_projection), dstSRS="EPSG:{}".format(self.target_proj),
                      options=["INIT_DEST=0"])
            if working_dir:
                shutil.copy(out_mask_processing, out_mask)
                os.remove(out_mask_processing)
            logger.info("Reprojection succeed")
        logger.info("End preprocessing")

        
    def preprocess(self, working_dir=None, ram=128, logger=logger):
        """
        """
        input_dates = [os.path.join(self.tile_directory, cdir) for cdir in os.listdir(self.tile_directory)]
        for date in input_dates:
            self.preprocess_date(date, self.output_preprocess_directory,
                                 working_dir, ram)
            self.preprocess_date_masks(date, self.output_preprocess_directory,
                                       working_dir, ram)

    def footprint(self, ram=128):
        """
        in this case (L3A), we consider the whole tile
        """
        from Common.OtbAppBank import CreateBandMathApplication
        from Common.FileUtils import ensure_dir
        
        date = self.get_available_dates()[0]
        footprint_dir = os.path.join(self.features_dir, "tmp")
        ensure_dir(footprint_dir,raise_exe=False)
        footprint_out = os.path.join(footprint_dir, self.footprint_name)
        
        s2_l3a_border = CreateBandMathApplication({"il": date,
                                                   "out": footprint_out,
                                                   "exp":"1",
                                                   "ram": str(ram)})
        # needed to travel throught iota2's library
        app_dep = []

        return s2_l3a_border, app_dep

    def write_interpolation_dates_file(self):
        """
        """
        from Common.FileUtils import getDateS2
        from Common.FileUtils import ensure_dir
        from Common.FileUtils import dateInterval
        
        interp_date_dir = os.path.join(self.features_dir, "tmp")
        ensure_dir(interp_date_dir, raise_exe=False)
        interp_date_file = os.path.join(interp_date_dir, self.interpolated_dates)
        # get dates in the whole S2 data-set
        date_interp_min, date_interp_max = getDateS2(self.s2_l3a_data, self.all_tiles.split(" "))
        dates = [str(date).replace("-","") for date in dateInterval(date_interp_min, date_interp_max, self.temporal_res)]
        if not os.path.exists(interp_date_file):
            with open(interp_date_file, "w") as interpolation_date_file:
                interpolation_date_file.write("\n".join(dates))
        return interp_date_file, dates

    def write_dates_file(self):
        """
        """
        from Common.FileUtils import ensure_dir
        date_file = os.path.join(self.features_dir, "tmp", self.input_dates)
        all_available_dates = [os.path.basename(date).split("_")[self.date_position].split("-")[0] for date in self.get_available_dates()]

        if not os.path.exists(date_file):
            with open(date_file, "w") as input_date_file:
                input_date_file.write("\n".join(all_available_dates))

        return date_file, all_available_dates

    def get_time_series(self, ram=128):
        """
        TODO : be able of using a date interval
        Return
        ------
            list
                [(otb_Application, some otb's objects), time_series_labels]
                Functions dealing with otb's application instance has to 
                returns every objects in the pipeline
        """
        from Common.OtbAppBank import CreateConcatenateImagesApplication
        from Common.FileUtils import ensure_dir

        dates_concatenation = self.get_available_dates()
        
        time_series_dir = os.path.join(self.features_dir, "tmp")
        ensure_dir(time_series_dir, raise_exe=False)
        times_series_raster = os.path.join(time_series_dir, self.time_series_name)
        dates_time_series = CreateConcatenateImagesApplication({"il": dates_concatenation,
                                                                "out": times_series_raster,
                                                                "pixType": "int16",
                                                                "ram": str(ram)})
        dates_in_file, dates_in = self.write_dates_file()
        # build labels
        features_labels = ["{}_{}_{}".format(self.__class__.name, band_name, date) for date in dates_in for band_name in self.stack_band_position]

        # needed to travel throught iota2's library
        app_dep = []

        # if not all bands must be used
        if self.extracted_bands:
            app_dep.append(dates_time_series)
            (dates_time_series,
             features_labels) = self.extract_bands_time_series(dates_time_series,
                                                               dates_in,
                                                               len(self.stack_band_position),
                                                               self.extracted_bands,
                                                               ram)

        return (dates_time_series, app_dep), features_labels

    def extract_bands_time_series(self, dates_time_series,
                                  dates_in,
                                  comp,
                                  extract_bands,
                                  ram):
        """
        TODO : mv to base class ?
        extract_bands : list
                [('B2', 1), ('B3', 2), ('B4', 3), ('B6', 5), ('B7', 6), ('B8', 7), ('B8A', 8), ('B11', 9), ('B12', 10)]
        comp : number of bands in stack
        """
        from Common.OtbAppBank import CreateExtractROIApplication

        nb_dates = len(dates_in)
        channels_interest = []
        for date_number in range(nb_dates):
            for band_name, band_position in extract_bands:
                channels_interest.append(band_position + int(date_number * comp))

        features_labels = ["{}_{}_{}".format(self.__class__.name, band_name, date) for date in dates_in for band_name, band_pos in extract_bands]
        channels_list = ["Channel{}".format(channel) for channel in channels_interest]
        time_series_out = dates_time_series.GetParameterString("out")
        dates_time_series.Execute()
        extract = CreateExtractROIApplication({"in":dates_time_series,
                                               "cl":channels_list,
                                               "ram":str(ram),
                                               "out":dates_time_series.GetParameterString("out")})
        return extract, features_labels

    
    def get_time_series_gapFilling(self, ram=128):
        """
        TODO : prendre en compte le forcage des dates
        """
        dates_interp_file, dates_interp = self.write_interpolation_dates_file()
        pass

    def get_time_series_masks(self, ram=128):
        """
        needed to gapFilling application
        """
        pass
    def get_time_series_features(self, ram=128):
        """
        """
        pass

class Sentinel_1(Sensor):

    name = 'Sentinel1'

    def __init__(self):
        pass

class User_stack(Sensor):

    name = 'userStack'

    def __init__(self):
        pass

class Sentinel_2_S2C(Sensor):

    name = 'Sentinel2S2C'

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
            
            sensorConfig = (cfg_IOTA2.getParam("chain", "pyAppPath")).split(os.path.sep)
            sensorConfig = (os.path.sep).join(sensorConfig[0:-1] + ["config", "sensors.cfg"])
            cfg_sensors = SCF.serviceConfigFile(sensorConfig, iota_config=False)

            self.struct_path = cfg_sensors.getParam("Sentinel_2_S2C", "arbo")
            self.imType = cfg_sensors.getParam("Sentinel_2_S2C", "imtype")

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

