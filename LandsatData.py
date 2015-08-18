#!/usr/bin/python

import os
import glob
from sys import argv
import Dico as dico

"""This is the module to get LANDSAT data \n
including images and masks and according \n
to the LANDSAT folders organization"""
res = str(dico.res)


def getLandsatImages(ipath, opath, tile):
   """
   Returns the list of the LANDSAT Images in choronological order
       INPUT:
            -ipath: LANDSAT images path
            -opath: output path
           
       OUTPUT:
            - A texte file named LandsatImagesList.txt, containing the names and path of the LANDSAT images 
            - A texte file named LandsatImagesDateList.txt, containing the list of the dates in chronological order
    
   """

   file = open(opath+"/LANDSATimagesList_"+tile+".txt", "w")
   filedate = open(opath+"/LANDSATimagesDateList_"+tile+".txt", "w")
   count = 0
   imageList = []
   fList = []
   dateList = []
  
   #Find all matches and put them in a list 
   for image in glob.glob(ipath+"/*"+tile+"*/*ORTHO_SURF_CORR_PENTE*.TIF"):
      imagePath = image.split('/')
      imageName = imagePath[-1].split('.')
      imageNameParts = imageName[0].split('_')
      if int(imageNameParts[3]) <= 20151231:
         file.write(image)
         file.write('\n')
         imageList.append(imageNameParts)
         fList.append(image) 

  #Re-organize the names by date according to LANDSAT naming
   imageList.sort(key=lambda x: x[3])
   #Write all the images in chronological order in a text file
   for imSorted  in imageList:
      filedate.write(imSorted[3])
      filedate.write('\n')
      count = count + 1
    
   filedate.close() 
   file.close()    
   return fList

   return fList
#-------------------------------------------------------------------------------
def getResizedLandsatImages(ipath, opath):
   """
   Returns the list of the resized LANDSAT Images in choronological order
       INPUT:
            -ipath: LANDSAT images path
            -opath: output path
           
       OUTPUT:
            - A texte file named LandsatImagesList.txt, containing the names and path of the LANDSAT images 
            - A texte file named LandsatImagesDateList.txt, containing the list of the dates in chronological order
    
   """

   file = open(opath+"/LANDSATimagesListResize.txt", "w")
   filedate = open(opath+"/LANDSATresizedImagesDateList.txt", "w")
   count = 0
   imageList = []
   fList = []
   dateList = []
  
   #print opath
   #Find all matches and put them in a list 
   for image in glob.glob(opath+"/"+"*_"+res+"m.TIF"):
      imagePath = image.split('/')
      imageName = imagePath[-1].split('.')
      imageNameParts = imageName[0].split('_')
      imageList.append(imageNameParts)

   #Re-organize the names by date according to LANDSAT naming
   imageList.sort(key=lambda x: x[1])

   #Write all the images in chronological order in a text file
   for imSorted  in imageList:
      filedate.write(imSorted[1])
      filedate.write('\n')
      name = '_'.join(imSorted)+'.TIF'
      for im in glob.glob(opath+"/"+name):
         file.write(im)
         file.write('\n')
         fList.append(im) 
      count = count + 1
   filedate.close() 
   file.close()     

   return fList


#--------------------------------------------------------------------------------
def getLandsatCloudMask(imagePath):
   """
   Get the name of the cloud mask using the name of the image
   ARGs:
       INPUT:
            -imagePath: the absolute path of one image
       OUTPUT:
            -The name of the corresponding cloud mask

   """
   folder = imagePath.split('/')
   imageName = folder[-1].split('.')
   imageNameP = imageName[0].split('_')
   maskName = '_'.join(imageNameP[0:-5])+'_'+imageNameP[-1]+'_NUA.TIF'
   mask = '/'.join(folder[0:-1])+'/MASK/'+maskName
           
   return mask


