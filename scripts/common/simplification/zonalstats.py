#!/usr/bin/python
#-*- coding: utf-8 -*-
"""

"""

import sys
import os
import sqlite3 as lite
import argparse
import time
import math
 
class StdevFunc:
    def __init__(self):
        self.M = 0.0
        self.S = 0.0
        self.k = 1
 
    def step(self, value):
        if value is None:
            return
        tM = self.M
        self.M += (value - tM) / self.k
        self.S += (value - tM) * (value - self.M)
        self.k += 1
 
    def finalize(self):
        if self.k < 3:
            return None
        return math.sqrt(self.S / (self.k-2))

def test(dbsqlite):
    
    conn = lite.connect(dbsqlite)
    print 'la'
    conn.create_aggregate("stdev", 1, StdevFunc)
    print 'lala'
    cursor = conn.cursor()
    print 'lalala'
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    res = cursor.fetchall()
    res = [x[0] for x in res]
    print res
    if len(res) > 0:
        if 'stats' in res:
            cursor.execute("DROP TABLE stats;")
        if 'stats_back' in res:
            cursor.execute("DROP TABLE stats_back;")            
 
    cursor.execute('CREATE TABLE stats AS SELECT stats.originfid, stats.class, CAST(stats.value_0 AS INTEGER) AS originclass, '\
                   'ROUND(stats.mean_validity, 2) AS mean_validity, ROUND(stats.std_validity, 2) AS std_validity, '\
                   'ROUND(stats.mean_confidence, 2) AS mean_confidence, '\
                   'ROUND(CAST(stats.nb AS FLOAT) / totstats.tot, 2) AS rate '\
                   'from (select * , avg(value_1) AS mean_validity, count(value_2) AS nb, '\
                   'stdev(value_1) AS std_validity, avg(value_2) AS mean_confidence ' \
                   'FROM output '\
                   'GROUP BY originfid, value_0) stats '\
                   'INNER join '\
                   '(SELECT originfid, count(value_2) as tot FROM output GROUP BY originfid) totstats '\
                   'on stats.originfid = totstats.originfid limit 10')
    
    cursor.execute('select * from stats')    
    print cursor.fetchall()
 
    cursor.execute('select '\
                   'originfid, '\
                   'class, '\
                   'mean_validity, '\
                   'std_validity, '\
                   'mean_confidence, '\
                   'case when originclass = 11 THEN rate end as Ete, '\
                   'case when originclass = 12 THEN rate end as Hiver, '\
                   'case when originclass = 31 THEN rate end as Feuillus, '\
                   'case when originclass = 32 THEN rate end as Coniferes, '\
                   'case when originclass = 34 THEN rate end as Pelouse, '\
                   'case when originclass = 36 THEN rate end as Landes, '\
                   'case when originclass = 41 THEN rate end as UrbainDens, '\
                   'case when originclass = 42 THEN rate end as UrbainDiff, '\
                   'case when originclass = 43 THEN rate end as ZoneIndCom, '\
                   'case when originclass = 44 THEN rate end as Route, '\
                   'case when originclass = 45 THEN rate end as SurfMin, '\
                   'case when originclass = 46 THEN rate end as PlageDune, '\
                   'case when originclass = 51 THEN rate end as Eau, '\
                   'case when originclass = 53 THEN rate end as GlaceNeige, '\
                   'case when originclass = 211 THEN rate end as Prairie, '\
                   'case when originclass = 221 THEN rate end as Vergers, '\
                   'case when originclass = 222 THEN rate end as Vignes '\
                   'from stats order by originfid limit 10')
    
    print cursor.fetchall()
    
    
test('/home/vthierion/Documents/OSO/Dev/iota2/data/simplification/sample_extraction.sqlite')
