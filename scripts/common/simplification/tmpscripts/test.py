import os
import subprocess


command = "find ./dept_*/ -name stats.csv"
result_stats = subprocess.check_output(command, shell=True)
tabresult = result_size.rstrip().split('\n')
liststats = [int(x.split('_')[1].split['/'][0]) for x in tabresult]


cpt = [(r,len(files)) for r,d, files in os.walk('/work/OT/theia/oso/classifications/Simplification/FranceEntiere/otb/vecteurs/')]
cptsplits = [(a.split('_')[1].split('/')[0],b) for a,b in cpt if 'splits' in a]



command="grep -r --include 'shapeDept_error_*' reached /work/OT/theia/oso/classifications/Simplification/FranceEntiere/otb/vecteurs/"
result_size = subprocess.check_output(command, shell=True)
tabresult = result_size.rstrip().split('\n')
listinit = range(1, 96, 1)
listinit.remove(20)
listsize = list(set([int(x.split('_')[1].split('/')[0]) for x in tabresult]))
listshapesuccess = [x for x in listinit if x not in listsize]
