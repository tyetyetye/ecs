#!/usr/bin/env python3

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.ticker as mtick
import mariadb, sys, json
from multiprocessing import Process
from config import Config

class Plot:
    def __init__(self):
        self.metrics = ['Humidity', 'Temperature']
        self.config = Config()

    def get_dataframe(self):
        c = self.config.database()
        # TODO exception control for connecting to db and receiving rows
        conn = mariadb.connect(
            database = c['database'],
            user = c['user'],
            password = c['pass'],
            host = c['host'],
            port = c['port']
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
                p = Process(target = self.plot_worker, args=(df, time, metric, False))
                p.start()
                p = Process(target = self.plot_worker, args=(df, time, metric, True))
                p.start()

    def plot_worker(self, df, time, metric, thumb):
        df = df.last(time)
        c = self.config.plot()
        humidity_color = c['all']['humidity_color']
        temperature_color = c['all']['temperature_color']
        tick_label_rotation = c['all']['tick_label_rotation']
        save_path = c['all']['save_path']

        plot_line_width = c['large']['plot_line_width']
        major_grid_line_width = c['large']['major_grid_line_width']
        minor_grid_line_width = c['large']['minor_grid_line_width']
        plot_size_x = c['large']['plot_size_x']
        plot_size_y = c['large']['plot_size_y']
        sup_title_size = c['large']['sup_title_size']
        y_tick_label_size = c['large']['y_tick_label_size']
        x_major_tick_label_size = c['large']['x_major_tick_label_size']
        x_minor_tick_label_size = c['large']['x_minor_tick_label_size']
        x_label_size = c['large']['x_label_size']
        y_label_size = c['large']['y_label_size']
        x_label_pad = c['large']['x_label_pad']
        y_label_pad = c['large']['y_label_pad']
        rotation = c['large']['rotation']
        if thumb:
            plot_line_width = c['thumb']['plot_line_width']
            major_grid_line_width = c['thumb']['major_grid_line_width']
            minor_grid_line_width = c['thumb']['minor_grid_line_width']
            plot_size_x = c['thumb']['plot_size_x']
            plot_size_y = c['thumb']['plot_size_y']
            sup_title_size = c['thumb']['sup_title_size']
            y_tick_label_size = c['thumb']['y_tick_label_size']
            x_major_tick_label_size = c['thumb']['x_major_tick_label_size']
            x_label_size = c['thumb']['x_label_size']
            y_label_size = c['thumb']['y_label_size']
            x_label_pad = c['thumb']['x_label_pad']
            y_label_pad = c['thumb']['y_label_pad']
            rotation = c['thumb']['rotation']
        # create fig, ax and set size
        fig, ax = plt.subplots(figsize = (plot_size_x, plot_size_y))
        plt.ylabel(metric, fontsize=y_label_size, labelpad=y_label_pad)
        plt.xlabel('Time', fontsize=x_label_size, labelpad=x_label_pad)
        # set figure title
        fig.suptitle(time + ' - ' + metric, fontsize=sup_title_size)
        # timescale formatting
        if "D" in time:
            dayFmt = mdates.DateFormatter("%m-%d")
            hourFmt = mdates.DateFormatter("\n\n%-I:%M %p")
            ax.xaxis.set_major_locator(mdates.DayLocator())
            ax.xaxis.set_major_formatter(dayFmt)
            # format minor locator by number of days.  More days = less hour ticks
            n = int(time.split("D")[0])
            if not thumb:
                ax.xaxis.set_minor_locator(mdates.HourLocator(byhour=range(0,24,n)))
                ax.xaxis.set_minor_formatter(hourFmt)
        if "H" in time:
            hourFmt = mdates.DateFormatter("%-I %p")
            minuteFmt = mdates.DateFormatter("\n\n%-I:%M %p")
            ax.xaxis.set_major_locator(mdates.HourLocator())
            ax.xaxis.set_major_formatter(hourFmt)
            n = int(time.split("H")[0])*2
            if not thumb:
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
            if not thumb:
                ax.xaxis.set_minor_locator(mdates.SecondLocator(bysecond=range(0,60,n)))
                ax.xaxis.set_minor_formatter(secondFmt)
        # color by metric
        if(metric == 'Humidity'):
            l_color = humidity_color
            ax.yaxis.set_major_formatter(mtick.PercentFormatter())
        else:
            l_color = temperature_color
        # plot axes
        ax.plot(df[metric], linewidth=plot_line_width, ls='solid', color=l_color)
        # set rotation and alignment
        plt.setp(ax.get_xticklabels(which=rotation), rotation=tick_label_rotation,
                     ha='right')
        # set tick direction
        ax.get_xaxis().set_tick_params(which='both', direction='in')
        ax.get_yaxis().set_tick_params(which='both', direction='in')
        # set tick label sizes
        plt.setp(ax.get_yticklabels(), size=y_tick_label_size)
        plt.setp(ax.get_xticklabels(which='major'), size=x_major_tick_label_size)
        if not thumb:
            plt.setp(ax.get_xticklabels(which='minor'), size=x_minor_tick_label_size)
        ## show grid
        plt.grid(which='major', linewidth=major_grid_line_width)
        plt.grid(which='minor', linewidth=minor_grid_line_width)
        if thumb:
            save_f = '{}/{}_{}_thumb.png'.format(save_path, time, metric)
        else:
            save_f = '{}/{}_{}.png'.format(save_path, time, metric)
        plt.savefig(save_f, bbox_inches = "tight")
        print('Created: {}'.format(save_f))
        plt.clf()

def main():
    pl = Plot()
    pl.plot_dataframe('15min')

if __name__ == '__main__':
    main()
