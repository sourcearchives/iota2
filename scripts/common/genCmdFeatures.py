#!/usr/bin/python
#-*- coding: utf-8 -*-

import argparse,os

def getDateLandsat(pathLandsat,tiles,sensor="Landsat8"):
	"""
	"""
	dateMin = 30000000000
	dateMax = 0 #JC
	for tile in tiles:
		fold = os.listdir(pathLandsat+"/"+sensor+"_"+tile)
   		for i in range(len(fold)):
			if fold[i].count(".tgz")==0 and fold[i].count(".jpg")==0 and fold[i].count(".xml")==0:
				contenu = os.listdir(pathLandsat+"/"+sensor+"_"+tile+"/"+fold[i])
				for i in range(len(contenu)):
					if contenu[i].count(".TIF")!=0:
						Date = int(contenu[i].split("_")[3])
						if Date > dateMax:
							dateMax = Date
						if Date < dateMin:
							dateMin = Date
	return str(dateMin),str(dateMax)

def getDateL5(pathL5,tiles):
    return getDateLandsat(pathL5, tiles, "Landsat5")

def getDateL8(pathL8,tiles):
    return getDateLandsat(pathL8, tiles, "Landsat8")

def CmdFeatures(testPath,tiles,appliPath,pathL8,pathL5,pathConfig,pathout,pathWd):
	
	print "PATHL5 "+pathL5
	if pathL5 != "None":
		begDateL5,endDateL5 = getDateL5(pathL5,tiles)#recupere le min de ttes les dates et le max de ttes les dates
	else : 
		begDateL5 = "None"
		endDateL5 = "None"

	if pathL8 != "None":
		begDateL8,endDateL8 = getDateL8(pathL8,tiles)#recupere le min de ttes les dates et le max de ttes les dates
	else : 
		begDateL8 = "None"
		endDateL8 = "None"

	gap = "16"
	wr = "30"

	Allcmd=[]
	for i in range(len(tiles)):
		if not os.path.exists(pathout+"/"+tiles[i]):
				os.system("mkdir "+pathout+"/"+tiles[i])
		if pathWd == None:
			Allcmd.append("python "+appliPath+"/New_ProcessingChain.py -cf "+pathConfig+" -iL8 "+pathL8+"/Landsat8_"+tiles[i]+" -iL5 "+pathL5+"/Landsat5_"+tiles[i]+" -w "+pathout+"/"+tiles[i]+" --db_L5 "+begDateL5+" --de_L5 "+endDateL5+" --db_L8 "+begDateL8+" --de_L8 "+endDateL8+" -g "+gap+" -wr "+wr)
		else :
                  	Allcmd.append("python "+appliPath+"/processingFeat_hpc.py -cf "+pathConfig+" -iL8 "+pathL8+"/Landsat8_"+tiles[i]+" -iL5 "+pathL5+"/Landsat5_"+tiles[i]+" -w $TMPDIR --db_L8 "+begDateL8+" --de_L8 "+endDateL8+" --db_L5 "+begDateL5+" --de_L5 "+endDateL5+" -g "+gap+" -wr "+wr+" --wo "+pathout+"/"+tiles[i]+" > $LOGPATH/"+tiles[i]+"_feat.txt")
	#écriture du fichier de cmd
	cmdFile = open(testPath+"/cmd/features/features.txt","w")
	for i in range(len(Allcmd)):
		if i == 0:
			cmdFile.write("%s"%(Allcmd[i]))
		else:
			cmdFile.write("\n%s"%(Allcmd[i]))
	cmdFile.close()
	return Allcmd

if __name__ == "__main__":

	parser = argparse.ArgumentParser(description = "This function allow you to create all classification command")
	parser.add_argument("-path.test",help ="path to the folder which contains the test(mandatory)",dest = "testPath",required=True)
	parser.add_argument("-tiles",dest = "tiles",help ="All the tilesr required (mandatory)", nargs='+',required=True)
	parser.add_argument("-path.application",help ="path to python's applications (mandatory)",dest = "appliPath",required=True)
	parser.add_argument("--path.L8",help ="path to the Landsat_8's images",dest = "pathL8",default = None,required=False)
	parser.add_argument("--path.L5",help ="path to the Landsat_8's images",dest = "pathL5",default = None,required=False)
	parser.add_argument("-path.config",help ="path to the configuration file(mandatory)",dest = "pathConfig",required=True)
	parser.add_argument("-path.out",help ="path out(mandatory)",dest = "pathout",required=True)
	parser.add_argument("--wd",dest = "pathWd",help ="path to the working directory",default=None,required=False)
	args = parser.parse_args()

	CmdFeatures(args.testPath,args.tiles,args.appliPath,args.pathL8,args.pathL5,args.pathConfig,args.pathout,args.pathWd)





























































