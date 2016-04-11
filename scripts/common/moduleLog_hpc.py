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

class LogClassif(Log):

    def __init__(self,opath):
        Log.__init__(self,opath)
        self.numForceStep = None
    def init_dico(self):
        # A changer si ajout d'étape
        liste_step = range(1,6)
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
	self.ipathL5 = None
        self.ipathS4 = None
        #self.debutDate = None
        #self.debutEnd = None
        self.gap = None
        self.work_res = None
        self.numForceStep = None
        self.init_dico()

	self.seriePrim = None
	self.serieRefl = None
        #print "attribut opath",self.opath

    def init_dico(self):
        # A changer si ajout d'étape
        liste_step = range(1,6)
        #print liste_step

        for step in liste_step:
            self.dico[step] = True

    def initNewLog(self,parser):

        self.ipathF = parser.ipathF
        self.ipathL8 = parser.ipathL8
        self.ipathL5 = parser.ipathL5
        self.ipathS4 = parser.ipathS4
        #self.debutDate = parser.dateB
        #self.debutEnd = parser.dateE
        self.gap = parser.gap
        self.work_res = parser.workRes

        if not (parser.forceStep == None):
            numStep = int(parser.forceStep)
            self.numForceStep = numStep

    def update_SeriePrim(self,nomPrim):
	self.seriePrim = nomPrim
	CP.dump(self,open(self.opath+"/log","wb"))
	
    def update_SerieRefl(self,nomRefl):
	self.serieRefl = nomRefl
	CP.dump(self,open(self.opath+"/log","wb"))
             
    def compareLogInstanceArgs(self,log_old):
        #A changer si ajout d'étape
        same = True
        if not ((log_old.ipathL5 == self.ipathL5) or (log_old.work_res == self.work_res) or (log_old.ipathF == self.ipathF) or (log_old.ipathL8 == self.ipathL8) or (log_old.ipathS4 == self.ipathS4)):
            print "Not same resolution : Reprocessing all data"
            self.dico[1] = True
            same = False

        if same:
            liste_clef = log_old.dico.keys()
            for clef in liste_clef:
		
                self.dico[clef] = log_old.dico[clef]
    """
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
            
            self.dico[clef] = allTrue
        CP.dump(self,open(self.opath+"/log","wb"))
    """
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



