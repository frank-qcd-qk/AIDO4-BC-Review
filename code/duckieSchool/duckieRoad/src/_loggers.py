from concurrent.futures import ThreadPoolExecutor

import os
import pickle
import numpy as np

class Logger:
    def __init__(self, log_file):

        self._log_file = open(log_file, 'wb')
        # we log the data in a multithreaded fashion
        self._multithreaded_recording = ThreadPoolExecutor(4)
        self.recording = []

    def log(self, observation, action):
        self.recording.append({
            'step': [
                observation,
                action,
            ],
            'meta':[]
        })

    def on_episode_done(self):
        print('Quick write!')
        self._multithreaded_recording.submit(self._commit)

    def commit(self):
        # we use pickle to store our data
        pickle.dump(self.recording, self._log_file)
        self._log_file.flush()
        del self.recording[:]

    def close(self):
        self._multithreaded_recording.shutdown()
        self._log_file.close()
        os.chmod(self._log_file.name, 0o444)  # make file read-only after finishing