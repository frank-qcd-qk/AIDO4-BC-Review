import pickle
import dill

import os
import pickle
import numpy as np
import cv2
import csv
from concurrent.futures import ThreadPoolExecutor

dill._dill._reverse_typemap['ObjectType'] = object
with open("training_data.log",'rb') as f:
    end = False
    observations = []
    actions = []        
    while not end:  
        try:
            loaded = pickle.load(f,encoding="latin1")
            for entry in loaded:
                step = entry['step']
                actions.append(step[1])
                observations.append(step[0])                
        except EOFError:
            end = True


print(len(actions))
print(len(observations))

class Logger:
    def __init__(self, log_file):
        self._log_file = open(log_file, 'wb')
        # we log the data in a multithreaded fashion
        self._multithreaded_recording = ThreadPoolExecutor(8)
        self.recording = []

    def log(self, observation, action):
        self.recording.append({
            'step': [
                observation,
                action,
            ]
        })

    def on_episode_done(self):
        print('Quick write!')
        self._multithreaded_recording.submit(self.commit)

    def commit(self):
        # we use pickle to store our data
        pickle.dump(self.recording, self._log_file)
        self._log_file.flush()
        del self.recording[:]
        self.recording.clear()

    def close(self):
        self._multithreaded_recording.shutdown()
        self._log_file.close()
        # make file read-only after finishing
        os.chmod(self._log_file.name, 0o444)


newLog = Logger(log_file='converted_from_pickle2.log')

for observation,action in zip(observations,actions):
    print(action)
    linear_speed = float(action[0].decode('utf-8'))*0.8
    angular_speed = float(action[1].decode('utf-8'))*3
    new_action = np.array([linear_speed,angular_speed])
    cv2.cvtColor(observation, cv2.COLOR_YUV2RGB)    
    cv2.imshow('Observation',observation)
    cv2.waitKey(10)
    newLog.log(observation,new_action)
    newLog.commit()

#newLog.close()
