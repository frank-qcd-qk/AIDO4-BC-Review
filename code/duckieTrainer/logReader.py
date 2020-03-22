from concurrent.futures import ThreadPoolExecutor

import os
import pickle
import numpy as np

class Reader:
    def __init__(self, log_file):
        self._log_file = open(log_file, 'rb')

    def read(self):
        end = False
        Observation=[]
        Linear=[]
        Angular=[]

        while not end:
            try:
                log = pickle.load(self._log_file)
                for entry in log:
                    step = entry['step']
                    Observation.append(step[0])
                    action = step[1]
                    Linear.append(action[0])
                    Angular.append(action[1])

            except EOFError:
                end = True

        return Observation,Linear,Angular

    def close(self):
        self._log_file.close()
