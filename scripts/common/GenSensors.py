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

"""
Class Sensor

Define each sensor for generic processing

"""
import glob
import logging
from osgeo import gdal,osr,ogr
import os
import New_DataProcessing as DP
import otbApplication as otb
import otbAppli
from Utils import run
import logging

logger = logging.getLogger(__name__)

pixelo = 'int16'

otbVersion = 5.0

class MonException(Exception):
    """
    Exception class
    """
    def __init__(self, raison):
        self.raison = raison

    def __str__(self):
        return self.raison


class Sensor(object):

    def __init__(self):
        self.bands = {}
        self.name = None
        self.DatesVoulues = None
        self.path = None
        self.fimages = None
        self.fdates = None
        self.fdatesRes = None
        self.borderMask =None
        self.borderMaskN = None
        self.borderMaskR = None
        self.sumMask = None
        self.native_res = None
        self.work_res = None
        self.serieTempMask = None
        self.serieTemp = None
        self.nodata_MASK = None
        self.pathRes = None
        self.nodata = None
        self.nuages = None
        self.saturation = None
        self.div = None
        self.struct_path = None
        self.imType = None
        self.pathmask = None
        self.proj = None
        self.indices = []
        self.posDate = None

    def setDatesVoulues(self,path):
        self.DatesVoulues = path

    def getDatesVoulues(self):
        return self.DatesVoulues

    def setInputDatesFile(self, opath=None):
        
        count = 0
        imageList = []

        fList = []

        for image in glob.glob(self.path+self.struct_path+self.imType):
            imagePath = image.split("/")
            imageName = imagePath[-1].split("_")
            imageList.append(imageName)

        #Organize the names by date
        imageList.sort(key=lambda x: x[self.posDate])

        dates = []
        for imSorted  in imageList:
            date = imSorted[self.posDate].split("-")[0]
            dates.append(date)

        outputDateFile = self.fdates
        if opath:
            outputDateFile = os.path.join(opath, os.path.split(self.fdates)[-1])
        if not os.path.exists(outputDateFile):
            with open(outputDateFile, "w") as filedate:
                filedate.write("\n".join(dates))
        return outputDateFile

    def getImages(self, opath):

        file = open(self.fimages, "w")
        #filedate = open(self.fdates, "w")
        
        count = 0
        imageList = []

        fList = []

        glob_path = (self.path+self.struct_path+self.imType).replace("[","[[]")
        for image in glob.glob(glob_path):
            imagePath = image.split("/")
            imageName = imagePath[-1].split("_")
            imageList.append(imageName)

        #Organize the names by date
        imageList.sort(key=lambda x: x[self.posDate])
        #Write all the images in chronological order in a text file
        for imSorted  in imageList:
            s = "_"
            nameIm = s.join(imSorted)
            name = self.struct_path+nameIm
            for im in glob.glob((self.path+"/"+name).replace("[","[[]")):
                file.write(im)
                file.write('\n')
                fList.append(im)
            count = count + 1
        file.close()

        return fList


    def sortMask(self,liste):
        imageList = []
        for image in liste:
            imagepath = image.split("/")
            nameIm = imagepath[-1].split("_")
            imageList.append(nameIm)

        imageList.sort(key=lambda x: x[self.posDate])
        liste_Sort = []
        for imSorted  in imageList:
            s = "_"
            nameIm = s.join(imSorted)
            liste_Sort.append(glob.glob((self.pathmask+nameIm).replace("[","[[]"))[0])
        return liste_Sort

    def getList_NoDataMask(self):
        liste_nodata = glob.glob((self.pathmask+"/*"+self.nodata).replace("[","[[]"))
        liste = self.sortMask(liste_nodata)
        return liste


    def getList_CloudMask(self):
        liste_cloud = glob.glob((self.pathmask+"/*"+self.nuages).replace("[","[[]"))
        liste = self.sortMask(liste_cloud)
        return liste


    def getList_SatMask(self):
        liste_sat = glob.glob((self.pathmask+"/*"+self.saturation).replace("[","[[]"))
        liste = self.sortMask(liste_sat)
        return liste


    def getList_DivMask(self, logger=logger):
        logger = logging.getLogger(__name__)
        logger.debug("Search path for masks: {}".format(self.pathmask+"/*"+self.div))
        liste_div = glob.glob((self.pathmask+"/*"+self.div).replace("[","[[]"))
        liste = self.sortMask(liste_div)
        return liste


    def CreateBorderMask_bindings(self, opath, imref, wMode=False):

        imlist = self.getImages(opath.opathT)

        if self.nodata_MASK:
            mlist = self.getList_NoDataMask()
        else:
            mlist = self.getList_DivMask()

        #Builds the individual binary masks
        listMaskch = ""
        listMask = []

        if self.nodata_MASK:
            expr = "(im1b1/2)==rint(im1b1/2)?0:1"
        else:
            expr = "(im1b1/2)==rint(im1b1/2)?1:0"

        indBinary = []
        if not self.name == 'Sentinel2':
            for i in range(len(mlist)):
                name = os.path.split(mlist[i])[-1]
                outputDirectory = opath.opathT
                bandMath = otbAppli.CreateBandMathApplication({"il" : mlist[i],
                                                               "exp" : expr,
                                                               "pixType" : 'uint8',
                                                               "out" : outputDirectory+"/"+name})
                if wMode : bandMath.ExecuteAndWriteOutput()
                else : bandMath.Execute()
                indBinary.append(bandMath)

        #Builds the complete binary mask
        if not self.name == 'Sentinel2':
            expr = "0"
            for i in range(len(mlist)):
                    expr += "+im"+str(i+1)+"b1"
        else:
            expr = "+".join([ "(1-im"+str(i+1)+"b1)" for i in range(len(mlist))])

        listMask_s = indBinary
        if self.name == 'Sentinel2':
            listMask_s = mlist
        maskSum = otbAppli.CreateBandMathApplication({"il": listMask_s,
                                                      "exp": expr,
                                                      "pixType": 'uint8',
                                                      "out": self.sumMask})

        if wMode : maskSum.ExecuteAndWriteOutput()
        else : maskSum.Execute()

        expr = "im1b1>=1?1:0"
        maskBin = otbAppli.CreateBandMathApplication({"il": maskSum,
                                                      "exp": expr,
                                                      "pixType": 'uint8',
                                                      "out": self.borderMaskN})
        if (self.work_res == self.native_res):
            self.borderMask = self.borderMaskN
        return maskBin,indBinary,maskSum


    def createMaskSeries_bindings(self, opath, maskC, wMode=False, logger=logger):
        """
        Builds one multitemporal binary mask of SPOT images

        ARGs
        INPUT:
             -ipath: absolute path of the resized masks
             -opath: path were the multitemporal mask will be created
             OUTPUT:
             -Multitemporal binary mask .tif
        """

        logger.info("using common mask : " + maskC)

        imlist = self.getImages(opath)
        clist = self.getList_CloudMask()
        slist = self.getList_SatMask()
        dlist = self.getList_DivMask()
        #im1 = maskCommun, im2 = cloud, im3 = sat, im4 = div (bord)
        expr = "im1b1 * ( im2b1>0?1:0 or im3b1>0?1:0 or ((((im4b1/2)==rint(im4b1/2))?0:1)))"
        if self.name == 'Sentinel2':
            expr = " im1b1 * ( im2b1>0?1:0 or im3b1>0?1:0 or im4b1>0?1:0)"
        datesMasks = []
        for im in range(0,len(imlist)):
            impath = imlist[im].split('/')
            imname = impath[-1].split('.')
            name = opath+'/'+imname[0]+'_MASK.TIF'
            #chain = [maskC,clist[im],slist[im],dlist[im]]
            chain = " ".join([maskC,clist[im],slist[im],dlist[im]])
            dateMask = otbAppli.CreateBandMathApplication({"il": [maskC,clist[im],slist[im],dlist[im]],
                                                           "exp": expr,
                                                           "pixType": 'uint8',
                                                           "out": name})
            datesMasks.append(dateMask)
            if wMode:
                dateMask.ExecuteAndWriteOutput()
            else:
                dateMask.Execute()
        masksSeries = otbAppli.CreateConcatenateImagesApplication({"il" : datesMasks,
                                                                   "pixType" : 'uint8',
                                                                   "out" : self.serieTempMask})
        return masksSeries,datesMasks

    def createSerie_bindings(self, opath, logger=logger):
        """
        Concatenation of all the images Landsat to create one multitemporal multibands image
        ARGs
        INPUT:
             -ipath: absolute path of the images
             -opath: path were the images will be concatenated
        OUTPUT:
             -Multitemporal, multiband serie
        """
        logger.info("temporal series generation : " + self.serieTemp)
        imlist = self.getImages(opath)
        sep = " "*47
        logger.debug("temporal series generation using dates (chrono sorted): \n"+ sep + ("\n"+sep).join(imlist))
        temporalSerie = otbAppli.CreateConcatenateImagesApplication({"il" : imlist,
                                                                     "pixType" : 'int16',
                                                                     "out" : self.serieTemp})
        return temporalSerie





