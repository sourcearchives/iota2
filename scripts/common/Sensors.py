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

    
class Formosat(Sensor):

    def __init__(self,path_image,opath,fconf,workRes):
        Sensor.__init__(self)
        # Invariant parameters
        self.name = 'SudouestKalideos'
	self.DatesVoulues = None
        self.path = path_image
        self.bands["BANDS"] = { "blue" : 1 , "green" : 2 , "red" : 3 , "NIR" : 4}
        self.nbBands = len(self.bands['BANDS'].keys())
        self.posDate = 1 
        self.fimages = opath.opathT+"/FormosatimagesList.txt"
        self.fdates = opath.opathT+"/FormosatimagesDateList.txt"
        self.work_res = workRes
        self.fImResize = opath.opathT+"/FormosatImageResList.txt"
        self.fdatesRes = opath.opathT+"/FormosatImageDateResList.txt"
        #MASK Chain
        self.sumMask = opath.opathT+"/Formosat_Sum_Mask.tif"
        self.borderMaskN = opath.opathT+"/Formosat_Border_MaskN.tif"
        self.borderMaskR = opath.opathT+"/Formosat_Border_MaskR.tif"
        
        #Time series
        self.serieTemp = opath.opathT+"/Formosat_ST_REFL.tif"
        self.serieTempMask = opath.opathT+"/Formosat_ST_MASK.tif"
        self.serieTempGap = opath.opathT+"/Formosat_ST_REFL_GAP.tif"   
        #Indices
        self.indices = "NDVI","Brightness"
        # Users parameters
        cfg = Config(fconf)
        conf = cfg.Formosat
        conf2 = cfg.GlobChain
        #Get DATA INFO
        self.struct_path = conf.arbo
        self.native_res = int(conf.nativeRes)
        self.imType = conf.imtype
        self.pathRes = opath.opathT+"/FormRes_%sm/"%workRes
        self.proj = conf2.proj
        #Get MASK INFO
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
            
            liste = self.getImages(opath)
            if len(liste) == 0:
                raise MonException("ERROR : No valid images in %s"%self.path)
            else:
                self.imRef = liste[0]
        except MonException, mess:
            print mess

    def getDateFromName(self,nameIm):
        
        imagePath = nameIm.split("/")
        #print nameIm
        nameimage = imagePath[-1].split("_")
        #print nameimage
        date = nameimage[1]
        
        return date

    def getTypeMask(self,name):
        chaine = name.split('.')
        if chaine[1] == "nuages":
            return "NUA"
        elif chaine[1] == 'saturation':
            return "SAT"
        elif chaine[1] == 'bord_eau':
            return 'DIV'
        else:
            return -1

