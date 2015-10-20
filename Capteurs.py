# -*- coding: utf-8 -*-
"""
Class Sensor

Define each sensor for generic processing

"""
class Sensor(object):
    
    def __init__(self):
        self.bands = {}
        self.name = None
        self.path = None
        self.fimages = None
        self.fdates = None
        

class Spot4(Sensor):

    def __init__(self,path_image,opath):
        self.name = 'Spot4'
        self.path = path_image
        self.bands["BANDS"] = {'green' : 1 , 'red' : 2, 'NIR' : 3, 'SWIR' : 4}
        self.fimages = opath.opathT+"SPOTimagesList.txt"
        self.fdates = opath.opathT+"SPOTimagesDateList.txt"
        self.imType =  'ORTHO_SURF_CORR_PENTE'

        
    def getSpotImages(self):
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
       file = open(self.fimages, "w")
       filedate = open(self.fdates, "w")
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
          for im in glob.glob(self.path+"/*/*/*/"+name):
             file.write(im)
             file.write('\n')
             fList.append(im) 
          count = count + 1
       filedate.close() 
       file.close()     
   return fList

   def getSpotCloudMask(self):
        """
        Get the name of the cloud mask using the name of the image
        ARGs:
            INPUT:
                -imagePath: the absolute path of one image
            OUTPUT:
                -The name of the corresponding cloud mask

        """
        folder = self.path.split('/')
        ifolder = '/'.join(folder[0:-1])+'/MASK'
        os.chdir(ifolder)
        fmask = glob.glob("*_NUA.TIF")
        mask = os.getcwd()+'/'+fmask[0]

   return mask

    def getSpotSatMask(self):
       """
       Get the name of the saturation mask using the name of the image
       ARGs:
           INPUT:
                -imagePath: the absolute path of one image
           OUTPUT:
                -The name of the corresponding saturation mask

       """
       folder = self.path.split('/')
       ifolder = '/'.join(folder[0:-1])+'/MASK'
       os.chdir(ifolder)
       fmask = glob.glob("*_SAT.TIF")
       mask = os.getcwd()+'/'+fmask[0]

       return mask

    def getSpotDivMask(self):
       """
       Get the name of the 'divers' mask using the name of the image
       ARGs:
           INPUT:
                -imagePath: the absolute path of one image
           OUTPUT:
                -The name of the corresponding divers mask

       """
       folder = self.path.split('/')
       ifolder = '/'.join(folder[0:-1])+'/MASK'
       os.chdir(ifolder)
       fmask = glob.glob("*_DIV.TIF")
       mask = os.getcwd()+'/'+fmask[0]   

       return mask

    def getSpotNoDataMask(self):
       """
       Get the name of the 'divers' mask using the name of the image
       ARGs:
           INPUT:
                -imagePath: the absolute path of one image
           OUTPUT:
                -The name of the corresponding divers mask

       """
       folder = self.path.split('/')
       ifolder = '/'.join(folder[0:-1])+'/MASK'
       os.chdir(ifolder)
       fmask = glob.glob("*_NODATA.TIF")
       mask = os.getcwd()+'/'+fmask[0]   

       return mask
    #----------------------------------------------------------------------
    def getList_SpotCloudMask(self,listimagePath):
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

    def getList_SpotSatMask(self,listimagePath):
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

    def getList_SpotDivMask(self,listimagePath):
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

    def getList_SpotNoDataMask(self,listimagePath):
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
          listMask.append(self.getSpotNoDataMask(image))

       return listMask

    #--------------------------------------------------------------------
    def getSpotImageRef(self):

       imlist = self.getSpotImages()
       imref = imlist[0]

   return imref

class Landsat8(Sensor):

    def __init__(self,path_image):
        self.name = 'Landsat8'
        self.path = path_image
        self.bands["BANDS"] = { "aero" : 1 , "blue" : 2 , "green" : 3, "red" : 4, "NIR" : 5, "SWIR1" : 6 , "SWIR2" : 7}
        self.fimages = opath.opathT+"LANDSATimagesList.txt"
        self.fdates = opath.opathT+"LANDSATimagesDateList.txt"
        self.imType = "D0001H0001" #tile ????
        
    def getLandsatImages(self, opath):
       """
       Returns the list of the LANDSAT Images in choronological order
           INPUT:
                -ipath: LANDSAT images path
                -opath: output path

           OUTPUT:
                - A texte file named LandsatImagesList.txt, containing the names and path of the LANDSAT images 
                - A texte file named LandsatImagesDateList.txt, containing the list of the dates in chronological order

       """

       file = open(opath.opathT+"/LANDSATimagesList_"+self.imType+".txt", "w")
       filedate = open(opath.opathT+"/LANDSATimagesDateList_"+self.imType+".txt", "w")
       count = 0
       imageList = []
       fList = []
       dateList = []

       #Find all matches and put them in a list 
       for image in glob.glob(self.path+"/*"+self.imType+"*/*ORTHO_SURF_CORR_PENTE*.TIF"):
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
    def getResizedLandsatImages(self, opath):
       """
       Returns the list of the resized LANDSAT Images in choronological order
           INPUT:
                -ipath: LANDSAT images path
                -opath: output path

           OUTPUT:
                - A texte file named LandsatImagesList.txt, containing the names and path of the LANDSAT images 
                - A texte file named LandsatImagesDateList.txt, containing the list of the dates in chronological order

       """

       file = open(opath.opathT+"/LANDSATimagesListResize.txt", "w")
       filedate = open(opath.opathT+"/LANDSATresizedImagesDateList.txt", "w")
       count = 0
       imageList = []
       fList = []
       dateList = []

       #print opath
       #Find all matches and put them in a list 
       for image in glob.glob(opath.opathT+"/"+"*_"+res+"m.TIF"):
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
    def getLandsatCloudMask(self,imagePath):
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


    def getLandsatSatMask(self,imagePath):
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

    def getLandsatDivMask(self,imagePath):
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

    def getLandsatNoDataMask(self,imagePath):
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

    def getLandsatBinDivMask(self,imagePath):
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
    def getList_LandsatCloudMask(self,listimagePath):
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

    def getList_LandsatSatMask(self,listimagePath):
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

    def getList_LandsatDivMask(self,listimagePath):
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

    def getList_LandsatNoDataMask(self,listimagePath):
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

    def getList_LandsatBinDivMask(self,listimagePath):
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

    def getLandsatResCloudMask(self,imagePath):
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


    def getLandsatResSatMask(self,imagePath):
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

    def getLandsatResDivMask(self,imagePath):
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
    def getList_LandsatResCloudMask(self,listimagePath):
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

    def getList_LandsatResSatMask(self,listimagePath):
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

    def getList_LandsatResDivMask(self,listimagePath):
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
    def getLandsatImageRef(self,ipath, opath):

       imlist = self.getLandsatImages(ipath, opath, "*30m.tif")
       imref = imlist[0]

   return imref






class Formosat(Sensor):

    def __init__(self,path_image):
        self.name = 'Formosat'
        self.path = path_image
        self.bands["BANDS"] = { "blue" : 1 , "green" : 2 , "red" : 3 , "NIR" : 4}
        
        
