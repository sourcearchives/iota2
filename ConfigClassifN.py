def dicRF():
   rf = {}
   rf['classifier'] = 'rf'
   rf['classifier.rf.min'] = 25
   rf['classifier.rf.max'] = 25
   #rf['classifier.rf.max'] = 10
   #rf['classifier.rf.max'] = 5
   rf['sample.mt'] = -1
   rf['sample.mv'] = 0
   #rf['sample.edg'] = 'false'
   rf['sample.vfn'] = 'CODE'
   rf['sample.vtr'] = 0.1
   #rf['rand'] = 2
   #rf['sample.bm'] = 0
   #rf['io.out'] = "./RF_Classification.txt"
   #rf['io.confmatout'] = "./RF_ConfMat.csv"
   return rf
 
def dicSVM():
   svm = {}
   svm['classifier'] = 'svm'
   svm['classifier.svm.k'] = 'rbf'
   svm['sample.mt'] = -1
   svm['sample.mv'] = 0
   svm['sample.edg'] = 'false'
   svm['sample.vfn'] = 'CODE'
   svm['sample.vtr'] = 0.1
   svm['classifier.svm.opt'] = 1
   svm['rand'] = 2
   #svm['sample.bm'] = 1
   #svm['io.out'] = "./SVM_Classification.txt"
   #svm['io.confmatout'] = "./SVM_ConfMat.csv"
   return svm