def getLandsatSatMask(imagePath):
   """
   Get the name of the cloud mask using the name of the image
   ARGs:
       INPUT:
            -imagePath: the absolute path of one image
       OUTPUT:
            -The name of the corresponding cloud mask

   """
   folder = imagePath.split('/')
   imageName = folder[-1].split('.')
   imageNameP = imageName[0].split('_')
   maskName = '_'.join(imageNameP[0:-5])+'_'+imageNameP[-1]+'_SAT.TIF'
   mask = '/'.join(folder[0:-1])+'/MASK/'+maskName
           
   return mask

def getLandsatDivMask(imagePath):
   """
   Get the name of the cloud mask using the name of the image
   ARGs:
       INPUT:
            -imagePath: the absolute path of one image
       OUTPUT:
            -The name of the corresponding cloud mask

   """
   folder = imagePath.split('/')
   imageName = folder[-1].split('.')
   imageNameP = imageName[0].split('_')
   maskName = '_'.join(imageNameP[0:-5])+'_'+imageNameP[-1]+'_DIV.TIF'
   mask = '/'.join(folder[0:-1])+'/MASK/'+maskName
           
   return mask

def getLandsatNoDataMask(imagePath):
   """
   Get the name of the cloud mask using the name of the image
   ARGs:
       INPUT:
            -imagePath: the absolute path of one image
       OUTPUT:
            -The name of the corresponding cloud mask

   """
   folder = imagePath.split('/')
   imageName = folder[-1].split('.')
   imageNameP = imageName[0].split('_')
   maskName = '_'.join(imageNameP[0:-5])+'_'+imageNameP[-1]+'_NODATA.TIF'
   mask = '/'.join(folder[0:-1])+'/MASK/'+maskName
           
   return mask

def getLandsatBinDivMask(imagePath):
   """
   Get the name of the cloud mask using the name of the image
   ARGs:
       INPUT:
            -imagePath: the absolute path of one image
       OUTPUT:
            -The name of the corresponding cloud mask

   """
   folder = imagePath.split('/')
   imageName = folder[-1].split('.')
   imageNameP = imageName[0].split('_')
   maskName = '_'.join(imageNameP[0:-5])+'_'+imageNameP[-1]+'_DIV.TIF'
   mask = '/'.join(folder[0:-1])+'/MASK/'+maskName
           
   return mask


#-------------------------------------------------------------------------------
def getList_LandsatCloudMask(listimagePath):
   """
   Get the list of the cloud masks for each image on the images list
   ARGs:
       INPUT:
            -listimagePath: the list with the absolute path of the images
       OUTPUT:
            -The list with the name of the corresponding masks
   """
   listMask = []
   for image in listimagePath:
      listMask.append(getLandsatCloudMask(image))
   
   return listMask

def getList_LandsatSatMask(listimagePath):
   """
   Get the list of the cloud masks for each image on the images list
   ARGs:
       INPUT:
            -listimagePath: the list with the absolute path of the images
       OUTPUT:
            -The list with the name of the corresponding masks
   """
   listMask = []
   for image in listimagePath:
      listMask.append(getLandsatSatMask(image))
  
   return listMask

def getList_LandsatDivMask(listimagePath):
   """
   Get the list of the cloud masks for each image on the images list
   ARGs:
       INPUT:
            -listimagePath: the list with the absolute path of the images
       OUTPUT:
            -The list with the name of the corresponding masks
   """
   listMask = []
   for image in listimagePath:
      listMask.append(getLandsatDivMask(image))
  
   return listMask

def getList_LandsatNoDataMask(listimagePath):
   """
   Get the list of the cloud masks for each image on the images list
   ARGs:
       INPUT:
            -listimagePath: the list with the absolute path of the images
       OUTPUT:
            -The list with the name of the corresponding masks
   """
   listMask = []
   for image in listimagePath:
      listMask.append(getLandsatNoDataMask(image))
  
   return listMask

def getList_LandsatBinDivMask(listimagePath):
   """
   Get the list of the cloud masks for each image on the images list
   ARGs:
       INPUT:
            -listimagePath: the list with the absolute path of the images
       OUTPUT:
            -The list with the name of the corresponding masks
   """
   listMask = []
   for image in listimagePath:
      listMask.append(getLandsatBinDivMask(image))
  
   return listMask


#----------------------------------------------------------------

