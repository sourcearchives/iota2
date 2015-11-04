def dicRF():
   rf = {}
   rf['classifier'] = 'rf'
   rf['classifier.rf.min'] = 5
   rf['classifier.rf.max'] = 25
   #rf['classifier.rf.max'] = 10
   #rf['classifier.rf.max'] = 5
   rf['sample.mt'] = -1
   rf['sample.mv'] = 0
   #rf['sample.edg'] = 'false'
   rf['sample.vfn'] = 'CODE'
   rf['sample.vtr'] = 0.1
   rf['rand'] = 2
   #rf['sample.bm'] = 0
   #rf['io.out'] = "./RF_Classification.txt"
   #rf['io.confmatout'] = "./RF_ConfMat.csv"
   return rf
   
