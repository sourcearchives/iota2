#!/usr/bin/python
#-*- coding: utf-8 -*-

import subprocess
import sys
import argparse
import vector_functions as vf
import checkvoisins

# génération de jobs avec erreurs

def generateurVoisins(pathjob, time, outpath, log, launch, listile=[]):

    listile = checkvoisins.findWalltime(log)
    
    basepath = pathjob
    for indjob in listile:
        basepath += str(indjob) + '.pbs'
        jobFile = open(basepath,"w")

        jobFile.write( "#!/bin/bash\n\
#PBS -N voisinage%s\n\
#PBS -l select=1:ncpus=20:mem=100000mb:generation=g2016\n\
#PBS -l walltime=%s:00:00\n\
#PBS -q qoper\n\
#PBS -o %s\n\
#PBS -e %s\n\
\n\
module load python/2.7.12\n\
\n\
source /work/OT/theia/oso/OTB/otb_superbuild/otb_superbuild-5.10.1-Release-install/config_otb.sh\n\
export PYTHONPATH=${PYTHONPATH}:/home/qt/thierionv/chaineIOTA/scripts/common/\n\
\n\
PYPATH=/home/qt/thierionv/simplification/post-processing-oso/script_oso/\n\
cd $PYPATH\n\
\n\
cp /work/OT/theia/oso/classifications/Simplification/FranceEntiere/otb/5101/double/classif_clump_regularisee.tif $TMPDIR\n\
cp /work/OT/theia/oso/classifications/Simplification/FranceEntiere/otb/5101/double/grille.* $TMPDIR\n\
\n\
python job_tif_v3.py -wd $TMPDIR -in $TMPDIR/classif_clump_regularisee.tif -nbcore 20 -strippe 2 -grid $TMPDIR/grille.shp -ngrid %s -out /work/OT/theia/oso/classifications/Simplification/FranceEntiere/otb/voisins/ -tmp -cluster\n\
\n\
rm $TMPDIR/classif_clump_regularisee.tif $TMPDIR/grille.* $TMPDIR/tile_%s.tif\n\
\n"%(indjob, time, basepath[:-4] + 'v2_output.log', basepath[:-4] + 'v2_error.log', indjob, indjob))
        
        jobFile.close()

        if launch:        
            subprocess.check_output('qsub %s'%(basepath), shell=True)

        basepath = pathjob

        
def generateurVectorisation(pathjob, time, outpath, launch, listile=[]):
    
    if listile is None:
        listtileSimp = checkvoisins.findSimplifTile(outpath)
        listtileVois = checkvoisins.findSuccess(outpath)

        listile = [x for x in listtileVois[0] if x not in listtileSimp]

    basepath = pathjob
    for indjob in listile:
        basepath += str(indjob) + '.pbs'
        jobFile = open(basepath,"w")
        
        jobFile.write( "#!/bin/bash\n\
#PBS -N simplif%s\n\
#PBS -l select=1:ncpus=1:mem=20000mb:generation=g2016\n\
#PBS -l walltime=%s:00:00\n\
#PBS -q qoper\n\
#PBS -o %s\n\
#PBS -e %s\n\
\n\
module load python/2.7.12\n\
\n\
source /work/OT/theia/oso/OTB/otb_superbuild/otb_superbuild-5.10.1-Release-install/config_otb.sh\n\
PYPATH=/home/qt/thierionv/simplification/post-processing-oso/script_oso/\n\
cd $PYPATH\n\
\n\
cp /work/OT/theia/oso/classifications/Simplification/FranceEntiere/otb/voisins/%s/outfiles/tile_%s.tif $TMPDIR\n\
\n\
python job_simplification.py -wd $TMPDIR -grass /work/OT/theia/oso/OTB/GRASS/grass7.2.1svn-x86_64-pc-linux-gnu-13_03_2017 -in $TMPDIR/tile_%s.tif -ngrid %s -out /work/OT/theia/oso/classifications/Simplification/FranceEntiere/otb/voisins/ -douglas 10 -hermite 10 -angle True -resample False -tmp -cluster\n\
\n\
rm $TMPDIR/tile_%s.tif\n\
\n"%(indjob, time, basepath[:-4] + '_output.log', basepath[:-4] + '_error.log', indjob, indjob, indjob, indjob, indjob))
        jobFile.close()

        if launch:
            subprocess.check_output('qsub %s'%(basepath), shell=True)        

        basepath = pathjob
        
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
        
        parser.add_argument("-tile", '--list', nargs='+', dest="tile", type=int, \
                            help="Tile number(s) (optional : can be calulated if omited)" )        
        parser.add_argument("-jobpath", dest="jobpath", action="store", \
                            help="generic job name and path", required = True)
        parser.add_argument("-out", dest="outpath", action="store", \
                            help="job outpath", required = True)
        parser.add_argument("-log", dest="log", action="store", \
                            help="generic log file", required = True)        
        parser.add_argument("-time", dest="time", action="store", \
                            help="job walltime", required = True)        
        parser.add_argument("-type", dest="jobtype", action="store", \
                            help="job type ? vecteur or voisin", required = True)
        parser.add_argument("-launch", action="store_true", \
                            help="Launch generated jobs", default = False)        
           
        args = parser.parse_args()

        if args.jobtype == 'voisin':
            generateurVoisins(args.jobpath, args.time, args.outpath, args.log, args.launch, args.tile)
        elif args.jobtype == 'vecteur':
            generateurVectorisation(args.jobpath, args.time, args.outpath, args.launch, args.tile)
        else:
            print 'Type {} does not exist'.format(args.jobtype)
            sys.exit()

