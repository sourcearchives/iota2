#!/usr/bin/python
#-*- coding: utf-8 -*-

# =========================================================================
#   Program:   iota2
#
#   Copyright (c) CESBIO. All rights reserved.
#
#   See LICENSE for details.
#
#   This software is distributed WITHOUT ANY WARRANTY; without even
#   the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR
#   PURPOSE.  See the above copyright notices for more information.
#
# =========================================================================

"""
Make OSO map regularization (10 m regularization, 10 m to 20 m resampling, 20 m regularization, inland and sea water differentiation)
"""

import sys, os, argparse
import shutil
import time
import logging
logger = logging.getLogger(__name__)
import numpy as np
import AdaptRegul

try:
    from Common import Utils
    from Common import OtbAppBank
except ImportError:
    raise ImportError('Iota2 not well configured / installed')

#------------------------------------------------------------------------------

def rastToVectRecode(path, classif, vector, outputName, ram = "10000", dtype = "uint8", valvect = 255, valrastout = 255):

    """
    Convert vector in raster file and change background value 

    Parameters
    ----------
    path : string
        working directory
    classif : string
        path to landcover classification
    vector : string
        vector file to rasterize
    outputName : string
        output filename and path
    ram : string
        ram for OTB applications
    dtype : string
        pixel type of the output raster
    valvect : integer
        value of vector to search
    valrastout : integer
        value to use to recode
    """

    # Empty raster
    bmapp = OtbAppBank.CreateBandMathApplication({"il": classif,
                                                "exp": "im1b1*0",
                                                "ram": str(0.2 * float(ram)),
                                                "pixType": dtype,
                                                "out": os.path.join(path, 'temp.tif')})
    bmapp.ExecuteAndWriteOutput()

    # Burn
    tifMasqueMerRecode = os.path.join(path, 'masque_mer_recode.tif')
    rastApp = OtbAppBank.CreateRasterizationApplication({"in" : vector,
                                                       "im" : os.path.join(path, 'temp.tif'),
                                                       "background": 1,
                                                       "out": tifMasqueMerRecode})

    rastApp.ExecuteAndWriteOutput()

    # Differenciate inland water and sea water
    bandMathAppli = OtbAppBank.CreateBandMathApplication({"il": [classif, tifMasqueMerRecode],
                                                          "exp": "(im2b1=={})?im1b1:{}".format(valvect, valrastout),
                                                          "ram": str(0.2 * float(ram)),
                                                          "pixType": dtype,
                                                          "out": outputName})
    bandMathAppli.ExecuteAndWriteOutput()
    os.remove(tifMasqueMerRecode)


def OSORegularization(classif, umc1, core, path, output, ram = "10000", noSeaVector = None, rssize = None, umc2 = None, logger = logger):

    # OTB Number of threads
    os.environ["ITK_GLOBAL_DEFAULT_NUMBER_OF_THREADS"] = str(core)

    # first regularization
    regulClassif, time_regul1 = AdaptRegul.regularisation(classif, umc1, core, path, ram)

    logger.info(" ".join([" : ".join(["First regularization", str(time_regul1)]), "seconds"]))

    # second regularization
    if umc2 != None :
        if rssize != None :
            if os.path.exists(os.path.join(path, "reechantillonnee.tif")):
                os.remove(os.path.join(path, "reechantillonnee.tif"))
                
            command = "gdalwarp -q -multi -wo NUM_THREADS=%s -r mode -tr %s %s %s %s/reechantillonnee.tif" %(core, \
                                                                                                          rssize, \
                                                                                                          rssize, \
                                                                                                          regulClassif, \
                                                                                                          path)
            Utils.run(command)
            logger.info(" ".join([" : ".join(["Resample", str(time.time() - time_regul1)]), "seconds"]))

        regulClassif, time_regul2 = AdaptRegul.regularisation(os.path.join(path, "reechantillonnee.tif"), umc2, core, path, ram)
        os.remove(os.path.join(path, "reechantillonnee.tif"))
        logger.info(" ".join([" : ".join(["Second regularization", str(time_regul2)]), "seconds"]))

    if noSeaVector is not None:
        outfilename = os.path.basename(output)
        rastToVectRecode(path, regulClassif, noSeaVector, os.path.join(path, outfilename), ram, "uint8")
    else:
        outfilename = regulClassif

    shutil.copyfile(os.path.join(path, outfilename), output)
    os.remove(os.path.join(path, outfilename))

if __name__ == "__main__":
    if len(sys.argv) == 1:
	prog = os.path.basename(sys.argv[0])
	print '      '+sys.argv[0]+' [options]'
	print "     Help : ", prog, " --help"
	print "        or : ", prog, " -h"
	sys.exit(-1)

    else:
	usage = "usage: %prog [options] "
	parser = argparse.ArgumentParser(description = "Regularization and resampling a classification raster")
        parser.add_argument("-wd", dest="path", action="store", \
                            help="Working directory", required = True)

        parser.add_argument("-in", dest="classif", action="store", \
                            help="Name of classification", required = True)

        parser.add_argument("-inland", dest="inland", action="store", \
                            help="inland water limit shapefile", required = False)

        parser.add_argument("-nbcore", dest="core", action="store", \
                            help="Number of CPU / Threads to use for OTB applications (ITK_GLOBAL_DEFAULT_NUMBER_OF_THREADS)", \
                            required = True)

        parser.add_argument("-ram", dest="ram", action="store", \
                            help="RAM for otb applications", default = "10000", required = False)

        parser.add_argument("-umc1", dest="umc1", action="store", \
                            help="MMU for first regularization", required = True)

        parser.add_argument("-umc2", dest="umc2", action="store", \
                            help="MMU for second regularization", required = False)

        parser.add_argument("-rssize", dest="rssize", action="store", \
                            help="Pixel size for resampling", required = False)

        parser.add_argument("-outfile", dest="out", action="store", \
                            help="output file name", required = True)

        args = parser.parse_args()

        OSORegularization(args.classif, args.umc1, args.core, args.path, args.out, args.ram, args.inland, args.rssize, args.umc2)

        # python regularization.py -wd /home/thierionv/cluster/simplification/post-processing-oso/script_oso/wd -in /home/thierionv/cluster/simplification/post-processing-oso/script_oso/OSO_10m.tif -inland /home/thierionv/work_cluster/classifications/Simplification/masque_mer.shp -nbcore 4 -umc1 10 -umc2 3 - rssize 20 -outfile /home/thierionv/cluster/simplification/post-processing-oso/script_oso/out/classif_regul_20m.tif
