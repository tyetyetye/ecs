#!/usr/bin/env python3
import json

class Config:
    def __init__(self):
        self.config_dir = '/opt/ecs/config'

    def read_config(self, file):
        path = self.config_dir + '/' + file
        with open(path, 'r') as config_json:
            data = config_json.read()
        return json.loads(data)

    def database(self):
        return self.read_config('db.json')

    def sensor(self):
        return self.read_config('sensor.json')

    def plot(self):
        return self.read_config('graph.json')
