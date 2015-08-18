#!/usr/bin/python

import os
import glob
from sys import argv


"""This is the module to get SPOT data \n
including images and masks and according \n
to the SPOT folders organization"""


imType = 'ORTHO_SURF_CORR_PENTE'


#-----------------------------------------------------------------------
def getSpotImages(ipath, opath):
   """
   Returns the list of the SPOT Images in choronological order
   ARGs:
       INPUT:
            -ipath: SPOT images path
            -opath: output path
           
       OUTPUT:
            - A texte file named SpotImagesList.txt, 
              containing the names and path of the SPOT images 
            - A texte file named SpotImagesDateList.txt, 
              containing the list of the dates in chronological order
    
    IMPORTANT: to find the images it follows the folder structure of SPOT images
   """
   #Contient toutes les images trouvees
   file = open(opath+"/SPOTimagesList.txt", "w")
   filedate = open(opath+"/SPOTimagesDateList.txt", "w")
   count = 0
   imageList = []
   fList = []
   dateList = []
   
   #Find all matches and put them in a list 
   for image in glob.glob(ipath+"/*/*/*/*"+imType+"*.TIF"):
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
      for im in glob.glob(ipath+"/*/*/*/"+name):
         file.write(im)
         file.write('\n')
         fList.append(im) 
      count = count + 1
   filedate.close() 
   file.close()     
   return fList

#---------------------------------------------------------------

def getSpotCloudMask(imagePath):
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

def getSpotSatMask(imagePath):
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

def getSpotDivMask(imagePath):
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

def getSpotNoDataMask(imagePath):
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
def getList_SpotCloudMask(listimagePath):
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
      listMask.append(getSpotCloudMask(image))
  
   return listMask

def getList_SpotSatMask(listimagePath):
   """
   Get the list of the saturation masks for each image on the images list
   ARGs:
       INPUT:
            -listimagePath: the list with the absolute path of the images
       OUTPUT:
            -The list with the name of the corresponding masks
   """
   listMask = []
   for image in listimagePath:
      listMask.append(getSpotSatMask(image))

   return listMask

def getList_SpotDivMask(listimagePath):
   """
   Get the list of the 'divers' masks for each image on the images list
   ARGs:
       INPUT:
            -listimagePath: the list with the absolute path of the images
       OUTPUT:
            -The list with the name of the corresponding masks
   """
   listMask = []
   for image in listimagePath:
      listMask.append(getSpotDivMask(image))

   return listMask

def getList_SpotNoDataMask(listimagePath):
   """
   Get the list of the 'divers' masks for each image on the images list
   ARGs:
       INPUT:
            -listimagePath: the list with the absolute path of the images
       OUTPUT:
            -The list with the name of the corresponding masks
   """
   listMask = []
   for image in listimagePath:
      listMask.append(getSpotNoDataMask(image))

   return listMask

#--------------------------------------------------------------------
def getSpotImageRef(ipath, opath):

   imlist = getSpotImages(ipath, opath)
   imref = imlist[0]
   
   return imref
   
#---------------------------------------------------------------------

#getSpotImages(argv[1], argv[2])




