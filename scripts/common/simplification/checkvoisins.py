#!/usr/bin/python
#-*- coding: utf-8 -*-

import subprocess
from operator import itemgetter
import time
import sys
import argparse

def findWalltime(logpath):
        # logpath='/home/qt/thierionv/simplification/voisins-simpli.e80410.'
        #command = 'grep -r ' + logpath + '.* -e "walltime"'
        command = 'grep -r ' + logpath + '*_error.log -e "walltime"'
        result_walltime = subprocess.check_output(command, shell=True)
        print result_walltime
        taberreur = []
        tabresult = result_walltime.rstrip().split('\n')
        for line in tabresult:
                interresfinal = line.split('.')[0].split('_')[0].split('/')
                resfinal = interresfinal[len(interresfinal)-1].replace('voisins','')
	        #interresult = line.split('.')[2]
	        #resfinal = interresult.split(':')[0]
                print resfinal
	        taberreur.append(int(resfinal))
                
        return taberreur

def findSuccess(outpath, listjobsinit=100):
        # outpath='/work/OT/theia/oso/classifications/Simplification/FranceEntiere/otb/voisins/'
        command = 'find ' + outpath + ' -name "tile_*.tif"'
        result_success = subprocess.check_output(command, shell=True)
        tabjobsuccess = []
        tabresultsuccess = result_success.rstrip().split('\n')
        for line in tabresultsuccess:
	        interresult = line.split('.')[0]
	        resfinalsuccess = interresult.split('_')[1]
	        try:
		        tabjobsuccess.append(int(resfinalsuccess))
		        listjobsinit.pop(jobs_init.index(int(resfinalsuccess)))
	        except:
		        pass		

        return tabjobsuccess, listjobsinit


#### A MODIFIER ####
def findEmptyTile(listjobsinit, logpath):
        # logpath='/home/qt/thierionv/simplification/voisins-simpli.e80410.'
        logpath = logpath.split('.')[0] + '.o' + logpath.split('.')[1][1:]        
        command = 'grep ' + logpath + '.* -e "Aucune entite dans la tuile"'        
        result_vide = subprocess.check_output(command, shell=True)
        tabjobvide = []
        tabresultvide = result_vide.rstrip().split('\n')
        for line in tabresultvide:
	        interresult = line.split('.')[2]
	        resfinalvide = interresult.split(':')[0]
	        try:
                        tabjobvide.append(int(resfinalvide))
		        listjobsinit.pop(jobs_init.index(int(resfinalvide)))
	        except:
		        pass
                
        return tabjobvide, listjobsinit


def checkStatsVoisins(outpath):
        status = {
                31: 'Finished',
                21: 'Neighbors extent calculation',
                13: 'Entities extent calculation'
        }
        # outpath='/work/OT/theia/oso/classifications/Simplification/FranceEntiere/otb/voisins/'
        command = 'find ' + outpath + ' -name log_prints_* | xargs wc -l'
        result_stats = subprocess.check_output(command, shell=True)

        stats = []
        tabresultstats = result_stats.rstrip().split('\n')
        for line in tabresultstats:
                try:
                        nbtile = line.lstrip().split(' ')[1].split('.')[0].split('_')[2]
                        statsresult = line.lstrip().split(' ')[0]                                
                        stats.append((int(nbtile), status[int(statsresult)]))
                except:
                        pass

        return stats

def findSimplifTile(outpath):
        # outpath='/work/OT/theia/oso/classifications/Simplification/FranceEntiere/otb/voisins/'
        command = 'find ' + outpath + ' -name "log_jobs_simplification*.csv"'
        result_simplif = subprocess.check_output(command, shell=True)
        simplif = []
        tabresultsimplifs = result_simplif.rstrip().split('\n')
        for line in tabresultsimplifs:
                try:
                        nbtile = line.split('.')[0].split('_')[3]
                        simplif.append(int(nbtile))
                except:
                        pass

        return simplif

