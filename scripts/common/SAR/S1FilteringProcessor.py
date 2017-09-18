import ConfigParser
import otbAppli
import os,re
from sys import argv
import otbApplication as otb

def getOrtho(orthoList,pattern):
    """
    pattern example : "s1b(.*)ASC(.*)tif"
    """
    for ortho in orthoList:
        try:
            name = os.path.split(ortho.GetParameterValue("io.out"))[-1].split("?")[0]
        except:
            name = os.path.split(ortho.GetParameterValue("out"))[-1].split("?")[0]
        compiled = re.compile(pattern)
        ms = compiled.search(name)
        try :
            ms.group(1).strip()
            yield ortho
        except:
            continue

def getDatesInOtbOutputName(otbObj):
    
    if isinstance(otbObj,str):	
        return int(otbObj.split("/")[-1].split("_")[4].split("t")[0])
    elif type(otbObj)==otb.Application:
        outputParameter = otbAppli.getInputParameterOutput(otbObj)
        return int(otbObj.GetParameterValue(outputParameter).split("/")[-1].split("_")[4].split("t")[0])
    
def main(ortho=None,configFile="./S1Processor.cfg"):
    
    import ast
    print "Filtering"
    config = ConfigParser.ConfigParser()
    config.read(configFile)
    wMode = ast.literal_eval(config.get('Processing','writeTemporaryFiles'))
    stackFlag = ast.literal_eval(config.get('Processing','outputStack'))
    stdoutfile=None
    stderrfile=open("S1ProcessorErr.log",'a')
    RAMPerProcess=int(config.get('Processing','RAMPerProcess'))
    if "logging" in config.get('Processing','Mode').lower():
        stdoutfile=open("S1ProcessorOut.log",'a')
        stderrfile=open("S1ProcessorErr.log",'a')
    if "debug" in config.get('Processing','Mode').lower():
        stdoutfile=None
        stderrfile=None
    outputPreProcess = config.get('Paths','Output')
    wr = config.get('Filtering','Window_radius')

    reset_outcore = config.get('Filtering','Reset_outcore')
    stdoutfile=None

    directories=os.walk(outputPreProcess).next()
    SARFilter = []
    for d in directories[1]:
        s1aDESlist = sorted([currentOrtho for currentOrtho in getOrtho(ortho,"s1a(.*)"+d+"(.*)DES(.*)tif")],key=getDatesInOtbOutputName)
        if s1aDESlist:
            outs1aDES = os.path.join(directories[0],d,"outcore_S1aDES.tif")
            s1aDESlist_out = s1aDESlist
            if wMode or not stackFlag: 
                s1aDESlist_out = sorted([currentOrtho.GetParameterValue(otbAppli.getInputParameterOutput(currentOrtho)) for currentOrtho in getOrtho(ortho,"s1a(.*)"+d+"(.*)DES(.*)tif")],key=getDatesInOtbOutputName)
            s1aDES = otbAppli.CreateMultitempFilteringOutcore(s1aDESlist_out,outs1aDES,\
                                                        str(wr),ram=str(RAMPerProcess),\
                                                        pixType="float")
            if wMode or not stackFlag : s1aDES.ExecuteAndWriteOutput()
            else : s1aDES.Execute()
            
                                                        
        s1aASClist = sorted([currentOrtho for currentOrtho in getOrtho(ortho,"s1a(.*)"+d+"(.*)ASC(.*)tif")],key=getDatesInOtbOutputName)
        if s1aASClist:
            s1aASClist_out = s1aASClist
            if wMode or not stackFlag: 
                s1aASClist_out = sorted([currentOrtho.GetParameterValue(otbAppli.getInputParameterOutput(currentOrtho)) for currentOrtho in getOrtho(ortho,"s1a(.*)"+d+"(.*)ASC(.*)tif")],key=getDatesInOtbOutputName)
            outs1aASC = os.path.join(directories[0],d,"outcore_S1aASC.tif")
            s1aASC = otbAppli.CreateMultitempFilteringOutcore(s1aASClist_out,outs1aASC,\
                                                        str(wr),ram=str(RAMPerProcess),\
                                                        pixType="float")
            if wMode or not stackFlag : s1aASC.ExecuteAndWriteOutput()                                            
            else : s1aASC.Execute()
                                           
        s1bDESlist = sorted([currentOrtho for currentOrtho in getOrtho(ortho,"s1b(.*)"+d+"(.*)DES(.*)tif")],key=getDatesInOtbOutputName)
        if s1bDESlist:
            s1bDESlist_out = s1bDESlist
            if wMode or not stackFlag: 
                s1bDESlist_out = sorted([currentOrtho.GetParameterValue(otbAppli.getInputParameterOutput(currentOrtho)) for currentOrtho in getOrtho(ortho,"s1b(.*)"+d+"(.*)DES(.*)tif")],key=getDatesInOtbOutputName)
            outs1bDES = os.path.join(directories[0],d,"outcore_S1bDES.tif")
            s1bDES = otbAppli.CreateMultitempFilteringOutcore(s1bDESlist,outs1bDES,\
                                                        str(wr),ram=str(RAMPerProcess),\
                                                        pixType="float")
            if wMode or not stackFlag : s1bDES.ExecuteAndWriteOutput()
            else : s1bDES.Execute()
            
        s1bASClist = sorted([currentOrtho for currentOrtho in getOrtho(ortho,"s1b(.*)"+d+"(.*)ASC(.*)tif")],key=getDatesInOtbOutputName)
        if s1bASClist:
            s1bASClist_out = s1bASClist
            if wMode or not stackFlag: 
                s1bASClist = sorted([currentOrtho.GetParameterValue(otbAppli.getInputParameterOutput(currentOrtho)) for currentOrtho in getOrtho(ortho,"s1b(.*)"+d+"(.*)ASC(.*)tif")],key=getDatesInOtbOutputName)
            outs1bASC = os.path.join(directories[0],d,"outcore_S1bASC.tif")
            s1bASC = otbAppli.CreateMultitempFilteringOutcore(s1bASClist,outs1bASC,\
                                                        str(wr),ram=str(RAMPerProcess),\
                                                        pixType="float")
            if wMode or not stackFlag: s1bASC.ExecuteAndWriteOutput()       
            else : s1bASC.Execute()                                     

        try:
            os.makedirs(os.path.join(directories[0],d,"filtered"))
        except:
            pass
            
        s1aDESlist = sorted([currentOrtho for currentOrtho in getOrtho(ortho,"s1a(.*)"+d+"(.*)DES(.*)tif")],key=getDatesInOtbOutputName)
        if s1aDESlist:
            outs1aDES = os.path.join(directories[0],d,"outcore_S1aDES.tif")
            enl = os.path.join(directories[0],d,"filtered/enl_S1aDES.tif")
            stackFiltered = os.path.join(directories[0],d,"filtered/stack_s1aDES.tif")
            s1aDES_out = s1aDES
            s1aDESlist_out = s1aDESlist
            if wMode or not stackFlag:
                s1aDESlist_out = sorted([currentOrtho.GetParameterValue(otbAppli.getInputParameterOutput(currentOrtho)) for currentOrtho in getOrtho(ortho,"s1a(.*)"+d+"(.*)DES(.*)tif")],key=getDatesInOtbOutputName)
                s1aDES_out = s1aDES.GetParameterValue("oc")
            if not stackFlag : stackFiltered = None
            s1aDES_last,a,b = otbAppli.CreateMultitempFilteringFilter(s1aDESlist_out,s1aDES_out,\
                                                            str(wr),enl,ram=str(RAMPerProcess),\
                                                            pixType="float",\
                                                            outputStack=stackFiltered)
            SARFilter.append((s1aDES_last,s1aDES,a,b,s1aDESlist))
                                                        
        s1aASClist = sorted([currentOrtho for currentOrtho in getOrtho(ortho,"s1a(.*)"+d+"(.*)ASC(.*)tif")],key=getDatesInOtbOutputName)
        if s1aASClist:
            outs1aASC = os.path.join(directories[0],d,"outcore_S1aASC.tif")
            enl = os.path.join(directories[0],d,"filtered/enl_S1aASC.tif")
            stackFiltered = os.path.join(directories[0],d,"filtered/stack_s1aASC.tif")
            s1aASC_out = s1aASC
            s1aASClist_out = s1aASClist
            if wMode or not stackFlag:
                s1aASC_out = s1aASC.GetParameterValue("oc")
                s1aASClist_out = sorted([currentOrtho.GetParameterValue(otbAppli.getInputParameterOutput(currentOrtho)) for currentOrtho in getOrtho(ortho,"s1a(.*)"+d+"(.*)ASC(.*)tif")],key=getDatesInOtbOutputName)
            if not stackFlag : stackFiltered = None
            s1aASC_last,a,b = otbAppli.CreateMultitempFilteringFilter(s1aASClist_out,s1aASC_out,\
                                                            str(wr),enl,ram=str(RAMPerProcess),\
                                                            pixType="float",\
                                                            outputStack=stackFiltered)
            SARFilter.append((s1aASC_last,s1aASC,a,b,s1aASClist))
                                           
        s1bDESlist = sorted([currentOrtho for currentOrtho in getOrtho(ortho,"s1b(.*)"+d+"(.*)DES(.*)tif")],key=getDatesInOtbOutputName)
        if s1bDESlist:
            outs1bDES = os.path.join(directories[0],d,"outcore_S1bDES.tif")
            enl = os.path.join(directories[0],d,"filtered/enl_s1bDES.tif")
            stackFiltered = os.path.join(directories[0],d,"filtered/stack_s1bDES.tif")
            s1bDES_out = s1bDES
            s1bDESlist_out = s1bDESlist
            if wMode or not stackFlag:
                s1bDES_out = s1bDES.GetParameterValue("oc")
                s1bDESlist_out = sorted([currentOrtho.GetParameterValue(otbAppli.getInputParameterOutput(currentOrtho)) for currentOrtho in getOrtho(ortho,"s1b(.*)"+d+"(.*)DES(.*)tif")],key=getDatesInOtbOutputName)
            if not stackFlag : stackFiltered = None
            s1bDES_last,a,b = otbAppli.CreateMultitempFilteringFilter(s1bDESlist_out,s1bDES_out,\
                                                            str(wr),enl,ram=str(RAMPerProcess),\
                                                            pixType="float",\
                                                            outputStack=stackFiltered)
            SARFilter.append((s1bDES_last,s1bDES,a,b,s1bDESlist))
                                            
        s1bASClist = sorted([currentOrtho for currentOrtho in getOrtho(ortho,"s1b(.*)"+d+"(.*)ASC(.*)tif")],key=getDatesInOtbOutputName)
        if s1bASClist:
            outs1bASC = os.path.join(directories[0],d,"outcore_S1bASC.tif")
            enl = os.path.join(directories[0],d,"filtered/enl_S1bASC.tif")
            stackFiltered = os.path.join(directories[0],d,"filtered/stack_s1bASC.tif")
            s1bASClist_out=s1bASClist
            s1bASC_out=s1bASC
            if wMode or not stackFlag:
                s1bASClist_out = sorted([currentOrtho.GetParameterValue(otbAppli.getInputParameterOutput(currentOrtho)) for currentOrtho in getOrtho(ortho,"s1b(.*)"+d+"(.*)ASC(.*)tif")],key=getDatesInOtbOutputName)
                s1bASC_out = s1bASC.GetParameterValue("oc")
            if not stackFlag : stackFiltered = None
            s1bASC_last,a,b = otbAppli.CreateMultitempFilteringFilter(s1bASClist_out,s1bASC_out,\
                                                            str(wr),enl,ram=str(RAMPerProcess),\
                                                            pixType="float",\
                                                            outputStack=stackFiltered)
            SARFilter.append((s1bASC_last,s1bASC,a,b,s1bASClist))

    return SARFilter
if __name__=="__main__":
    main(argv[0])
	
