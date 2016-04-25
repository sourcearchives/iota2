# =========================================================================
#   Program:   iota2
#
#   Copyright (c) CESBIO. All rights reserved.
#
#   See LICENSE for details.
#
#   This software is distributed WITHOUT ANY WARRANTY; without even
#   the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR
#   PURPOSE.  See the above copyright notices for more information.
#
# =========================================================================

import datetime


def CreateFichierDatesReg(debut,fin,gap,opath,sensorName):
    """
    debut : liste [year,month,day]
    end : idem
    gap : time between two images in days
    """
    date_init = datetime.date(int(debut[0:4]),int(debut[4:6]),int(debut[6:8]))
    date_end = datetime.date(int(fin[0:4]),int(fin[4:6]),int(fin[6:8]))
    date_end_1 = datetime.date(int(fin[0:4]),int(fin[4:6]),int(fin[6:8])-1)
    fich = open(opath+"/DatesInterpReg"+sensorName+".txt","w")
    gap = int(gap)
    ndate = date_init.isoformat()
    ndate = ndate.split("-")
    ndate = ndate[0]+ndate[1]+ndate[2]

    fich.write(ndate+"\n")

    date = date_init+datetime.timedelta(days=gap)
    #print date.isoformat()
    date = date_init
    while(date+datetime.timedelta(days=gap) < date_end_1):
        new_date = date+datetime.timedelta(days=gap)

        ndate = new_date.isoformat()
        ndate = ndate.split("-")
        ndate = ndate[0]+ndate[1]+ndate[2]
        date = new_date
        fich.write(ndate+"\n")

    ndate = date_end.isoformat()
    ndate = ndate.split("-")
    ndate = ndate[0]+ndate[1]+ndate[2]
    fich.write(ndate)
    fich.close()
    return opath+"/DatesInterpReg"+sensorName+".txt"
