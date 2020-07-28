#!/usr/bin/env python3

import pandas as pd
import matplotlib.pyplot as plt
import mariadb, configparser
import matplotlib.dates as mdates

class ecs_graph:
    def __init__(self):
        self.read_config()
        self.get_dataframe()

    def read_config(self):
        config_file = 'ecs-sensor.ini'
        config = configparser.ConfigParser()
        config.read(config_file)
        self.db_info = {
            "database": config['Database']['Database'],
            "user": config['Database']['DbUser'],
            "pass": config['Database']['DbPass'],
            "host": config['Database']['DbHost'],
            "port": int(config['Database']['DbPort'])
                   }
        times = config['Graph']['TimeScales']
        self.df_t = times.split(', ')

    def get_dataframe(self):
        conn = mariadb.connect(
            database = self.db_info['database'],
            user = self.db_info['user'],
            password = self.db_info['pass'],
            host = self.db_info['host'],
            port = self.db_info['port']
        )
        cur = conn.cursor()
        cur.execute('select datetime, humidity, temp from environment')
        rows = cur.fetchall()

        df = pd.DataFrame( [[ij for ij in i] for i in rows] )
        df.rename(columns={0: 'DateTime', 1: 'Humidity', 2: 'Temperature'}, inplace=True)
        self.dataframe_transform(df)

    def dataframe_transform(self, df):
        for t in self.df_t:
            df2 = df
            if ("H" or "min") in t:
                df2['HourDatetime'] = pd.to_datetime(df2['DateTime'], format='%Y-%m-%d %H:%M:%S').dt.time
                df2['Hour'] = df2['HourDatetime'].map(lambda ts: ts.strftime("%I:%M %p"))
                df2 = df2.set_index(['DateTime'])
                df2 = df2.last(t)
                df2 = df2.set_index(['Hour'])
            if "D" in t:
                df2['Day'] = df2['DateTime'].map(lambda ts: ts.strftime("%m-%d %I:%M %p"))
                df2 = df2.set_index(['DateTime'])
                df2 = df2.last(t)
                df2 = df2.set_index(['Day'])
            self.plot_dataframe(df2, t)

    def plot_dataframe(self, df, t):
        fig, ax = plt.subplots(figsize = (16,12))
        ax.xaxis.set_major_locator(mdates.AutoDateLocator())
        ax.plot(df['Humidity'])
        fig.suptitle(t + ' - Humidity', fontsize=20)
        plt.xlabel('Time', fontsize=18)
        plt.ylabel('Relative Humidity', fontsize=16)
        plt.savefig(t + '_humidity.png')
        return
        plt.clf()

        fig, ax = plt.subplots(figsize = (16,12))
        ax.xaxis.set_major_locator(mdates.AutoDateLocator())
        ax.plot(df['Temperature'])
        fig.suptitle(t + ' - Temperature', fontsize=20)
        plt.xlabel('Time', fontsize=18)
        plt.ylabel('Temperature', fontsize=16)
        plt.savefig(t + '_temperature')

def main():
    gr = ecs_graph()

if __name__ == '__main__':
    main()
