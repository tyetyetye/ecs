#!/usr/bin/env python3

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.ticker as mtick
import mariadb, configparser, sys
from multiprocessing import Process

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

    def get_dataframe(self):
        self.read_config()
        # TODO exception control for connecting to db and receiving rows
        conn = mariadb.connect(
            database = self.db_d['database'],
            user = self.db_d['user'],
            password = self.db_d['pass'],
            host = self.db_d['host'],
            port = self.db_d['port']
        )
        cur = conn.cursor()
        cur.execute(self.get_sql_query())
        rows = cur.fetchall()
        conn.close()
        dataframe = pd.DataFrame( [[ij for ij in i] for i in rows] )
        dataframe.rename(columns={0: 'DateTime', 1: 'Humidity', 2: 'Temperature'}, inplace=True)
        dataframe = dataframe.set_index(['DateTime'])
        return dataframe

    def get_sql_query(self):
        # Generate SQL query to return rows corresponding to the greatest timescale
        temp = '\t'.join(self.times)
        if 'M' in temp:
            max_t = 'M'
            sql_d = ' MONTH'
        elif 'D' in temp:
            max_t = 'D'
            sql_d = ' DAY'
        elif 'H' in temp:
            max_t = 'H'
            sql_d = ' HOUR'
        elif 'min' in temp:
            max_t = 'min'
            sql_d = ' MINUTE'
        max_n = 0
        for time in self.times:
            if max_t in time:
                time_n = int(time.split(max_t)[0])
                if time_n > max_n:
                    max_n = time_n
        return 'SELECT datetime, humidity, temp FROM environment WHERE datetime BETWEEN DATE_SUB(NOW(), INTERVAL ' + str(max_n) + sql_d \
            + ') AND NOW();'

    def plot_dataframe(self, timescales):
        self.times = timescales.split(', ')
        df = self.get_dataframe()
        for time in self.times:
            for metric in self.metrics:
                # multiprocessing
                p = Process(target = self.plot_worker, args=(df, time, metric))
                p.start()

    def plot_worker(self, df, time, metric):
        df = df.last(time)
        # set size of figure
        fig, ax = plt.subplots(figsize = (self.plot_d['size_x'], self.plot_d['size_y']), tight_layout=True)
        # set figure title
        fig.suptitle(time + ' - ' + metric, fontsize=self.plot_d['sup_size'])
        # timescale formatting
        if "D" in time:
            dayFmt = mdates.DateFormatter("%m-%d")
            hourFmt = mdates.DateFormatter("\n\n%-I:%M %p")
            ax.xaxis.set_major_locator(mdates.DayLocator())
            ax.xaxis.set_major_formatter(dayFmt)
            # format minor locator by number of days.  More days = less hour ticks
            n = int(time.split("D")[0])
            ax.xaxis.set_minor_locator(mdates.HourLocator(byhour=range(0,24,n)))
            ax.xaxis.set_minor_formatter(hourFmt)
        if "H" in time:
            hourFmt = mdates.DateFormatter("%-I %p")
            minuteFmt = mdates.DateFormatter("\n\n%-I:%M %p")
            ax.xaxis.set_major_locator(mdates.HourLocator())
            ax.xaxis.set_major_formatter(hourFmt)
            n = int(time.split("H")[0])*2
            ax.xaxis.set_minor_locator(mdates.MinuteLocator(byminute=range(0,60,n)))
            ax.xaxis.set_minor_formatter(minuteFmt)
        if "min" in time:
            minuteFmt = mdates.DateFormatter("%-I:%M %p")
            secondFmt = mdates.DateFormatter("\n\n%-I:%M:%S %p")
            # if minutes is too small minute/8 (for 8 major ticks) will equal 0
            n = 0
            m = 8
            while n == 0:
                n = round(int(time.split("min")[0])/m)
                m = m/2
            ax.xaxis.set_major_locator(mdates.MinuteLocator(byminute=range(0,60,round(n))))
            ax.xaxis.set_major_formatter(minuteFmt)
            n = int(time.split("min")[0])*2
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
        plt.savefig('./images/' + time + '_' + metric + '.png')
        print('Created: ./images/' + time + '_' + metric + '.png...')
        #plt.show()
        plt.clf()

def main():
    gr = ecs_graph()
    gr.plot_dataframe('15min, 6H, 3D')

if __name__ == '__main__':
    main()
