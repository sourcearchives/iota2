import datetime


def CreateFichierDatesReg(debut,fin,gap,opath):
    """
    debut : liste [year,month,day]
    end : idem
    gap : time between two images in week
    """
    date_init = datetime.date(int(debut[0:4]),int(debut[4:6]),int(debut[6:8]))
    date_end = datetime.date(int(fin[0:4]),int(fin[4:6]),int(fin[6:8]))
    fich = open(opath+"/DatesInterpReg.txt","w")
    gap = int(gap)
    ndate = date_init.isoformat()
    ndate = ndate.split("-")
    ndate = ndate[0]+ndate[1]+ndate[2]

    fich.write(ndate+"\n")

    date = date_init+datetime.timedelta(weeks=gap)
    #print date.isoformat()
    date = date_init
    while(date+datetime.timedelta(weeks=gap) < date_end):
        new_date = date+datetime.timedelta(weeks=gap)

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
    return opath+"/DatesInterpReg.txt"
