# -*- coding: utf-8 -*-
from Capteurs import Sensor
import glob
import os

from DataProcessing import GetBorderProp
class Spot4(Sensor):

    def __init__(self,path_image,opath):
        Sensor.__init__(self)
        self.name = 'Spot4'
        self.path = path_image
        self.bands["BANDS"] = {'green' : 1 , 'red' : 2, 'NIR' : 3, 'SWIR' : 4}
        self.nbBands = len(self.bands['BANDS'].keys())
        self.fimages = opath.opathT+"/SPOTimagesList.txt"
        self.fdates = opath.opathT+"/SPOTimagesDateList.txt"
        self.imType =  'ORTHO_SURF_CORR_PENTE'
        # TODO Try catch
        liste = self.getImages(opath)
        if len(liste)== 0:
            print "Erreur aucune image trouvee"
        else:
            self.imRef = liste[0]
        
        self.borderMask = None
        self.SerieTemp = opath.opathT+"ST_SPOT.TIF"
        self.SerieTempGap = opath.opathT+"ST_SPOT_GAP.TIF"
        self.SerieMask = opath.opathT+"ST_SPOT_MASK.TIF"

    def getImages(self,opath):

       file = open(self.fimages, "w")
       filedate = open(self.fdates, "w")
       count = 0
       imageList = []
       fList = []
       

       #Find all matches and put them in a list
       for image in glob.glob(self.path+"/*/*/*/*"+self.imType+"*.TIF"):
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
    def getList_CloudMask(self,listimagePath):
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
          listMask.append(self.getCloudMask(image))

       return listMask

    def getList_SatMask(self,listimagePath):
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
          listMask.append(self.getSatMask(image))

       return listMask

    def getList_DivMask(self,listimagePath):
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
          listMask.append(self.getDivMask(image))

       return listMask

    def getList_NoDataMask(self,listimagePath):
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
           listMask.append(self.getNoDataMask(image))
       return listMask



       
   ##  def CreateBorderMask(self, opath,imRef):
   ##      """ TODO : Gerer le resize si ce n'est pas la ref"""
        
   ##      imlist = self.getImages(opath)
   ##      mlist = self.getList_NoDataMask(imlist)
        
   ##      listMaskch = ""
   ##      listMask = []
   ##      propBorder = []
        
   ##      for i in range(len(mlist)):
   ##          name = mlist[i].split("/")
   ##          command = "otbcli_BandMath -il "+mlist[i]\
   ##          +" -out "+opath.opathT+"/"+name[-1]+" -exp "\
   ##          +"\"if(im1b1,1,0)\""
   ##          os.system(command)
   ##          print (command)
   ##          listMaskch = listMaskch+opath.opathT+"/"+name[-1]+" "
   ##          listMask.append(opath.opathT+"/"+name[-1])
        
   ##      expr = "0"
   ##      for i in range(len(listMask)):
   ##          expr += "+im"+str(i+1)+"b1"
        
   ##      BuildMaskSum = "otbcli_BandMath -il "+listMaskch+" -out "+opath.opathT+"/SumMaskS.tif -exp "+expr
   ##      print BuildMaskSum
   ##      #os.system(BuildMaskSum)
        
   ##         #Calculate how many bands will be used for building the common mask
        
   ##      for mask in listMask:
   ##          p = GetBorderProp(mask)
   ##          propBorder.append(p)
   ##      sumMean = 0
   ##      for value in propBorder:
   ##          sumMean = sumMean+value
   ##          meanMean = sumMean/len(propBorder)
   ##          usebands = 0
   ##      for value in propBorder:
   ##          if value>=meanMean:
   ##              usebands = usebands +1
        
   ##      #Builds the mask
   ##      expr = "\"if(im1b1>=8,1,0)\""
   ##      #expr = "\"if(im1b1>="+str(usebands)+",1,0)\""
   ##      BuildMaskBin = "otbcli_BandMath -il "+opath.opathT+"/SumMaskS.tif -out "+opath.opathT+"/MaskS.tif -exp "+expr
   ##      print BuildMaskBin
   ##      self.borderMask = opath.opathT+"/MaskS.tif"
   ##      #os.system(BuildMaskBin)

   ##      for mask in listMask:
   ##          os.remove(mask)

   ##      return 0

   ##  def createSerie(self, opath):
   ##      """
   ##      Concatenation of all the images SPOT to create one multitemporal multibands image
   ##      ARGs 
   ##      INPUT:
   ##           -ipath: absolute path of the images
   ##           -opath: path were the images will be concatenated
   ##      OUTPUT:
   ##           -Multitemporal, multiband serie   
   ##      """
   ##      imlist = self.getImages(opath)
   
   ##      ilist = ""
   ##      bandlist = []
   ##      bandinlist = []
   ##      bandclipped = []
        
   ##      for image in imlist:
   ##          ilist = ilist + image + " "
      

   ##      for image in imlist:
   ##          impath = image.split('/')
   ##          imname = impath[-1].split('.')
   ##          splitS = "otbcli_SplitImage -in "+image+" -out "+opath+"/"+impath[-1]
   ##          print splitS
   ##          os.system(splitS)
   ##          for band in range(0, int(Sbands)):
   ##              bnamein = imname[0]+"_"+str(band)+".TIF"
   ##              bnameout = imname[0]+"_"+str(band)+"_masked.tif"
   ##              maskB = "otbcli_BandMath -il "+opath+"/"+maskC+" "+opath+"/"+bnamein+" -exp \"if(im1b1==0,-10000,im2b1)\" -out "+bnameout
   ##              print maskB
   ##              os.system(maskB)
   ##              bandclipped.append(DP.ClipRasterToShp(bnameout, opath+"/"+maskCshp, opath))
         
   ##              bandinlist.append(opath+"/"+bnamein)
   ##              bandlist.append(opath+"/"+bnameout)
         
   ##      bandChain = " "

   ##      for bandclip in bandclipped:
   ##          bandChain = bandChain + bandclip + " "
        
   ##      Concatenate = "otbcli_ConcatenateImages -il "+bandChain+" -out "+opath+"/SPOT_MultiTempIm_clip.tif "
   ##      print Concatenate
   ##      print Concatenate
   ##      os.system(Concatenate)
   ##      return 0
   ## #print bandlist
   ## #print bandinlist
   ## #print bandclipped

   ## #for image in bandlist:
   ##    #os.remove(image)
   ## #for image in bandinlist:
   ##    #os.remove(image)
   ## #for image in bandclipped:
   ##    #os.remove(i)

  
   ##  def CreateMaskSeriesSpot(self, opath):
   ##      """
   ##      Builds one multitemporal binary mask of SPOT images

   ##      ARGs 
   ##      INPUT:
   ##           -ipath: absolute path of the images
   ##           -opath: path were the multitemporal mask will be created
   ##           OUTPUT:
   ##           -Multitemporal binary mask .tif
   ##      """


   ##      imlist = self.getImages(opath)
   ##      clist = self.getList_SpotCloudMask(imlist)
   ##      slist = self.getList_SpotSatMask(imlist)
   ##      dlist = self.getList_SpotNoDataMask(imlist)
   ##      maskC = opath+"/MaskCommunSL.tif"
   
  
   ##      chain = ""
   ##      bandChain = ""
   ##      listallNames = []  
   ##      bandclipped = []

   ##      for im in range(0,len(imlist)):
   ##          impath = imlist[im].split('/')
   ##          imname = impath[-1].split('.')
   ##          name = opath+'/'+imname[0]+'_MASK.tif'
   ##          chain = clist[im]+' '+slist[im]+' '+dlist[im]
   ##      #The following expression is for cloud, saturation and border masks
   ##      Binary = "otbcli_BandMath -il "+maskC+" "+chain\
   ##    +" -exp \"(im1b1 * (if(im2b1>0,1,0) or if(im3b1>0,1,0))) or (if(im4b1,0,1)*im1b1)\" -out "+name
   ##      print Binary
   ##      os.system(Binary)
   ##      bandclipped.append(DP.ClipRasterToShp(name, opath+"/"+maskCshp, opath))
   ##      listallNames.append(name)
   
   ##      for bandclip in bandclipped:
   ##          bandChain = bandChain + bandclip + " "
   
   ##      Concatenate = "otbcli_ConcatenateImages -il "+bandChain+" -out "+opath+"/SPOT_MultiTempMask_clip.tif "
   ##      os.system(Concatenate)

   ##      for i in listallNames:
   ##          os.remove(i)
   
   ##      for i in bandclipped:
   ##          os.remove(i)
   
   ##      return 0