def jobsStatus(log, outpath, jobArraysize):
        
        jobs_init = range(0, jobArraysize, 1)
        tabjobvide, listjobsinit = findEmptyTile(jobs_init, log)        
        taberreur = findWalltime(log)
        tabresteexcute = [x for x in listjobsinit if x not in taberreur]        
        tabjobsuccess, listjobsinit = findSuccess(outpath, jobs_init)
        simplif = findSimplifTile(outpath)
        stats = checkStatsVoisins(outpath)
        taberreurtps = [(x,y) for x,y in stats if x in taberreur]

        return tabjobvide, taberreur, tabresteexcute, tabjobsuccess, simplif, stats, taberreurtps

def jobsStatusFile(fileStat, tabjobvide, taberreur, tabresteexcute, tabjobsuccess, simplif, stats, taberreurtps):
        # "/work/OT/theia/oso/classifications/Simplification/FranceEntiere/otb/progression_cluster"
        prevjobsuccess = []
        prevjobnofinished = []
        prevjobrest = []
        prevsimplifsuccess = []
        with open(fileStat, "r") as fp:
                for i, line in enumerate(fp):
                        try:
                                if i == 1:
                                        prevdate = line
                                if i == 2:
                                        prevjobsuccess = [int(x) for x in line.split('[')[1].split(']')[0].split(',')]
                                if i == 4:
                                        prevjobnofinished =  [int(x) for x in line.split('[')[1].split(']')[0].split(',')]
                                if i == 6:
                                        prevjobrest =  [int(x) for x in line.split('[')[1].split(']')[0].split(',')]
                                if i == 8:
                                        prevsimplifsuccess = [int(x) for x in line.split('[')[1].split(']')[0].split(',')]
                        except:
                                pass


        jobFile = open(fileStat, "w")
        jobFile.write("%s\n\
Jobs voisins réussis\n\
%s\n\
Non terminés (temps dépassé)\n\
%s\n\
Reste à exécuter\n\
%s\n\
Jobs simplification réussis\n\
%s\n\
#### Progression depuis %s ####\n\
Nouveaux jobs voisins réussis\n\
%s\n\
Nouveaux Non terminés (temps dépassé)\n\
%s\n\
Nouveaux Jobs simplification réussis\n\
%s\n\
"%(time.strftime('%d/%m/%Y %H:%M:%S'), \
   sorted(tabjobsuccess), \
   taberreur, \
   tabresteexcute, \
   sorted(simplif), \
   prevdate, \
   [x for x in tabjobsuccess if x not in prevjobsuccess], \
   [x for x,y in taberreurtps if x not in prevjobnofinished], \
   [x for x in simplif if x not in prevsimplifsuccess]))
        

if __name__ == "__main__":
    if len(sys.argv) == 1:
	prog = os.path.basename(sys.argv[0])
	print '      '+sys.argv[0]+' [options]' 
	print "     Help : ", prog, " --help"
	print "        or : ", prog, " -h"
	sys.exit(-1)  

    else:
	usage = "usage: %prog [options] "
	parser = argparse.ArgumentParser(description = "Job generation for voisinage")
        parser.add_argument("-grille", dest="grille", action="store", \
                            help="grid shapefile file", required = True)
        parser.add_argument("-log", dest="log", action="store", \
                            help="generic log file", required = True)
        parser.add_argument("-out", dest="outpath", action="store", \
                            help="job outpath", required = True)        
        parser.add_argument("-ngrid", dest="ngrid", action="store", type = int, \
                            help="grid tile number", required = True)
        parser.add_argument("-logfile", dest="logfile", action="store", \
                            help="output logfile", required = True)
        
        args = parser.parse_args()

        tabjobvide, taberreur, tabresteexcute, \
                tabjobsuccess, simplif, stats, taberreurtps = jobsStatus(args.log, args.outpath, args.ngrid)

        jobsStatusFile(args.logfile, tabjobvide, taberreur, tabresteexcute, tabjobsuccess, simplif, stats, taberreurtps)
