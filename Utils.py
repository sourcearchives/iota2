

import os

class Opath(object):

    def __init__(self,opath):
        """
        Take the output path from main argument line and define and create the output folders
        """

        self.opath = opath
        self.opathT = opath+"/tmp"
        self.opathF = opath+"/Final"
        self.opathCL = opath+"/Final/Images"
        self.opathIS = opath+"/in-situ"

        if not os.path.exists(self.opath):
            os.mkdir(self.opath)

        if not os.path.exists(self.opathT):
            os.mkdir(self.opathT)

        if not os.path.exists(self.opathF):
            os.mkdir(self.opathF)

        if not os.path.exists(self.opathCL):
            os.mkdir(self.opathCL)

        if not os.path.exists(self.opathIS):
            os.mkdir(self.opathIS)