class Landsat5(Sensor):

    def __init__(self,path_image,opath,fconf,workRes):
        Sensor.__init__(self)
        #Invariant Parameters
        self.name = 'Landsat5'
	self.DatesVoulues = None
        self.path = path_image
	self.bands["BANDS"] = { "blue":1 ,"green":2 ,"red":3 ,"NIR":4 ,"SWIR":5}
        self.nbBands = len(self.bands['BANDS'].keys())
        self.posDate = 3
        self.fimages = opath.opathT+"/LANDSAT5imagesList.txt"
        self.fdates = opath.opathT+"/LANDSAT5imagesDateList.txt"
        self.fImResize = opath.opathT+"/Landsat5ImageResList.txt"
        self.fdatesRes = opath.opathT+"/Landsat5ImageDateResList.txt"
        self.work_res = workRes
        
        #MASK
        self.sumMask = opath.opathT+"/Landsat5_Sum_Mask.tif"
        self.borderMaskN = opath.opathT+"/Landsat5_Border_MaskN.tif"
        self.borderMaskR = opath.opathT+"/Landsat5_Border_MaskR.tif"
        
        #Time series
        self.serieTemp = opath.opathT+"/Landsat5_ST_REFL.tif"
	#self.serieTemp = opath.opathT+"/Landsat5_ST_REFL.tif"
        self.serieTempMask = opath.opathT+"/Landsat5_ST_MASK.tif"
        self.serieTempGap = opath.opathT+"/Landsat5_ST_REFL_GAP.tif"   
        #Indices
        self.indices = "NDVI","NDWI","Brightness"     
        # Users parameters
        cfg = Config(fconf)
        conf = cfg.Landsat5
        conf2 = cfg.GlobChain
        #DATA INFO
        self.struct_path = conf.arbo
        self.native_res = int(conf.nativeRes)
        self.imType = conf.imtype
        self.pathRes = opath.opathT+"/LandRes_%sm/"%workRes
        self.proj = conf2.proj

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
            
            liste = self.getImages(opath)
	    print liste
            if len(liste) == 0:
                raise MonException("ERROR : No valid images in %s"%self.path)
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

    def __init__(self,path_image,opath,fconf,workRes):
        Sensor.__init__(self)
        #Invariant Parameters
        self.name = 'Landsat8'
	self.DatesVoulues = None
        self.path = path_image
        self.bands["BANDS"] = { "aero":1 ,"blue":2 ,"green":3 ,"red":4 ,"NIR":5 ,"SWIR":6 ,"SWIR2":7}
        self.nbBands = len(self.bands['BANDS'].keys())
        self.posDate = 3
        self.fimages = opath.opathT+"/LANDSAT8imagesList.txt"
        self.fdates = opath.opathT+"/LANDSAT8imagesDateList.txt"
        self.fImResize = opath.opathT+"/Landsat8ImageResList.txt"
        self.fdatesRes = opath.opathT+"/Landsat8ImageDateResList.txt"
        self.work_res = workRes
        
        #MASK
        self.sumMask = opath.opathT+"/Landsat8_Sum_Mask.tif"
        self.borderMaskN = opath.opathT+"/Landsat8_Border_MaskN.tif"
        self.borderMaskR = opath.opathT+"/Landsat8_Border_MaskR.tif"
        
        #Time series
        self.serieTemp = opath.opathT+"/Landsat8_ST_REFL.tif"
	#self.serieTemp = opath.opathT+"/Landsat8_ST_REFL.tif"
        self.serieTempMask = opath.opathT+"/Landsat8_ST_MASK.tif"
        self.serieTempGap = opath.opathT+"/Landsat8_ST_REFL_GAP.tif"   
        #Indices
        self.indices = "NDVI","NDWI","Brightness"     
        # Users parameters
        cfg = Config(fconf)
        conf = cfg.Landsat8
        conf2 = cfg.GlobChain
        #DATA INFO
        self.struct_path = conf.arbo
        self.native_res = int(conf.nativeRes)
        self.imType = conf.imtype
        self.pathRes = opath.opathT+"/LandRes_%sm/"%workRes
        self.proj = conf2.proj

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
            
            liste = self.getImages(opath)
	    print liste
            if len(liste) == 0:
                raise MonException("ERROR : No valid images in %s"%self.path)
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

