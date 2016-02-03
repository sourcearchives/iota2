
"""


python ProcessingClassifY.py -p /mnt/data/data1/Venus/ 


"""

import os, sys
import moduleLog as ML
import ClassificationN as CLN
import ClassificationY as CLY
import argparse

if len(sys.argv) == 1:
    prog = os.path.basename(sys.argv[0])
    print '      '+sys.argv[0]+' [options]'
    print "     Aide : ", prog, " --help"
    print "        ou : ", prog, " -h"

    sys.exit(-1)

else:

    usage = "Usage: %prog [options] "

    parser = argparse.ArgumentParser(description = "Preprocessing and classification for multispectral,multisensor and multitemporal data")

    parser.add_argument("-p",dest="path",action="store",\
                        help="Global Path containing the Preprocessing chain tree", required = True)

    parser.add_argument("-fs",dest="forceStep", action="store",\
                        help="Force step", default = None)

    parser.add_argument("-r",dest="Restart",action="store",\
                        help="Restart from previous valid status if parameters are the same",choices =('True','False'),default = 'True')

    args = parser.parse_args()
    


arg = args.Restart
if arg == "False":
    restart = False
else:
    restart = True


opath = args.path

path_model = opath+"/Model_Classic/"
if not os.path.exists(path_model):
    os.mkdir(path_model)

#Init du log

log = ML.LogClassif(path_model)
#print "opath_log",log.opath
log.initNewLog(args)
if restart:
    nom_fich = path_model+"/log"
    #print "nomfich",nom_fich
    if  os.path.exists(nom_fich):
        log_old = ML.load_log(nom_fich)
        log.compareLogInstanceArgs(log_old)        
    else:
        print "Not log file found at %s, all step will be processed"%path_model

log.checkStep()


#Step 1 : Lister les annees disponibles
Step = 1
liste_annee = os.listdir(opath+"/DONNEES/")
Step = log.update(Step)

#Step 2 : Classer chaque annee avec la VT correspondante mode "Classic"
for annee in liste_annee:
    path_annee = opath+"/DONNEES/"+annee
    #Tester la serie temporelle
    SerieT = path_annee+"/Final/SL_MultiTempGapF_NDVI_Brightness__.tif"
    path_model_years = path_model+"/"+annee
    if not os.path.exists(path_model_years):
        os.mkdir(path_model_years)
        
    #Lister les verites terrain pour apprentissage
    path_DT = path_annee+"/in-situ/"
    print path_DT
    learnsamples = CLN.getListLearnsamples(path_DT)
    #Apprentissage pour chaque jeu de donnees
    print learnsamples
    for sample in learnsamples:
        CLY.learnModel(SerieT,sample,path_model_years)

    


#valsamples = CL.getListValsamples(PathVectorDT)
