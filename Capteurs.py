# -*- coding: utf-8 -*-
"""
Class Sensor

Define each sensor for generic processing

"""
import glob
from osgeo import gdal,osr,ogr
import os
import New_DataProcessing as DP
pixelo = 'float'
class Sensor(object):
    
    def __init__(self):
        self.bands = {}
        self.name = None
        self.path = None
        self.fimages = None
        self.fdates = None
        self.fimagesRes = None
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
        
    def getImages(self,opath):
        pass

    def getList_NoDataMask(self,liste):
        pass

    def getList_CloudMask(self):
        pass

    def getList_SatMask(self):
        pass
    
    def getList_DivMask(self):
        pass
    
    def getList_ResCloudMask(self):
        pass

    def getList_ResSatMask(self):
        pass

    def getList_ResDivMask(self):
        pass

    def GetBorderProp(self,mask):
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
    
    def CreateBorderMask(self,opath,imref):

        
        imlist = self.getImages(opath.opathT)
        mlist = self.getList_DivMask()

        ds = gdal.Open(imref, gdal.GA_ReadOnly)
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
            ## os.system("otbcli_BandMath -il "+mlist[i]\
            ##           +" -out "+opath.opathT+"/"+name[-1]+" -exp "\
            ##           +"\"if(im1b1 and 00000001,0,1)\"")
            ##           #+"\"if(im1b1,1,0)\"")#valide pour masque NoData
            listMaskch = listMaskch+opath.opathT+"/"+name[-1]+" "
            listMask.append(opath.opathT+"/"+name[-1])
  
        #Builds the complete binary mask
        expr = "0"
        for i in range(len(listMask)):
            expr += "+im"+str(i+1)+"b1"

        BuildMaskSum = "otbcli_BandMath -il "+listMaskch+" -out "+self.sumMask+" -exp "+expr
        #os.system(BuildMaskSum)

        #Calculate how many bands will be used for building the common mask

        for mask in listMask:
            p = self.GetBorderProp(mask)
            propBorder.append(p)
        sumMean = 0
        for value in propBorder:
            sumMean = sumMean+value
            meanMean = sumMean/len(propBorder)
            usebands = 0
        for value in propBorder:
            if value>=meanMean:
                usebands = usebands +1

        expr = "\"if(im1b1>="+str(usebands)+",1,0)\""
        BuildMaskBin = "otbcli_BandMath -il "+self.sumMask+" -out "+self.borderMaskN+" -exp "+expr
        print BuildMaskBin
        #os.system(BuildMaskBin)
        if (self.work_res == self.native_res) :
            self.borderMask = self.borderMaskN
        else:
            
            ResizeMaskBin = 'gdalwarp -of GTiff -r %s -tr %d %d -te %s -t_srs %s %s %s \n'% ('near', resolX,resolY,chain_extend,chain_proj, self.borderMaskN,self.borderMaskR)
            #os.system(ResizeMaskBin)
            self.borderMask = self.borderMaskR

        
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

   
        chain_proj = "EPSG:2154"
   
        resolX = abs(gt[1]) # resolution en metres de l'image d'arrivee 
        resolY = abs(gt[5]) # resolution en metres de l'image d'arrivee
        chain_extend = str(ulx)+' '+str(lry)+' '+str(lrx)+' '+str(uly)   
 
        for image in imlist:
            line = image.split('/')
            name = line[-1].split('.')
            newname = '_'.join(name[0:-1])
            imout = opath+"/"+newname+"_"+self.work_res+"m.TIF"

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
                namer = name[-2]+self.work_res+"m"
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
        file = open(self.fimagesRes, "w")
        filedate = open(self.fdatesRes, "w")
        count = 0
        imageList = []
        fList = []
        dateList = []
    

        #Find all matches and put them in a list 
        for image in glob.glob(opath.opathT+"/"+self.name+"*_"+self.work_res+"m.TIF"):
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
        for im in glob.glob(opath.opathT+"/"+name):
            file.write(im)
            file.write('\n')
            fList.append(im) 
            count = count + 1
        filedate.close() 
        file.close()     
    
        return fList


    def createMaskSeries(self, opath):
        """
        Builds one multitemporal binary mask of SPOT images

        ARGs 
        INPUT:
             -ipath: absolute path of the resized masks
             -opath: path were the multitemporal mask will be created
             OUTPUT:
             -Multitemporal binary mask .tif
        """
        if self.work_res == self.native_res:
            print "res native"
            imlist = self.getImages(opath)
            clist = self.getList_CloudMask()
            slist = self.getList_SatMask()
            dlist = self.getList_DivMask()
        else:
            imlist = self.getResizedImages(opath)
            clist = self.getList_ResCloudMask()
            slist = self.getList_ResSatMask()
            dlist = self.getList_ResDivMask()
        maskC = opath+"/MaskCommunSL.tif" # image ecrite par createcommonzone
        maskCshp = opath+"/MaskCommunSL.shp"
        
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
            bandclipped.append(DP.ClipRasterToShp(name, maskCshp, opath))
            listallNames.append(name)

        for bandclip in bandclipped:
            bandChain = bandChain + bandclip + " "

        Concatenate = "otbcli_ConcatenateImages -il "+bandChain+" -out "+self.serieTempMask+" "+pixelo
        print Concatenate
        os.system(Concatenate)

        
        return 0 

    def createSerie(self, opath):
        """
        Concatenation of all the images Landsat to create one multitemporal multibands image
        ARGs 
        INPUT:
             -ipath: absolute path of the images
             -opath: path were the images will be concatenated
        OUTPUT:
             -Multitemporal, multiband serie   
        """
        if self.work_res == self.native_res:
            imlist = self.getImages(opath)
        else:
            imlist = self.getResizedImages(opath,opath)
        ilist = ""
        olist = []
        bandlist = []
        bandclipped = []
        bands = len(self.bands["BANDS"].keys())

        maskC = opath+"/MaskCommunSL.tif" # image ecrite par createcommonzone
        maskCshp = opath+"/MaskCommunSL.shp"
        for image in imlist:
            ilist = ilist + image + " "
            olist.append(image)
            
        for image in imlist:
            impath = image.split('/')
            imname = impath[-1].split('.')
            splitS = "otbcli_SplitImage -in "+image+" -out "+opath+"/"+impath[-1]
            print "impath-1 : ",opath+"/"+impath[-1]
            
            os.system(splitS)
            for band in range(0, int(bands)):
                bnamein = imname[0]+"_"+str(band)+".tif"
                bnameout = imname[0]+"_"+str(band)+"_masked.tif"
                maskB = "otbcli_BandMath -il "+maskC+" "+opath+"/"+bnamein+" -exp \"if(im1b1==0,-10000, if(im2b1!=-10000 and im2b1<0,0,im2b1))\" -out "+opath+"/"+bnameout
                print "avant bandmath",maskB
                os.system(maskB)
                print "apres bandmath"
                bandclipped.append(DP.ClipRasterToShp(opath+"/"+bnameout, maskCshp, opath))
                print maskB
                bandlist.append(opath+"/"+bnameout)
 
        bandChain = " "

        for bandclip in bandclipped:
            bandChain = bandChain + bandclip + " "

        Concatenate = "otbcli_ConcatenateImages -il "+bandChain+" -out "+self.serieTemp
        os.system(Concatenate)

        ## outname = "LANDSAT_r_MultiTempIm4bpi_clip.tif"
        ## chain = ""
        ## bands = [bandsL["green"], bandsL["red"], bandsL["NIR"], bandsL["SWIR1"]]
   
        ## for image in imlist:
        ##     for band in bands:
        ##         name = image.split('.')
        ##         newname = name[0]+'_'+str(band-1)+'_masked_clipped.TIF'
        ##         chain = chain + newname +" "
   
        ## Concatenate = "otbcli_ConcatenateImages -il "+chain+" -out "+opath+"/"+outname
        ## print Concatenate
        ## os.system(Concatenate)
        ## return 0
