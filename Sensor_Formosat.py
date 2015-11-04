#from config import Config
from Capteurs import Sensor
import glob

from Capteurs import MonException

    
class Formosat(Sensor):

    def __init__(self,path_image,opath,fconf,workRes):
        Sensor.__init__(self)
        self.name = 'SudouestKalideos'
        self.path = path_image
        self.bands["BANDS"] = { "blue" : 1 , "green" : 2 , "red" : 3 , "NIR" : 4}
        self.nbBands = len(self.bands['BANDS'].keys())
        self.fimages = opath.opathT+"/FormosatimagesList.txt"
        self.fdates = opath.opathT+"/FormosatimagesDateList.txt"
        self.native_res = 8
        self.imType = "ortho_surf_pente_8m"
        self.sumMask = opath.opathT+"/Formosat_Sum_Mask.tif"
        self.borderMaskN = opath.opathT+"/Formosat_Border_MaskN.tif"
        self.borderMaskR = opath.opath+"/Formosat_Border_MaskR.tif"
        
        self.struct_path = "/*"
        
 #       cfg = Config(fconf)
 #       conf = cfg.Formosat
        
        #print conf
 #       self.serieTemp = opath.opathT+conf.serieTempo
 #       self.serieTempMask = opath.opathT+conf.serieTempoMask
 #       self.serieTempGap = opath.opathT+conf.serieTempoGap
        
        #self.serieTempPrimGap = opath.opathT+conf.serieTempoPrimGap
        #A virer pour config
        self.serieTemp = opath.opathT+"/Formosat_ST_REFL.tif"
        self.serieTempMask = opath.opathT+"/Formosat_ST_MASK.tif"
        self.serieTempGap = opath.opathT+"/Formosat_ST_REFL_GAP.tif"       
        self.nodata_MASK = False
        #self.serieTempPrimGap = opath.opathT+conf.serieTempoPrimGap

        self.work_res = workRes
        
#        if conf.nodata_Mask == 'False':
#            self.nodata_MASK = False
#        elif conf.nodata_Mask == "True":
#            self.nodata_MASK = True
#        else:
#            print "Value Error for No Data Mask flag. NoDataMask not considered"
#            self.nodata_MASK = False
        

        try:
            
            liste = self.getImages(opath)
            if len(liste) == 0:
                raise MonException("ERROR : No valid images in %s"%self.path)
            else:
                self.imRef = liste[0]
        except MonException, mess:
            print mess
   

    def getImages(self,opath):

        file = open(self.fimages, "w")
        filedate = open(self.fdates, "w")
        count = 0
        imageList = []
        fList = []

        for image in glob.glob(self.path+self.struct_path+self.imType+".tif"):
            imagePath = image.split("/")
            imageName = imagePath[-1].split('.')
            imageNameParts = imageName[0].split('_')
            
            imageList.append(imageNameParts)

        #Organize the names by date according to SPOT4 naming
        imageList.sort(key=lambda x: x[1])

        #Write all the images in chronological order in a text file
        for imSorted  in imageList:
            filedate.write(imSorted[1])
            filedate.write('\n')
            name = '_'.join(imSorted)+'.tif'
            for im in glob.glob(self.path+"/"+name):
                file.write(im)
                file.write('\n')
                fList.append(im)
            count = count + 1
        filedate.close()
        file.close()
        
        return fList

    def getNoDataMask(image):
        pass #Non definit pour formosat
    def getList_NoDataMask(self,liste):
        pass #Non definit pour formosat

    def getList_CloudMask(self):
        liste_cloud = glob.glob(self.path+"/*.nuages.tif")
        return liste_cloud

    def getList_SatMask(self):
        liste_sat = glob.glob(self.path+"/*.saturation.tif")
        return liste_sat

    def getDivMask(self,imagepath):
        pass
    def getList_DivMask(self):
        liste_div = glob.glob(self.path+"/*.bord_eau.tif")
        return liste_div
    
    def getList_ResCloudMask(self):
        pass

    def getList_ResSatMask(self):
        pass

    def getList_ResDivMask(self):
        pass
