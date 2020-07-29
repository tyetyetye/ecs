#!/usr/bin/env python3

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import mariadb, configparser

class ecs_graph:
    def __init__(self):
        self.read_config()

    def read_config(self):
        config_file = 'ecs.ini'
        config = configparser.ConfigParser()
        config.read(config_file)
        self.db_d= {
            "database": config['Database']['Database'],
            "user": config['Database']['DbUser'],
            "pass": config['Database']['DbPass'],
            "host": config['Database']['DbHost'],
            "port": int(config['Database']['DbPort'])
        }
        self.plot_d = {
            "plot_size_x": int(config['Graph']['PlotSizeX']),
            "plot_size_y": int(config['Graph']['PlotSizeY']),
            "plot_sup_size": int(config['Graph']['PlotSupTitleSize']),
            "plot_x_label_size": int(config['Graph']['PlotXLabelSize']),
            "plot_y_label_size": int(config['Graph']['PlotYLabelSize'])
        }
        times = config['Graph']['TimeScales']
        self.df_t = times.split(', ')

    def get_dataframe(self):
        conn = mariadb.connect(
            database = self.db_d['database'],
            user = self.db_d['user'],
            password = self.db_d['pass'],
            host = self.db_d['host'],
            port = self.db_d['port']
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
            if ("D" or "M") in t:
                df['Day'] = df['DateTime'].map(lambda ts: ts.strftime("%m-%d %I:%M %p"))
                df = df.set_index(['DateTime'])
                df = df.last(t)
                df = df.set_index(['Day'])
            self.plot_dataframe(df, t)

    def plot_dataframe(self, df, t):
        #metrics = ['Humidity', 'Temperature']
        metrics = ['Humidity']
        tick_n = 10
        for metric in metrics:
            # set size of figure
            fig, ax = plt.subplots(figsize = (self.plot_d['plot_size_x'], self.plot_d['plot_size_y']))
            # color by metric
            if(metric == 'Humidity'):
                l_color = 'b'
            else:
                l_color = 'r'
            # plot axes
            ax.plot(df[metric], linewidth=2.0, ls='solid', color=l_color)
            # use tick_n as a maximum number of ticks
            if(df[metric].shape[0] > tick_n):
                x_ticks = list(range(1, df[metric].shape[0], int(df[metric].shape[0]/tick_n)))
                ax.set_xticks(x_ticks)
                #ax.xaxis.set_major_formatter(mdates.DateFormatter("%m-%d %I:%M %p"))
            else:
                ax.xaxis.set_major_locator(mdates.AutoDateLocator())
            # set figure title
            fig.suptitle(t + ' - ' + metric, fontsize=self.plot_d['plot_sup_size'])
            # Set x/y label
            plt.xlabel('Time', fontsize=self.plot_d['plot_x_label_size'])
            plt.ylabel(metric, fontsize=self.plot_d['plot_y_label_size'])
            # set xtick properties
            plt.setp(ax.get_xticklabels(), rotation=30, ha="right", rotation_mode="anchor")
            # show grid
            plt.grid(True)
            #plt.show()
            plt.savefig('./images/' + t + '_' + metric + '.png')
            plt.clf()

def main():
    gr = ecs_graph()
    gr.get_dataframe()

if __name__ == '__main__':
    main()
