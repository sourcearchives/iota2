
import argparse
import moduleLog as ML
import sys,os
if len(sys.argv) == 1:
    prog = os.path.basename(sys.argv[0])
    print '      '+sys.argv[0]+' [options]'
    print "     Aide : ", prog, " --help"
    print "        ou : ", prog, " -h"

    sys.exit(-1)

else:

    usage = "Usage: %prog [options] "

    parser = argparse.ArgumentParser(description = "Preprocessing and classification for multispectral,multisensor and multitemporal data")

    parser.add_argument("-cf",dest="config",action="store",\
                        help="Config chaine", required = True)
    parser.add_argument("-iL", dest="ipathL8", action="store", \
                            help="Landsat Image path", default = None)

    parser.add_argument("-iS",dest="ipathS4",action="store",\
                            help="Spot Image path",default = None)

    parser.add_argument("-iF", dest="ipathF", action="store", \
                            help=" Formosat Image path",default = None)

    parser.add_argument("-vd", dest="shapeF", action="store", \
                            help="vector data for labelling", required = True)

    parser.add_argument("-w", dest="opath", action="store",\
                            help="Output path", required = True)

    parser.add_argument("-db", dest="dateB", action="store",\
                            help="Date for begin regular grid", required = True)
    
    parser.add_argument("-de", dest="dateE", action="store",\
                        help="Date for end regular grid",required = True)
    
    parser.add_argument("-g",dest="gap", action="store",\
                        help="Date gap between two images in week", required=True)

    parser.add_argument("-wr",dest="workRes", action="store",\
                        help="Working resolution", required=True)

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
## print arg,bool(arg)
## restart = bool(args.Restart)
## print restart
opath = args.opath

log = ML.Log(opath)
log.initNewLog(args)
if restart:
    nom_fich = opath+"/log"
    if  os.path.exists(nom_fich):
        log_old = ML.load_log(nom_fich)
        ML.compareLogInstanceArgs(log_old,log)        
    else:
        print "Not log file found at %s, all step will be processed"%opath

log.checkStep()


print log.dico
#Step 1
if log.dico[1]:
    print 1
    log.update(1)
    
#Step 2
if log.dico[2]:
    print 2
    log.update(2)
    
#Step 3
if log.dico[3]:
    print 3
    log.update(3)
    
#Step 4
if log.dico[4]:
    print 4
    log.update(4)
    
#Step 5
if log.dico[5]:
    print 5
    log.update(5)
    
## #Step 6
## print 6
## #Step 7
## print 7
## #Step 8
## print 8
## #Step 9
## print 9
## #Step 10
## print 10
## #Step 11
## print 11
## #Step 12
## print 12
## #Step 13
## print 13
#Tout est bien terminer
os.system("mv %s %s"%(opath+"/log_tmp",opath+"/log"))
