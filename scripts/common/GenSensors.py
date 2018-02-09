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
        self.fImResize = None
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

    def getImages(self,opath):

        file = open(self.fimages, "w")
        filedate = open(self.fdates, "w")
        count = 0
        imageList = []

        fList = []

        for image in glob.glob(self.path+self.struct_path+self.imType):
            imagePath = image.split("/")
            imageName = imagePath[-1].split("_")
            imageList.append(imageName)

        #Organize the names by date
        imageList.sort(key=lambda x: x[self.posDate])
        #Write all the images in chronological order in a text file
        for imSorted  in imageList:
            date = imSorted[self.posDate].split("-")[0]
            filedate.write(date)
            #filedate.write(self.getDateFromName(imSorted))
            filedate.write('\n')
            s = "_"
            nameIm = s.join(imSorted)
            name = self.struct_path+nameIm#imSorted
            for im in glob.glob(self.path+"/"+name):
                file.write(im)
                file.write('\n')
                fList.append(im)
            count = count + 1
        filedate.close()
        file.close()

        return fList

    def getResizedImages(self,opath):
        #file = open(self.fImagesRes, "w")
        filedate = open(self.fdatesRes, "w")
        count = 0
        imageList = []
        fList = []

        for image in glob.glob(self.pathRes+"/*"+self.imType):
            imagePath = image.split("/")
            imageName = imagePath[-1].split("_")
            imageList.append(imageName)

        #Organize the names by date
        imageList.sort(key=lambda x: x[self.posDate])
        #Write all the images in chronological order in a text file
        for imSorted  in imageList:
            filedate.write(imSorted[self.posDate])
            filedate.write('\n')
            s = "_"
            nameIm = s.join(imSorted)
            #name = imSorted
            for im in glob.glob(self.pathRes+"/"+nameIm):
                #file.write(im)
                #file.write('\n')
                fList.append(im)
            count = count + 1
        filedate.close()
        #file.close()

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
            liste_Sort.append(glob.glob(self.pathmask+nameIm)[0])

        return liste_Sort

    def getList_NoDataMask(self):
        liste_nodata = glob.glob(self.pathmask+"/*"+self.nodata)
        liste = self.sortMask(liste_nodata)
        return liste


    def getList_CloudMask(self):
        liste_cloud = glob.glob(self.pathmask+"/*"+self.nuages)
        liste = self.sortMask(liste_cloud)
        return liste


    def getList_SatMask(self):
        liste_sat = glob.glob(self.pathmask+"/*"+self.saturation)
        liste = self.sortMask(liste_sat)
        return liste

    def getList_DivMask(self, logger=logger):
        logger = logging.getLogger(__name__)
        logger.debug("Search path for masks: {}".format(self.pathmask+"/*"+self.div))
        liste_div = glob.glob(self.pathmask+"/*"+self.div)
        liste = self.sortMask(liste_div)
        return liste

    def getList_ResCloudMask(self):
        liste_cloud = glob.glob(self.pathRes+"/*"+self.nuages)
        liste = self.sortMask(liste_cloud)
        return liste

    def getList_ResSatMask(self):
        liste_sat = glob.glob(self.pathRes+"/*"+self.saturation)
        liste = self.sortMask(liste_sat)
        return liste

    def getList_ResDivMask(self):
        liste_div = glob.glob(self.pathRes+"/*"+self.div)
        liste = self.sortMask(liste_div)
        return liste

    def GetBorderProp(self, mask, logger=logger):
        """
        Calculates the proportion of valid pixels in a mask. Is used to calculate
        the number of images to be used to build the mask

        ARGs
        INPUT:
        -mask: the binary mask
        OUTPUT:
        -Returns the proportion of valid pixels
        """

        hDataset = gdal.Open(mask, gdal.GA_ReadOnly )
        x = hDataset.RasterXSize
        y = hDataset.RasterYSize
        hBand = hDataset.GetRasterBand(1)
        stats = hBand.GetStatistics(True, True)
        mean = stats[2]
        nbPixel=x*y
        nbPixelCorrect=nbPixel*mean
        p=nbPixelCorrect*100/nbPixel

        return p

    def CreateBorderMask_bindings(self,opath,imref,nbLook,wMode=False):

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
            #expr = "+".join([ "im"+str(i+1)+"b1" for i in range(len(mlist))])
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


    def ResizeImages(self, opath, imref):
        """
        Resizes images using one ref image
        ARGs
        INPUT:
             -ipath: absolute path of the LANDSAT images
             -opath: path were the mask will be created
             -imref: SPOT Image to use for resizing
        OUTPUT:
             - A text file containing the list of LANDSAT images resized
        """
        imlist = self.getImages(opath)

        fileim = open(self.fImResize, "w")
        imlistout = []

        ds = gdal.Open(imref, gdal.GA_ReadOnly)
        nb_col=ds.RasterXSize
        nb_lig=ds.RasterYSize
        proj=ds.GetProjection()
        gt=ds.GetGeoTransform()
        ulx = gt[0]
        uly = gt[3]
        lrx = gt[0] + nb_col*gt[1] + nb_lig*gt[2]
        lry = gt[3] + nb_col*gt[4] + nb_lig*gt[5]

        srs=osr.SpatialReference(proj)
        chain_proj = self.proj

        resolX = abs(gt[1]) # resolution en metres de l'image d'arrivee
        resolY = abs(gt[5]) # resolution en metres de l'image d'arrivee
        chain_extend = str(ulx)+' '+str(lry)+' '+str(lrx)+' '+str(uly)

        for image in imlist:
            line = image.split('/')
            name = line[-1]

            imout = self.pathRes+"/"+name

            Resize = 'gdalwarp -of GTiff -r %s -tr %d %d -te %s -t_srs %s %s %s \n'% ('cubic', resolX,resolY,chain_extend,chain_proj, image, imout)
            run(Resize)

            fileim.write(imout)
            imlistout.append(imout)
            fileim.write("\n")


        fileim.close()

    def ResizeMasks(self, opath, imref):
        """
        Resizes LANDSAT masks using one spot image
        ARGs
        INPUT:
             -ipath: absolute path of the LANDSAT images
             -opath: path were the mask will be created
             -imref: SPOT Image to use for resizing
        OUTPUT:
             - A text file containing the list of LANDSAT images resized
        """
        imlist = self.getImages(opath)
        cmask = self.getList_CloudMask()

        print cmask
        smask = self.getList_SatMask()
        dmask = self.getList_DivMask()

        allmlists = [cmask, smask, dmask]
        if otbVersion == 5.0:
            expMask =  {"NUA":"im1b1 and 00000001?1:im1b1 and 00001000?1:0", "SAT":"im1b1!=0", "DIV":"im1b1 and 00000001?1:0"}
        else:
            expMask = {"NUA":"if(im1b1 and 00000001,1,if(im1b1 and 00001000,1,0))", "SAT":"im1b1!=0", "DIV":"if(im1b1 and 00000001,1,0)"}
        ds = gdal.Open(imref, gdal.GA_ReadOnly)
        nb_col=ds.RasterXSize
        nb_lig=ds.RasterYSize
        proj=ds.GetProjection()
        gt=ds.GetGeoTransform()
        ulx = gt[0]
        uly = gt[3]
        lrx = gt[0] + nb_col*gt[1] + nb_lig*gt[2]
        lry = gt[3] + nb_col*gt[4] + nb_lig*gt[5]

        srs=osr.SpatialReference(proj)

        chain_proj = self.proj


        resolX = abs(gt[1]) # resolution en metres de l'image d'arrivee
        resolY = abs(gt[5]) # resolution en metres de l'image d'arrivee
        chain_extend = str(ulx)+' '+str(lry)+' '+str(lrx)+' '+str(uly)

        for mlist in allmlists:
            for mask in mlist:
                line = mask.split('/')
                name = line[-1].split('.')
                nameOut = line[-1]
                typeMask = self.getTypeMask(line[-1])#name[0].split('_')[-1]
                namep = name[-2]+"bordbin"
                #namer = name[-2]+self.work_res+"m"
                newnameb = namep+'.'+name[-1]
                #newnamer = namer+'.'+name[-1]
                imout = opath+"/"+newnameb
                imoutr = self.pathRes+"/"+nameOut
                #print mask , typeMask
                if typeMask == 'NUA' :
                    exp = expMask['NUA']
                elif typeMask == 'SAT':
                    exp = expMask['SAT']
                elif typeMask == 'DIV':
                    exp = expMask['DIV']
                binary = "otbcli_BandMath -il "+mask+" -exp \""+exp+"\" -out "+imout
                run(binary)
                Resize = 'gdalwarp -of GTiff -r %s -tr %d %d -te %s -t_srs %s %s %s \n'% ('near', resolX,resolY,chain_extend,chain_proj, imout, imoutr)
                run(Resize)

    def createMaskSeries_bindings(self, opath, wMode=False, logger=logger):
        """
        Builds one multitemporal binary mask of SPOT images

        ARGs
        INPUT:
             -ipath: absolute path of the resized masks
             -opath: path were the multitemporal mask will be created
             OUTPUT:
             -Multitemporal binary mask .tif
        """
        
        maskC = opath+"/MaskCommunSL.tif" # image ecrite par createcommonzone
        maskCshp = opath+"/MaskCommunSL.shp"

        logger.info("Common mask generation : " + maskC)

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





