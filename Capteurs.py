# -*- coding: utf-8 -*-


def class Sensor(object):
    def __init__(self):
        self.bands = {}
        self.name = None
        self.path = None
        
def class Spot4(Sensor):

    def __init__(self,path_image):
        self.name = 'Spot4'
        self.path = path_image
        self.bands["BANDS"] = {'green' : 1 , 'red' : 2, 'NIR' : 3, 'SWIR' : 4}

def class Landsat8(Sensor):

    def __init__(self,path_image):
        self.name = 'Landsat8'
        self.path = path_image
        self.bands["BANDS"] = { "aero" : 1 , "blue" : 2 , "green" : 3, "red" : 4, "NIR" : 5, "SWIR1" : 6 , "SWIR2" : 7}

def class Formosat(Sensor):

    def __init__(self,path_image):
        self.name = 'Formosat'
        self.path = path_image
        self.bands["BANDS"] = { "blue" : 1 , "green" : 2 , "red" : 3 , "NIR" : 4}
