from Capteurs import Sensor
import glob
import os
from osgeo import osr,ogr,gdal

class Landsat8(Sensor):

    def __init__(self,path_image,opath):
        Sensor.__init__(self)
        self.name = 'Landsat8'
        self.path = path_image
        self.bands["BANDS"] = { "aero" : 1 , "blue" : 2 , "green" : 3, "red" : 4, "NIR" : 5, "SWIR" : 6 , "SWIR2" : 7}
        self.nbBands = len(self.bands['BANDS'].keys())
        self.imType = "D0001H0001" #tile ????
        self.fdates = opath.opathT+"/LANDSATimagesDateList_"+self.imType+".txt"
        self.fimages = opath.opathT+"/LANDSATimagesList_"+self.imType+".txt"
        self.borderMask = None

        # TODO Try catch
        liste = self.getImages(opath)
        if len(liste)== 0:
            print "Erreur aucune image trouvee"
        else:
            self.imRef = liste[0]
        
    
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
           listMask.append(getCloudMask(image))

        return listMask

    def getList_SatMask(self,listimagePath):
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
           listMask.append(getSatMask(image))

        return listMask

    def getList_DivMask(self,listimagePath):
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
        for image in listimagePath:
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


    def CreateBorderMask(self, opath, imref):
        """
        Creates the mask of borders 
        ARGs 
        INPUT:
        -ipath: absolute path of the LANDSAT images
        -opath: path were the mask will be created
        OUTPUT:
        -Border mask 30 m
        """
   
        imlist = self.getImages(opath.opathT)
        mlist = self.getList_NoDataMask(imlist)
        print imlist
        print mlist
        #Get the info of the image

        ds = gdal.Open(imref, GA_ReadOnly)
        nb_col=ds.RasterXSize
        nb_lig=ds.RasterYSize
        proj=ds.GetProjection()
        gt=ds.GetGeoTransform()
        ulx = gt[0]
        uly = gt[3]
        lrx = gt[0] + nb_col*gt[1] + nb_lig*gt[2]
        lry = gt[3] + nb_col*gt[4] + nb_lig*gt[5]
        propBorder = []

        srs=osr.SpatialReference(proj)
   
        #chain_proj = srs.GetAuthorityName('PROJCS')+':'+srs.GetAuthorityCode('PROJCS')
        chain_proj = "EPSG:2154"
   
        resolX = abs(gt[1]) # resolution en metres de l'image d'arrivee 
        resolY = abs(gt[5]) # resolution en metres de l'image d'arrivee
        chain_extend = str(ulx)+' '+str(lry)+' '+str(lrx)+' '+str(uly)  

        #Builds the individual binary masks
        listMaskch = ""
        listMask = []
        for i in range(len(mlist)):
            name = mlist[i].split("/")
            os.system("otbcli_BandMath -il "+mlist[i]\
                      +" -out "+opath.opathT+"/"+name[-1]+" -exp "\
                      #+"\"if(im1b1 and 00000001,0,1)\"")
                      +"\"if(im1b1,1,0)\"")
            listMaskch = listMaskch+opath.opathT+"/"+name[-1]+" "
            listMask.append(opath.opathT+"/"+name[-1])
  
        #Builds the complete binary mask
        expr = "0"
        for i in range(len(listMask)):
            expr += "+im"+str(i+1)+"b1"

        BuildMaskSum = "otbcli_BandMath -il "+listMaskch+" -out "+opath.opathT+"/SumMaskL30m.tif -exp "+expr
        os.system(BuildMaskSum)

        #Calculate how many bands will be used for building the common mask

        for mask in listMask:
            p = GetBorderProp(mask)
            propBorder.append(p)
        sumMean = 0
        for value in propBorder:
            sumMean = sumMean+value
        meanMean = sumMean/len(propBorder)
        usebands = 0
        for value in propBorder:
            if value>=meanMean:
                usebands = usebands +1
  
        #Builds the mask
        #expr = "\"if(im1b1>=16,1,0)\""
        #expr = "\"if(im1b1>="+str(usebands)+",1,0)\""
        #Builds the mask
        #expr = "\"if(im1b1>=6,1,0)\""
        expr = "\"if(im1b1>="+str(usebands)+",1,0)\""
        BuildMaskBin = "otbcli_BandMath -il "+opath.opathT+"/SumMaskL30m.tif -out "+opath.opathT+"/MaskL30m.tif -exp "+expr
        print BuildMaskBin
        os.system(BuildMaskBin)

        ResizeMaskBin = 'gdalwarp -of GTiff -r %s -tr %d %d -te %s -t_srs %s %s %s \n'% ('near', resolX,resolY,chain_extend,chain_proj, opath.opathT+"/MaskL30m.tif", opath.opathT+"/MaskL"+res+"m.tif")
        os.system(ResizeMaskBin)

        self.borderMask = opath.opathT+"/MaskL"+res+"m.tif"
      #for mask in listMask:
        #os.remove(mask)


    def createSerieLandsat(self, opath):
        """
        Concatenation of all the images Landsat to create one multitemporal multibands image
        ARGs 
        INPUT:
             -ipath: absolute path of the images
             -opath: path were the images will be concatenated
        OUTPUT:
             -Multitemporal, multiband serie   
        """
        imlist = self.getResizedImages(opath,opath)
        ilist = ""
        olist = []
        bandlist = []
        bandclipped = []
        
        for image in imlist:
            ilist = ilist + image + " "
            olist.append(image)
            
        for image in imlist:
            impath = image.split('/')
            imname = impath[-1].split('.')
            splitS = "otbcli_SplitImage -in "+image+" -out "+opath+"/"+impath[-1]
      
            os.system(splitS)
            for band in range(0, int(Lbands)):
                bnamein = imname[0]+"_"+str(band)+".TIF"
                bnameout = imname[0]+"_"+str(band)+"_masked.TIF"
                maskB = "otbcli_BandMath -il "+opath+"/"+maskC+" "+opath+"/"+bnamein+" -exp \"if(im1b1==0,-10000, if(im2b1!=-10000 and im2b1<0,0,im2b1))\" -out "+opath+"/"+bnameout
                print maskB
                os.system(maskB)
                bandclipped.append(DP.ClipRasterToShp(opath+"/"+bnameout, opath+"/"+maskCshp, opath))
                print maskB
                bandlist.append(opath+"/"+bnameout)
 
        bandChain = " "

        for bandclip in bandclipped:
            bandChain = bandChain + bandclip + " "

        Concatenate = "otbcli_ConcatenateImages -il "+bandChain+" -out "+opath+"/LANDSAT_r_MultiTempIm_clip.tif "
        os.system(Concatenate)

        outname = "LANDSAT_r_MultiTempIm4bpi_clip.tif"
        chain = ""
        bands = [bandsL["green"], bandsL["red"], bandsL["NIR"], bandsL["SWIR1"]]
   
        for image in imlist:
            for band in bands:
                name = image.split('.')
                newname = name[0]+'_'+str(band-1)+'_masked_clipped.TIF'
                chain = chain + newname +" "
   
        Concatenate = "otbcli_ConcatenateImages -il "+chain+" -out "+opath+"/"+outname
        print Concatenate
        os.system(Concatenate)
        return 0
    
   #for image in bandlist:
      #os.remove(image)

   #for image in bandclipped:
      #os.remove(image)
 
    def ResizeImages(self, opath, imref):
        """
        Resizes LANDSAT images using one spot image
        ARGs 
        INPUT:
             -ipath: absolute path of the LANDSAT images
             -opath: path were the mask will be created
             -imref: SPOT Image to use for resizing
        OUTPUT:
             - A text file containing the list of LANDSAT images resized
        """
        imlist = self.getImages(opath)
  
        fileim = open(opath+"/LANDSATimagesListResize.txt", "w")
        imlistout = []
   
        ds = gdal.Open(imref, GA_ReadOnly)
        nb_col=ds.RasterXSize
        nb_lig=ds.RasterYSize
        proj=ds.GetProjection()
        gt=ds.GetGeoTransform()
        ulx = gt[0]
        uly = gt[3]
        lrx = gt[0] + nb_col*gt[1] + nb_lig*gt[2]
        lry = gt[3] + nb_col*gt[4] + nb_lig*gt[5]

        srs=osr.SpatialReference(proj)

   
        chain_proj = "EPSG:2154"
   
        resolX = abs(gt[1]) # resolution en metres de l'image d'arrivee 
        resolY = abs(gt[5]) # resolution en metres de l'image d'arrivee
        chain_extend = str(ulx)+' '+str(lry)+' '+str(lrx)+' '+str(uly)   
 
        for image in imlist:
            line = image.split('/')
            name = line[-1].split('.')
            newname = '_'.join(name[0:-1])
            imout = opath+"/"+newname+"_"+res+"m.TIF"

            Resize = 'gdalwarp -of GTiff -r %s -tr %d %d -te %s -t_srs %s %s %s \n'% ('cubic', resolX,resolY,chain_extend,chain_proj, image, imout)
            print Resize
            os.system(Resize)
      
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
        cmask = self.getList_CloudMask(imlist)
        smask = self.getList_SatMask(imlist)
        dmask = self.getList_DivMask(imlist)
   
        allmlists = [cmask, smask, dmask]

        expMask = {"NUA":"if(im1b1 and 00000001,1,if(im1b1 and 00001000,1,0))", "SAT":"im1b1!=0", "DIV":"if(im1b1 and 00000001,1,0)"}
        ds = gdal.Open(imref, GA_ReadOnly)
        nb_col=ds.RasterXSize
        nb_lig=ds.RasterYSize
        proj=ds.GetProjection()
        gt=ds.GetGeoTransform()
        ulx = gt[0]
        uly = gt[3]
        lrx = gt[0] + nb_col*gt[1] + nb_lig*gt[2]
        lry = gt[3] + nb_col*gt[4] + nb_lig*gt[5]

        srs=osr.SpatialReference(proj)
   
        chain_proj = "EPSG:2154"
   

        resolX = abs(gt[1]) # resolution en metres de l'image d'arrivee 
        resolY = abs(gt[5]) # resolution en metres de l'image d'arrivee
        chain_extend = str(ulx)+' '+str(lry)+' '+str(lrx)+' '+str(uly) 

        for mlist in allmlists:
            for mask in mlist:
                line = mask.split('/')
                name = line[-1].split('.')
                typeMask = name[0].split('_')[-1]
                namep = name[-2]+"bordbin"
                namer = name[-2]+res+"m"
                newnameb = namep+'.'+name[-1]
                newnamer = namer+'.'+name[-1]
                imout = opath+"/"+newnameb
                imoutr = opath+"/"+newnamer
                if typeMask == 'NUA':
                    exp = expMask['NUA']
                elif typeMask == 'SAT':
                    exp = expMask['SAT']
                elif typeMask == 'DIV':
                    exp = expMask['DIV']
                binary = "otbcli_BandMath -il "+mask+" -exp \""+exp+"\" -out "+imout
                print binary
                os.system(binary)
                Resize = 'gdalwarp -of GTiff -r %s -tr %d %d -te %s -t_srs %s %s %s \n'% ('near', resolX,resolY,chain_extend,chain_proj, imout, imoutr)
                print Resize
                os.system(Resize)

    def CreateMaskSeriesLandsat(ipath, opath):
        """
        Builds one multitemporal binary mask of SPOT images

        ARGs 
        INPUT:
             -ipath: absolute path of the resized masks
             -opath: path were the multitemporal mask will be created
             OUTPUT:
             -Multitemporal binary mask .tif
        """
        imlist = self.getResizedImages(ipath, opath)
        clist = self.getList_ResCloudMask(imlist)
        slist = self.getList_ResSatMask(imlist)
        dlist = self.getList_ResDivMask(imlist)
        maskC = opath+"/MaskCommunSL.tif"
   
        print clist
        chain = ""
        allNames = ""
        listallNames = []
        bandclipped = []
        bandChain = ""

        for im in range(0,len(imlist)):
            impath = imlist[im].split('/')
            imname = impath[-1].split('.')
            name = opath+'/'+imname[0]+'_MASK.TIF'
            chain = clist[im]+' '+slist[im]+' '+dlist[im]
            Binary = "otbcli_BandMath -il "+maskC+" "+chain+" -exp \"(im1b1 * (if(im2b1>0,1,0) or if(im3b1>0,1,0) or if(im4b1>0,1,0)))\" -out "+name
            print Binary
            os.system(Binary)
            bandclipped.append(DP.ClipRasterToShp(name, opath+"/"+maskCshp, opath))
            listallNames.append(name)

        for bandclip in bandclipped:
            bandChain = bandChain + bandclip + " "

        Concatenate = "otbcli_ConcatenateImages -il "+bandChain+" -out "+opath+"/LANDSAT_r_MultiTempMask_clip.tif "+pixelo
        print Concatenate
        os.system(Concatenate)

        
        return 0 
