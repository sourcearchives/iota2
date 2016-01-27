# -*- coding: utf-8 -*-
import cPickle as CP
"""
Class log

Flag True : the step must be processed
Falg False : the step is skipped

"""
class Log(object):
    def __init__(self,opath):
        self.dico = {}
        self.opath = opath
        
    def update(self,step):
        self.dico[step] = False
        CP.dump(self,open(self.opath+"/log","wb"))
        return step + 1
        
    def checkStep(self):
        liste_clef = self.dico.keys()
        liste_clef.sort()
        #print liste_clef
        allTrue = False
        for clef in liste_clef:
            if not (self.numForceStep == None):
                if clef == self.numForceStep:
                    allTrue = True
            if not allTrue:
                if  self.dico[clef]:
                    allTrue = True
            else:
                self.dico[clef] = True
        CP.dump(self,open(self.opath+"/log","wb"))   

class LogClassif(Log):

    def __init__(self,opath):
        Log.__init__(self,opath)
        self.numForceStep = None
    def init_dico(self):
        # A changer si ajout d'étape
        liste_step = range(1,14)
        #print liste_step

        for step in liste_step:
            self.dico[step] = True
    
    def initNewLog(self,parser):

        if not (parser.forceStep == None):
            numStep = int(parser.forceStep)
            self.numForceStep = numStep

    def compareLogInstanceArgs(self,log_old):
        #A changer si ajout d'étape
        same = True
        if same:
            liste_clef = log_old.dico.keys()
            for clef in liste_clef:
                self.dico[clef] = log_old.dico[clef]        

class LogPreprocess(Log):

    def __init__(self,opath):
        Log.__init__(self,opath)
        self.opath = opath
        self.dico = {}
        self.ipathF = None
        self.ipathL8 = None
        self.ipathS4 = None
        #self.shapeF = None
        self.debutDate = None
        self.debutEnd = None
        self.gap = None
        self.work_res = None
        self.numForceStep = None
        self.init_dico()
        #print "attribut opath",self.opath

    def init_dico(self):
        # A changer si ajout d'étape
        liste_step = range(1,14)
        #print liste_step

        for step in liste_step:
            self.dico[step] = True

    def initNewLog(self,parser):

        self.ipathF = parser.ipathF
        self.ipathL8 = parser.ipathL8
        self.ipathS4 = parser.ipathS4
        #self.shapeF = parser.shapeF
        self.debutDate = parser.dateB
        self.debutEnd = parser.dateE
        self.gap = parser.gap
        self.work_res = parser.workRes

        if not (parser.forceStep == None):
            numStep = int(parser.forceStep)
            self.numForceStep = numStep

    def update_SeriePrim(self,nomPrim):
	self.nomPrim = nomPrim
	CP.dump(self,open(self.opath+"/log","wb"))
	
    def update_SerieRefl(self,nomRefl):
	self.nomRefl = nomRefl
	CP.dump(self,open(self.opath+"/log","wb"))
             
    def compareLogInstanceArgs(self,log_old):
        #A changer si ajout d'étape
        same = True
        if not ((log_old.work_res == self.work_res) or (log_old.ipathF == self.ipathF) or (log_old.ipathL8 == self.ipathL8) or (log_old.ipathS4 == self.ipathS4)):
            print "Not same resolution : Reprocessing all data"
            self.dico[1] = True
            same = False
        ## else if not (log_old.ipathF == log_new.ipathF):
        ##     print "Not same path for Formosat input images : Reprocessing all data"
        ##     log_new.dico[1] = False
        ## else if not (log_old.ipathL8 == log_new.ipathL8):
        ##     print "Not same path for Landsat input images : Reprocessing all data"
        ##     log_new.dico[1] = False
        ## else if not (log_old.ipathS4 == log_new.ipathS4):
        ##     print "Not same path for Spot input images : Reprocessing all data"
        ##     log_new.dico[1] = False

        # if not (log_old.shapeF == self.shapeF):
        #     print "Not same vector file : step 12 must be processed"
        #     self.dico[12] = False
        #     same = False

        if same:
            liste_clef = log_old.dico.keys()
            for clef in liste_clef:
                self.dico[clef] = log_old.dico[clef]

    def checkStep(self):
        liste_clef = self.dico.keys()
        liste_clef.sort()
        #print liste_clef
        allTrue = False
        for clef in liste_clef:
            if not (self.numForceStep == None):
                if clef == self.numForceStep:
                    allTrue = True
            if not allTrue:
                if  self.dico[clef]:
                    allTrue = True
            else:
                self.dico[clef] = True
        CP.dump(self,open(self.opath+"/log","wb"))

def load_log(nom_fich_log):
    objLog = CP.load(open(nom_fich_log,"r"))
    return objLog