def getLandsatResCloudMask(imagePath):
   """
   Get the name of the resized cloud mask using the name of the image
   ARGs:
       INPUT:
            -imagePath: the absolute path of one image
       OUTPUT:
            -The name of the corresponding cloud mask
   """

   #folder = opath+"/Resize_LMasks"
   folderim = imagePath.split('/')
   imageName = folderim[-1].split('.')
   print imageName
   nameparts = imageName[0].split('_')
   print nameparts
   nameim = '_'.join(nameparts[0:5])
   mname = nameim+"_"+nameparts[-2]+"_NUA"+res+"m."+imageName[-1]
   folder = '/'.join(folderim[0:-1])
   mask = folder+'/'+mname
   
   return mask


def getLandsatResSatMask(imagePath):
   """
   Get the name of the resized saturation mask using the name of the image
   ARGs:
       INPUT:
            -imagePath: the absolute path of one image
       OUTPUT:
            -The name of the corresponding cloud mask
   """

   #folder = opath+"/Resize_LMasks"
   folderim = imagePath.split('/')
   imageName = folderim[-1].split('.')
   nameparts = imageName[0].split('_')
   nameim = '_'.join(nameparts[0:5])
   mname = nameim+"_"+nameparts[-2]+"_SAT"+res+"m."+imageName[-1]
   folder = '/'.join(folderim[0:-1])
   mask = folder+'/'+mname
   
   return mask

def getLandsatResDivMask(imagePath):
   """
   Get the name of the resized divers mask using the name of the image
   ARGs:
       INPUT:
            -imagePath: the absolute path of one image
       OUTPUT:
            -The name of the corresponding cloud mask
   """

   folderim = imagePath.split('/')
   imageName = folderim[-1].split('.')
   nameparts = imageName[0].split('_')
   nameim = '_'.join(nameparts[0:5])
   mname = nameim+"_"+nameparts[-2]+"_DIV"+res+"m."+imageName[-1]
   folder = '/'.join(folderim[0:-1])
   mask = folder+'/'+mname
   
   return mask


#-------------------------------------------------------------
def getList_LandsatResCloudMask(listimagePath):
   """
   Get the list of the resized cloud masks for each image on the images list
   ARGs:
       INPUT:
            -listimagePath: the list with the absolute path of the images
       OUTPUT:
            -The list with the name of the corresponding masks
   """
   listMask = []
   for image in listimagePath:
      listMask.append(getLandsatResCloudMask(image))
   
   return listMask

def getList_LandsatResSatMask(listimagePath):
   """
   Get the list of the resized saturation masks for each image on the images list
   ARGs:
       INPUT:
            -listimagePath: the list with the absolute path of the images
       OUTPUT:
            -The list with the name of the corresponding masks
   """
   listMask = []
   for image in listimagePath:
      listMask.append(getLandsatResSatMask(image))
   
   return listMask

def getList_LandsatResDivMask(listimagePath):
   """
   Get the list of the resized divers masks for each image on the images list
   ARGs:
       INPUT:
            -listimagePath: the list with the absolute path of the images
       OUTPUT:
            -The list with the name of the corresponding masks
   """
   listMask = []
   for image in listimagePath:
      listMask.append(getLandsatResDivMask(image))
   
   return listMask

#---------------------------------------------------------------
def getLandsatImageRef(ipath, opath):

   imlist = getLandsatImages(ipath, opath, "*30m.tif")
   imref = imlist[0]
   
   return imref

#a = getLandsatImages(argv[1], argv[2])
#a = getResizedLandsatImages(argv[2], argv[3])
#a = getList_LandsatCloudMask(getLandsatImages(argv[1], argv[2]))
#a = getList_LandsatSatMask(getLandsatImages(argv[1], argv[2]))
#a = getList_LandsatDivMask(getLandsatImages(argv[1], argv[2]))
#a = getList_LandsatResCloudMask(getLandsatImages(argv[1], argv[2])
#a = getList_LandsatResSatMask(getLandsatImages(argv[1], argv[2]))
#a = getList_LandsatResDivMask(getLandsatImages(argv[1], argv[2]))
#print a
