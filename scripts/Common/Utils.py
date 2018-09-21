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

import os
import datetime
import subprocess
import sys
import logging
from timeit import default_timer as timer

logger = logging.getLogger(__name__)

def run(cmd, desc=None, env=os.environ, logger=logger):

    # Create subprocess
    start = timer()
    logger.debug("run command : " + cmd)
    p = subprocess.Popen(cmd, env=env, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

    # Get output as strings
    out, err = p.communicate()

    # Get return code
    rc = p.returncode

    stop = timer()

    # Log outputs
    logger.debug("out/err: {}".format(out.rstrip()))
    logger.debug("Done in {} seconds".format(stop-start))


    # Log error code
    if rc != 0:
        logger.error("Command {}  exited with non-zero return code {}".format(cmd, rc))
        raise Exception("Launch command fail " + cmd + out)


class Opath(object):

    def __init__(self, opath, create=True, logger=logger):
        """
        Take the output path from main argument line and define and create the output folders
        """

        self.opath = opath
        self.opathT = opath+"/tmp"
        self.opathF = opath+"/Final"
        if create:
            if not os.path.exists(self.opath):
                try:
                    os.mkdir(self.opath)
                except OSError:
                    logger.debug(self.opath + "allready exists")

            if not os.path.exists(self.opathT):
                try:
                    os.mkdir(self.opathT)
                except OSError:
                    logger.debug(self.opathT + "allready exists")

            if not os.path.exists(self.opathT+"/REFL"):
                try:
                    os.mkdir(self.opathT+"/REFL")
                except OSError:
                    logger.debug(self.opathT+"/REFL"+ "allready exists")

            if not os.path.exists(self.opathF):
                try:
                    os.mkdir(self.opathF)
                except OSError:
                    logger.debug(self.opathF + "allready exists")
