from Capteurs import Sensor
import glob
import os
from osgeo import osr,ogr,gdal
from Capteurs import MonException

class Landsat8(Sensor):

    def __init__(self,path_image,opath,fconf,workRes):
        Sensor.__init__(self)
        self.name = 'Landsat8'
        self.path = path_image
        self.bands["BANDS"] = { "aero" : 1 , "blue" : 2 , "green" : 3, "red" : 4, "NIR" : 5, "SWIR" : 6 , "SWIR2" : 7}
        self.nbBands = len(self.bands['BANDS'].keys())
        
        self.fdates = opath.opathT+"/LANDSATimagesDateList_"+self.imType+".txt"
        self.fimages = opath.opathT+"/LANDSATimagesList_"+self.imType+".txt"
        self.borderMask = None
        
        self.imType = "ORTHO_SURF_CORR_PENTE"
        self.sumMask = opath.opathT+"/Formosat_Sum_Mask.tif"
        self.borderMaskN = opath.opathT+"/Formosat_Border_MaskN.tif"
        self.borderMaskR = opath.opath+"/Formosat_Border_MaskR.tif"
        
        
        
        cfg = Config(fconf)
        conf = cfg.Landsat
        
        self.struct_path ="/*"+conf.tile+"*/*"
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

    def getImages(self, opath):
       """
       Returns the list of the LANDSAT Images in choronological order
           INPUT:
                -ipath: LANDSAT images path
                -opath: output path

           OUTPUT:
                - A texte file named LandsatImagesList.txt, containing the names and path of the LANDSAT images 
                - A texte file named LandsatImagesDateList.txt, containing the list of the dates in chronological order

       """

       file = open(self.fimages, "w")
       filedate = open(self.fdates, "w")
       count = 0
       imageList = []
       fList = []
       dateList = []

       #Find all matches and put them in a list 
       for image in glob.glob(self.path+self.struct_path+self.imType+"*.TIF"):
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

       if len(fList)== 0:
           print "Erreur aucune image trouvee"
       else:
           self.imRef = fList[0]
           
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
        imageName = folder[-1].split('.')
        imageNameP = imageName[0].split('_')
        maskName = '_'.join(imageNameP[0:-5])+'_'+imageNameP[-1]+'_NUA.TIF'
        mask = '/'.join(folder[0:-1])+'/MASK/'+maskName

        return mask


    def getSatMask(self,imagePath):
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

    def getDivMask(self,imagePath):
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

    def getNoDataMask(self,imagePath):
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
           listMask.append(getCloudMask(image))

        return listMask

    def getList_SatMask(self):
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
           listMask.append(getSatMask(image))

        return listMask

    def getList_DivMask(self):
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
           listMask.append(getDivMask(image))

        return listMask

    def getList_NoDataMask(self,listimagePath):
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
           listMask.append(getNoDataMask(image))

        return listMask

    def getResCloudMask(self,imagePath):
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


    def getResSatMask(self,imagePath):
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

    def getResDivMask(self,imagePath):
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
    
    def getList_ResCloudMask(self,listimagePath):
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
           listMask.append(getResCloudMask(image))

        return listMask

    def getList_ResSatMask(self,listimagePath):
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
           listMask.append(getResSatMask(image))

        return listMask

    def getList_ResDivMask(self,listimagePath):
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
           listMask.append(getResDivMask(image))

        return listMask

    def getResizedImages(self, opath):
        
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

