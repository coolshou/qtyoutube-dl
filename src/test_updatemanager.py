#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Jun  2 11:01:30 2019

@author: coolshou
"""
import sys

try:
    from PyQt5.QtCore import (QCoreApplication)
except ImportError as error:
    print(error)
    sys.exit(1)

from updatemanager import UpdateThread
    

    
if __name__ == "__main__":
    #main
    app = QCoreApplication(sys.argv)
    #test it
    t = UpdateThread("bin")
    #why this did not happen to quit app?
    t.finished.connect(app.exec_())
    t.start()
    
    sys.exit(app.exec_())
