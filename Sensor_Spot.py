# -*- coding: utf-8 -*-
from Capteurs import Sensor
import glob
import os

from DataProcessing import GetBorderProp
from Capteurs import MonException


class Spot4(Sensor):

    def __init__(self,path_image,opath):
        Sensor.__init__(self)
        self.name = 'Spot4'
        self.path = path_image
        self.bands["BANDS"] = {'green' : 1 , 'red' : 2, 'NIR' : 3, 'SWIR' : 4}
        self.nbBands = len(self.bands['BANDS'].keys())
        self.fimages = opath.opathT+"/SPOTimagesList.txt"
        self.fdates = opath.opathT+"/SPOTimagesDateList.txt"
        self.native_res = 20
        self.imType =  'ORTHO_SURF_CORR_PENTE'
        self.sumMask = opath.opathT+"/SPOT4_Sum_Mask.tif"
        self.borderMaskN = opath.opathT+"/SPOT4_Border_MaskN.tif"
        self.borderMaskR = opath.opath+"/SPOT4_Border_MaskR.tif"
        
        self.struct_path = "/*/*/*/*"
        cfg = Config(fconf)
        conf = cfg.Spot4
        
        #print conf
        self.serieTemp = opath.opathT+conf.serieTempo
        self.serieTempMask = opath.opathT+conf.serieTempoMask
        self.serieTempGap = opath.opathT+conf.serieTempoGap
        
        #self.serieTempPrimGap = opath.opathT+conf.serieTempoPrimGap
        self.work_res = workRes
        
        if conf.nodata_Mask == 'False':
            self.nodata_MASK = False
        elif conf.nodata_Mask == "True":
            self.nodata_MASK = True
        else:
            print "Value Error for No Data Mask flag. NoDataMask not considered"
            self.nodata_MASK = False

        try:
            
            liste = self.getImages(opath)
            if len(liste) == 0:
                raise MonException("ERROR : No valid images in %s"%self.path)
            else:
                self.imRef = liste[0]
                self.liste_im = liste[:]
        except MonException, mess:
            print mess



    def getImages(self,opath):

       file = open(self.fimages, "w")
       filedate = open(self.fdates, "w")
       count = 0
       imageList = []
       fList = []
       

       #Find all matches and put them in a list
       for image in glob.glob(self.path+self.struct_path+self.imType+"*.TIF"):
          imagePath = image.split('/')
          imageName = imagePath[-1].split('.')
          imageNameParts = imageName[0].split('_')
          imageList.append(imageNameParts)

       #Organize the names by date according to SPOT4 naming
       imageList.sort(key=lambda x: x[3])

        #Write all the images in chronological order in a text file
       for imSorted  in imageList:
          filedate.write(imSorted[3])
          filedate.write('\n')
          name = '_'.join(imSorted)+'.TIF'
          for im in glob.glob(self.path+self.struct_path+name):
             file.write(im)
             file.write('\n')
             fList.append(im)
          count = count + 1
       filedate.close()
       file.close()

       return fList


    def getCloudMask(self,imagePath):
       """
       Get the name of the cloud mask using the name of the image
       ARGs:
            INPUT:
                -imagePath: the absolute path of one image
            OUTPUT:
                -The name of the corresponding cloud mask

        """
       folder = imagePath.split('/')
       ifolder = '/'.join(folder[0:-1])+'/MASK'
       os.chdir(ifolder)
       fmask = glob.glob("*_NUA.TIF")
       mask = os.getcwd()+'/'+fmask[0]

       return mask

    def getSatMask(self,imagePath):
       """
       Get the name of the saturation mask using the name of the image
       ARGs:
           INPUT:
                -imagePath: the absolute path of one image
           OUTPUT:
                -The name of the corresponding saturation mask

       """
       folder = imagePath.split('/')
       ifolder = '/'.join(folder[0:-1])+'/MASK'
       os.chdir(ifolder)
       fmask = glob.glob("*_SAT.TIF")
       mask = os.getcwd()+'/'+fmask[0]

       return mask

    def getDivMask(self,imagePath):
       """
       Get the name of the 'divers' mask using the name of the image
       ARGs:
           INPUT:
                -imagePath: the absolute path of one image
           OUTPUT:
                -The name of the corresponding divers mask

       """
       folder = imagePath.split('/')
       ifolder = '/'.join(folder[0:-1])+'/MASK'
       os.chdir(ifolder)
       fmask = glob.glob("*_DIV.TIF")
       mask = os.getcwd()+'/'+fmask[0]

       return mask

    def getNoDataMask(self,imagePath):
       """
       Get the name of the 'divers' mask using the name of the image
       ARGs:
           INPUT:
                -imagePath: the absolute path of one image
           OUTPUT:
                -The name of the corresponding divers mask

       """
       folder = imagePath.split('/')
       ifolder = '/'.join(folder[0:-1])+'/MASK'
       os.chdir(ifolder)
       fmask = glob.glob("*_NODATA.TIF")
       mask = os.getcwd()+'/'+fmask[0]

       return mask
    #----------------------------------------------------------------------
    def getList_CloudMask(self):
       """
       Get the list of the cloud masks for each image on the images list
       ARGs:
           INPUT:
                -listimagePath: the list with the absolute path of the images
           OUTPUT:
                -The list with the name of the corresponding masks
       """
       listMask = []
       for image in self.liste_im:
          listMask.append(self.getCloudMask(image))

       return listMask

    def getList_SatMask(self):
       """
       Get the list of the saturation masks for each image on the images list
       ARGs:
           INPUT:
                -listimagePath: the list with the absolute path of the images
           OUTPUT:
                -The list with the name of the corresponding masks
       """
       listMask = []
       for image in self.liste_im:
          listMask.append(self.getSatMask(image))

       return listMask

    def getList_DivMask(self):
       """
       Get the list of the 'divers' masks for each image on the images list
       ARGs:
           INPUT:
                -listimagePath: the list with the absolute path of the images
           OUTPUT:
                -The list with the name of the corresponding masks
       """
       listMask = []
       for image in self.liste_im:
          listMask.append(self.getDivMask(image))

       return listMask

    def getList_NoDataMask(self):
       """
       Get the list of the 'divers' masks for each image on the images list
       ARGs:
           INPUT:
                -listimagePath: the list with the absolute path of the images
           OUTPUT:
               -The list with the name of the corresponding masks
       """
       listMask = []
       for image in liste_im:
           listMask.append(self.getNoDataMask(image))
       return listMask


    def getList_ResCloudMask(self):
        pass

    def getList_ResSatMask(self):
        pass

    def getList_ResDivMask(self):
        pass
       
 
