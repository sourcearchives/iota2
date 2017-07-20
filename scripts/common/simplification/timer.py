# -*- coding: utf-8 -*-
"""
Created on Fri Mar  3 11:51:16 2017

@author: donatien
"""

class Timer(object):
    """
    Classe pour mesurer le temps d'execution.
    """  
    def start(self):  
        if hasattr(self, 'interval'):  
            del self.interval  
        self.start_time = time.time()  
  
    def stop(self):  
        if hasattr(self, 'start_time'):  
            self.interval = time.time() - self.start_time  
            del self.start_time # Force timer reinit