#!/usr/bin/env python3

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.ticker as mtick
import mariadb, configparser, sys
import multiprocessing

class ecs_graph:
    def __init__(self):
        self.config_file = 'ecs.ini'
        self.metrics = ['Humidity', 'Temperature']

    def read_config(self):
        config = configparser.ConfigParser()
        config.read(self.config_file)
        self.db_d= {
            "database": config['Database']['Database'],
            "user": config['Database']['DbUser'],
            "pass": config['Database']['DbPass'],
            "host": config['Database']['DbHost'],
            "port": int(config['Database']['DbPort'])
        }
        self.plot_d = {
            "size_x": int(config['Graph']['PlotSizeX']),
            "size_y": int(config['Graph']['PlotSizeY']),
            "sup_size": int(config['Graph']['SupTitleSize']),
            "x_label_size": int(config['Graph']['XLabelSize']),
            "y_label_size": int(config['Graph']['YLabelSize']),
            "humidity_color": config['Graph']['HumidityColor'],
            "temperature_color": config['Graph']['TemperatureColor'],
            "major_tick_size" : int(config['Graph']['XMajorTickSize']),
            "tick_label_rotation" : int(config['Graph']['TickRotation']),
            "x_tick_size" : int(config['Graph']['XTickSize'])

        }
        times = config['Graph']['TimeScales']
        # by default read .ini for timescales
        self.df_t = times.split(', ')

    def get_dataframe(self):
        self.read_config()
        conn = mariadb.connect(
            database = self.db_d['database'],
            user = self.db_d['user'],
            password = self.db_d['pass'],
            host = self.db_d['host'],
            port = self.db_d['port']
        )
        cur = conn.cursor()
        # TODO select LIMIT so whole database isn't pulled
        cur.execute('select datetime, humidity, temp from environment')
        rows = cur.fetchall()
        if rows:
            dataframe = pd.DataFrame( [[ij for ij in i] for i in rows] )
            dataframe.rename(columns={0: 'DateTime', 1: 'Humidity', 2: 'Temperature'}, inplace=True)
            dataframe = dataframe.set_index(['DateTime'])
            return dataframe

    def plot_dataframe(self, timescales = None):
        # use timescales if specified, otherwise use default read from .ini
        if timescales:
            times = timescales.split(', ')
        else:
            times = self.df_t
        df = self.get_dataframe()
        for t in times:
            for metric in self.metrics:
                self.plot_worker(df, t, metric)
                p = multiprocessing.Process(target = self.plot_worker, args=(df, t, metric))
                p.start()


    def plot_worker(self, df, t, metric):
        df = df.last(t)
        # set size of figure
        fig, ax = plt.subplots(figsize = (self.plot_d['size_x'], self.plot_d['size_y']), tight_layout=True)
        # set figure title
        fig.suptitle(t + ' - ' + metric, fontsize=self.plot_d['sup_size'])
        # timescale formatting
        if "D" in t:
            dayFmt = mdates.DateFormatter("%m-%d")
            hourFmt = mdates.DateFormatter("\n\n%-I:%M %p")
            ax.xaxis.set_major_locator(mdates.DayLocator())
            ax.xaxis.set_major_formatter(dayFmt)
            # format minor locator by number of days.  More days = less hour ticks
            n = int(t.split("D")[0])
            ax.xaxis.set_minor_locator(mdates.HourLocator(byhour=range(0,24,n)))
            ax.xaxis.set_minor_formatter(hourFmt)
        if "H" in t:
            hourFmt = mdates.DateFormatter("%-I %p")
            minuteFmt = mdates.DateFormatter("\n\n%-I:%M %p")
            ax.xaxis.set_major_locator(mdates.HourLocator())
            ax.xaxis.set_major_formatter(hourFmt)
            n = int(t.split("H")[0])*2
            ax.xaxis.set_minor_locator(mdates.MinuteLocator(byminute=range(0,60,n)))
            ax.xaxis.set_minor_formatter(minuteFmt)
        if "min" in t:
            minuteFmt = mdates.DateFormatter("%-I:%M %p")
            secondFmt = mdates.DateFormatter("\n\n%-I:%M:%S %p")
            # if minutes is too small minute/8 (for 8 major ticks) will equal 0
            n = 0
            m = 8
            while n == 0:
                n = round(int(t.split("min")[0])/m)
                m = m/2
            ax.xaxis.set_major_locator(mdates.MinuteLocator(byminute=range(0,60,round(n))))
            ax.xaxis.set_major_formatter(minuteFmt)
            n = int(t.split("min")[0])*2
            ax.xaxis.set_minor_locator(mdates.SecondLocator(bysecond=range(0,60,n)))
            ax.xaxis.set_minor_formatter(secondFmt)
        # color by metric
        if(metric == 'Humidity'):
            l_color = self.plot_d['humidity_color']
            ax.yaxis.set_major_formatter(mtick.PercentFormatter())
        else:
            l_color = self.plot_d['temperature_color']
        # plot axes
        ax.plot(df[metric], linewidth=2.0, ls='solid', color=l_color)
        # set xtick properties
        plt.setp(ax.get_xticklabels(minor='minor'), rotation=self.plot_d['tick_label_rotation'],
                     ha='right', size=self.plot_d['x_tick_size'])
        plt.setp(ax.get_xticklabels(which='major'), size=self.plot_d['major_tick_size'])
        ax.get_xaxis().set_tick_params(which='both', direction='in')
        ax.get_yaxis().set_tick_params(which='both', direction='in')
        # Set x/y label
        #plt.xlabel('Time', fontsize=self.plot_d['x_label_size'], labelpad=20)
        plt.ylabel(metric, fontsize=self.plot_d['y_label_size'], labelpad=20)
        # show grid
        plt.grid(which='major', linewidth=3)
        plt.grid(which='minor', linewidth=1)
        plt.savefig('./images/' + t + '_' + metric + '.png')
        print('Created: ./images/' + t + '_' + metric + '.png...')
        #plt.show()
        plt.clf()

def main():
    gr = ecs_graph()
    gr.plot_dataframe(timescales = '30min')

if __name__ == '__main__':
    main()
