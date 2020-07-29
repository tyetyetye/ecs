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
        config_file = 'ecs.ini'
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

    def dataframe_transform(self, dataframe):
        for t in self.df_t:
            df = dataframe
            if "min" in t:
                df['Minute'] = df['DateTime'].map(lambda ts: ts.strftime("%I:%M %p"))
                df = df.set_index(['DateTime'])
                df = df.last(t)
                df = df.set_index(['Minute'])
            if "H" in t:
                df['HourDatetime'] = pd.to_datetime(df['DateTime'], format='%Y-%m-%d %H:%M:%S').dt.time
                df['Hour'] = df['HourDatetime'].map(lambda ts: ts.strftime("%I:%M %p"))
                df = df.set_index(['DateTime'])
                df = df.last(t)
                df = df.set_index(['Hour'])
            if "D" in t:
                df['Day'] = df['DateTime'].map(lambda ts: ts.strftime("%m-%d %I:%M %p"))
                df = df.set_index(['DateTime'])
                df = df.last(t)
                df = df.set_index(['Day'])
            self.plot_dataframe(df, t)

    def plot_dataframe(self, df, t):
        metrics = ['Humidity', 'Temperature']
        for metric in metrics:
            fig, ax = plt.subplots(figsize = (16,12))
            ax.xaxis.set_major_locator(mdates.AutoDateLocator())
            ax.plot(df[metric])
            fig.suptitle(t + ' - ' + metric, fontsize=20)
            plt.xlabel('Time', fontsize=16)
            plt.ylabel(metric, fontsize=16)
            plt.savefig('./images/' + t + '_' + metric + '.png')
            plt.clf()

def main():
    gr = ecs_graph()

if __name__ == '__main__':
    main()
