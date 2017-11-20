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
                try:
                    os.mkdir(self.opath)
                except OSError:
                    print self.opath + "allready exists"

            if not os.path.exists(self.opathT):
                try:
                    os.mkdir(self.opathT)
                except OSError:
                    print self.opathT + "allready exists"

            if not os.path.exists(self.opathT+"/REFL"):
                try:
                    os.mkdir(self.opathT+"/REFL")
                except OSError:
                    print self.opathT+"/REFL"+ "allready exists"

            if not os.path.exists(self.opathF):
                try:
                    os.mkdir(self.opathF)
                except OSError:
                    print self.opathF + "allready exists"
