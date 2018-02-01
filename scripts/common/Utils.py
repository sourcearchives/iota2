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

import os, datetime, subprocess, sys
#import logging
from timeit import default_timer as timer

def run(cmd, desc=None, env=os.environ):

    # Get logger
    #logger = logging.getLogger(__name__)

    # Log description of step if available
    #if desc is not None:
    #    logger.info(desc)
        
    # Log cmd in debug
    #logger.debug(cmd)

    # Create subprocess
    start = timer()
    p = subprocess.Popen(cmd,env=env,shell=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)

    # Get output as strings
    out,err = p.communicate()

    # Get return code
    rc = p.returncode

    stop = timer()

    # Log outputs
    #logger.debug("out/err: {}".format(out))

    #logger.debug("Done in {} seconds".format(stop-start))

    # Log error code
    #if rc != 0:
    #    logger.error("Command {}  exited with non-zero return code {}".format(cmd,rc))
    
    
class Opath(object):

    def __init__(self,opath,create = True):
        """
        Take the output path from main argument line and define and create the output folders
        """
	
	self.opath = opath
	self.opathT = opath+"/tmp"
	self.opathF = opath+"/Final"
	if create:
		if not os.path.exists(self.opath):
		    os.mkdir(self.opath)

		if not os.path.exists(self.opathT):
		    os.mkdir(self.opathT)

		if not os.path.exists(self.opathT+"/REFL"):
		    os.mkdir(self.opathT+"/REFL")

		if not os.path.exists(self.opathF):
		    os.mkdir(self.opathF)
