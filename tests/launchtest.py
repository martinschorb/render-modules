#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jan  4 13:55:54 2021

@author: schorb
"""
import time
print('This is a test script for the launcher!')

for step in [5,10,20,30]:
    
    time.sleep(step)
    print(str(step)+' s have elapsed')

print('Script done and process finished...')