class Sentinel_1(Sensor):

    def __init__(self,path_image,opath,fconf,workRes):
        Sensor.__init__(self)
        #Invariant Parameters
        self.name = 'Landsat8'
	self.DatesVoulues = None
        self.path = path_image
        self.bands["BANDS"] = { "aero":1 ,"blue":2 ,"green":3 ,"red":4 ,"NIR":5 ,"SWIR":6 ,"SWIR2":7}
        self.nbBands = len(self.bands['BANDS'].keys())
        self.fimages = opath.opathT+"/LANDSATimagesList.txt"
        self.fdates = opath.opathT+"/LANDSATimagesDateList.txt"
        self.fImResize = opath.opathT+"/Landsat8ImageResList.txt"
        self.fdatesRes = opath.opathT+"/Landsat8ImageDateResList.txt"
        self.work_res = workRes
        
        #MASK
        self.sumMask = opath.opathT+"/Landsat8_Sum_Mask.tif"
        self.borderMaskN = opath.opathT+"/Landsat8_Border_MaskN.tif"
        self.borderMaskR = opath.opathT+"/Landsat8_Border_MaskR.tif"
        
        #Time series
        self.serieTemp = opath.opathT+"/Landsat8_ST_REFL.tif"
        self.serieTempMask = opath.opathT+"/Landsat8_ST_MASK.tif"
        self.serieTempGap = opath.opathT+"/Landsat8_ST_REFL_GAP.tif"   
        #Indices
        self.indices = "Haralick","",""     
        # Users parameters
        cfg = Config(fconf)
        conf = cfg.Landsat8
        conf2 = cfg.GlobChain
        #DATA INFO
        self.struct_path = conf.arbo
        self.native_res = int(conf.nativeRes)
        self.imType = conf.imtype
        self.pathRes = opath.opathT+"/LandRes_%sm/"%workRes
        self.proj = conf2.proj

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
            
            liste = self.getImages(opath)
	    print liste
            if len(liste) == 0:
                raise MonException("ERROR : No valid images in %s"%self.path)
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

    def __init__(self,path_image,opath,fconf,workRes):
        Sensor.__init__(self)
        #Invariant Parameters
        self.name = 'Sentinel2'
	self.DatesVoulues = None
        self.path = path_image
	self.bands["BANDS"] = { "blue":1 ,"green":2 ,"red":3 ,"RE1":4 ,"RE2":5 ,"RE3":6 ,"NIR":7,"NIR0":8,"SWIR":9,"SWIR2":10}#NIR0 = tight NIR
        self.nbBands = len(self.bands['BANDS'].keys())
        self.fimages = opath.opathT+"/Sentinel2imagesList.txt"
        self.fdates = opath.opathT+"/Sentinel2imagesDateList.txt"
        self.fImResize = opath.opathT+"/Sentinel2ImageResList.txt"
        self.fdatesRes = opath.opathT+"/Sentinel2ImageDateResList.txt"
	self.posDate = 1
        self.work_res = workRes
        
        #MASK
        self.sumMask = opath.opathT+"/Sentinel2_Sum_Mask.tif"
        self.borderMaskN = opath.opathT+"/Sentinel2_Border_MaskN.tif"
        self.borderMaskR = opath.opathT+"/Sentinel2_Border_MaskR.tif"
        
        #Time series
        #self.serieTemp = opath.opathT+"/Sentinel2_ST_REFL.tif"
	self.serieTemp = opath.opathT+"/Sentinel2_ST_REFL.tif"

        self.serieTempMask = opath.opathT+"/Sentinel2_ST_MASK.tif"
        self.serieTempGap = opath.opathT+"/Sentinel2_ST_REFL_GAP.tif"   
        #Indices
        self.indices = "NDVI","NDWI","Brightness"
        # Users parameters
        cfg = Config(fconf)
        conf = cfg.Sentinel_2
        conf2 = cfg.GlobChain
        #DATA INFO
        self.struct_path = conf.arbo
        self.native_res = int(conf.nativeRes)
        self.imType = conf.imtype
        self.pathRes = opath.opathT+"/LandRes_%sm/"%workRes
        self.proj = conf2.proj

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
            
            liste = self.getImages(opath)
	    print liste
            if len(liste) == 0:
                raise MonException("ERROR : No valid images in %s"%self.path)
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

    def __init__(self,path_image,opath,fconf,workRes):
        Sensor.__init__(self)
        #Invariant Parameters
        self.name = 'Spot4'
	self.DatesVoulues = None
        self.path = path_image
        self.bands["BANDS"] = {'green' : 1 , 'red' : 2, 'NIR' : 3, 'SWIR' : 4}
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
            
            liste = self.getImages(opath)
            if len(liste) == 0:
                raise MonException("ERROR : No valid images in %s"%self.path)
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
