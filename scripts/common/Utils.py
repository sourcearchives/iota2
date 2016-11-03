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
