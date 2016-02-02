import cPickle as CP

class Log(object):

    def __init__(self,opath):
        self.dico = {}
        self.opath = opath
        self.opath = opath
        self.dico = {}
        self.ipathF = None
        self.ipathL8 = None
        self.ipathS4 = None
        self.shapeF = None
        self.debutDate = None
        self.debutEnd = None
        self.gap = None
        self.work_res = None
        self.numForceStep = None
        self.init_dico()
    def initNewLog(self,parser):

        self.ipathF = parser.ipathF
        self.ipathL8 = parser.ipathL8
        self.ipathS4 = parser.ipathS4
        self.shapeF = parser.shapeF
        self.opath = parser.opath
        self.debutDate = parser.dateB
        self.debutEnd = parser.dateE
        self.gap = parser.gap
        self.work_res = parser.workRes

        if not (parser.forceStep == None):
            numStep = int(parser.forceStep)
            self.numForceStep = numStep

    def update(self,step):
        self.dico[step] = False
        CP.dump(self,open(self.opath+"/log","wb"))
        return step + 1
        
    def update_SeriePrim(self,nomPrim):
	self.nomPrim = nomPrim
	CP.dump(self,open(self.opath+"/log","wb"))
	
    def update_SerieRefl(self,nomRefl):
	self.nomRefl = nomRefl
	CP.dump(self,open(self.opath+"/log","wb"))
    
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

    def init_dico(self):
        # A changer si ajout d'etape
        liste_step = range(1,14)
        #print liste_step

        for step in liste_step:
            self.dico[step] = True
        
        

    def compareLogInstanceArgs(self,log_old):
        #A changer si ajout d'etape
        same = True
	#A decouper
        if not ((log_old.work_res == self.work_res)):
            print "Not same resolution : Reprocessing all data"
            self.dico[1] = True
            same = False

        if not (log_old.ipathF == self.ipathF):
            print "Not same Formosat path : Reprocessing all data"
            self.dico[1] = True
            same = False

        if not (log_old.ipathL8 == self.ipathL8):
            print "Not same resolution : Reprocessing all data"
            self.dico[1] = True
            same = False

        if not (log_old.ipathS4 == self.ipathS4):
            print "Not same resolution : Reprocessing all data"
            self.dico[1] = True
            same = False

            
        if not (log_old.shapeF == self.shapeF):
            print "Not same vector file : step 12 must be processed"
            self.dico[12] = False
            same = False

        if same:
            liste_clef = log_old.dico.keys()
            for clef in liste_clef:
                self.dico[clef] = log_old.dico[clef]

def sauv_log(objLog,opath):
    CP.dump(objLog,open(opath+"/log_tmp","wb"))

def load_log(nom_fich_log):
    objLog = CP.load(open(nom_fich_log,"r"))
    return objLog



def compareLogInstance(log1,log2):

    if not (log1.ipathF == log2.ipathF):
        print "Not same path for Formosat input images : Reprocessing all data"
    
    if not (log1.ipathL8 == log2.ipathL8):
        print "Not same path for Landsat input images : Reprocessing all data"

    if not (log1.ipathS4 == log2.ipathS4):
        print "Not same path for Spot input images : Reprocessing all data"

    if not (log1.work_res == log2.work_res):
        print "Not same resolution : Reprocessing all data"

