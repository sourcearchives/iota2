import cPickle as CP

class Log(object):

    def __init__(self):
        
        self.dicoStep = {}
        self.ipathF = None
        self.ipathL8 = None
        self.ipathS4 = None
        self.shapeF = None
        self.opath = None
        self.debutDate = None
        self.debutEnd = None
        self.gap = None
        self.work_res = None
        self.numForceStep = None
        self.init_dico(self)        

    def initNewLog(self,parser):

        self.ipathF = parser.ipathF
        self.ipathL8 = parser.ipathL8
        self.ipathS4 = parser.ipathS4
        self.shapeF = parser.shapeF
        self.opath = parser.opath
        self.debutDate = parser.dateB
        self.debutEnd = parser.dateE
        self.gap = parser.gap
        self.work_res = parser.work_res

        if not (parser.forceStep == None):
            numStep = int(parser.forceStep)
            self.numForceStep = numStep

    def update(self,step,status):
        self.dico[step] = status

    def init_dico(self):

        #Border Mask
        self.step1 = False
        #Masque emprise commune
        self.step2 = False
        #Reech Donnees
        self.step3 = False
        #Reech Mask
        self.step4 = False
        #Cree Serie Tempo Mask
        self.step5 = False
        #Cree Serie Tempo Refl
        self.step6 = False
        #Cree Gapfilling
        self.step7 = False
        #Feat Extract
        self.step8 = False
        #Concat Feat
        self.step9 = False
        #Order GapF
        self.step10 = False
        #Serie Classif
        self.step11 = False
        #Preparation DT
        self.step12 = False
        #Classif
        self.step13 = False
        
def sauv_log(objLog,opath):
    CP.dump(objLog,open(opath+"/log_tmp","wb"))

def load_log(nom_fich_log,opath):
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

    if not (log1.shapeF == log2.shapeF):
        print 
