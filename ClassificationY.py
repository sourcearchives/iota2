
import ClassificationN as CL
import os

#annee = 2007,2008,2009,2010,2011,2012,2013
def dicRF():
   rf = {}
   rf['classifier'] = 'rf'
   rf['classifier.rf.min'] = 5
   rf['classifier.rf.max'] = 25
   rf['sample.mt'] = -1
   rf['sample.mv'] = 0
   rf['sample.vfn'] = "ID_CLASS"
   rf['sample.vtr'] = 0.1
   return rf


def learnModel(Serie_T, VectorDT, opath):
   """
    Learn a model on the ref data given in arg
    -Serie_T : Time series image
    -PathvectorDT : path to directory containing vector files containing the samples
    -opath : The output directory
   """


   args_classif = dicRF()
   ch = ""
   i = 0
   bm = 0

   newpath = opath+"/RF"
   if not os.path.exists(newpath):
      os.mkdir(newpath)
   

   for key in args_classif:
      ch = ch+"-"+key+" "+str(args_classif[key])+" "
   
   name = Serie_T[0:-4]
   name_stat = name+".xml"
   dataSeries = name+".tif"
   
   if not os.path.exists(dataSeries):
      print "Pas d'image en entree"
   elif os.path.exists(dataSeries):
      if not os.path.exists(name_stat):
         CL.ComputeImageStats(opath,dataSeries)

   vectorPath = VectorDT.split("/")
   vectorName = vectorPath[-1].split('_')
   seed = vectorName[2]

   Classif = "otbcli_TrainImagesClassifier -io.il "+dataSeries+" -io.vd "+VectorDT\
             +" -io.imstat "+name_stat+" -sample.bm "+str(bm)+" -io.confmatout "+newpath+"/RF_ConfMat_"+seed\
             +"_bm"+str(bm)+".csv -io.out "+newpath+"/RF_Classification_"+seed+"_bm"+str(bm)+".txt "+ch
   os.system(Classif)
   print Classif
   return newpath+"/RF_ConfMat_"+seed+"_bm"+str(bm)+".csv"
