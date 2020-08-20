#!/usr/bin/env python3

import RPi.GPIO as GPIO
from pi_sht1x import SHT1x
from datetime import datetime
import time, mariadb, syslog
from config import Config

class Environment:
    def __init__(self):
        self.log_d('Starting ECS Sensor Daemon...')
        self.config = Config()
        self.read_config()
        self.db_chk()
        self.create_tables()
        self.temp = None
        self.rh = None

    def db_chk(self):
        # Check if db connection is successful for logging purposes
        self.log_d('Trying to connect to MariaDB database on ' + self.host + '...')
        try:
            conn = mariadb.connect(
                database = self.database,
                user = self.user,
                password = self.password,
                host = self.host,
                port = self.port
            )
            self.log_d('Connection to MariaDB is succesful!')
        except mariadb.Error as e:
            self.err_l(e)

    # log message to daemon log
    def log_d(self, log_m):
        syslog.openlog(logoption=syslog.LOG_PID, facility=syslog.LOG_DAEMON)
        syslog.syslog(log_m)

    # error logging
    def err_l(self, error):
        syslog.openlog(logoption=syslog.LOG_PID, facility=syslog.LOG_DAEMON)
        syslog.syslog(syslog.LOG_ERR, str(error))

    def read_config(self):
        c = self.config.sensor()
        self.sense_t = c['sense_t']
        self.data_pin = c['data_pin']
        self.sck_pin = c['sck_pin']
        c = self.config.database()
        self.database = c['database']
        self.user = c['user']
        self.password = c['pass']
        self.host = c['host']
        self.port= c['port']

    def create_tables(self):
        try:
            conn = mariadb.connect(
                database = self.database,
                user = self.user,
                password = self.password,
                host = self.host,
                port = self.port
            )
            cur = conn.cursor()

            # create device table
            cur.execute('''CREATE TABLE IF NOT EXISTS device
                    (dev_id INT PRIMARY KEY,
                    dev_name VARCHAR(255),
                    dev_state TINYINT);'''
                    )
            cur.execute('''SELECT * FROM device;''')
            row = cur.fetchone()
            # initialize device table if empty
            if row is None:
                cur.execute('''INSERT INTO device VALUES (0, 'Humidifier', 0);''')
                cur.execute('''INSERT INTO device VALUES (1, 'Fan', 0);''')

            # create environment table
            cur.execute('''CREATE TABLE IF NOT EXISTS environment
                   (datetime DATETIME,
                   humidity DECIMAL(5,2),
                   temp DECIMAL(5,2));'''
                   )

            # create onoff table
            cur.execute('''CREATE TABLE IF NOT EXISTS onoff
                    (datetime DATE,
                    dev_id INT,
                    state TINYINT,
                    humidity DECIMAL(5,2),
                    temp DECIMAL(5,2),
                    FOREIGN KEY(dev_id)
                        REFERENCES device (dev_id));'''
                    )
            conn.close()

        except mariadb.Error as e:
            self.err_l(e)

    def read(self):
        # get env readings
        try:
            with SHT1x(self.data_pin, self.sck_pin, gpio_mode=GPIO.BCM) as sensor:
                temp = sensor.read_temperature()
                self.temp = sensor.temperature_fahrenheit
                self.rh = sensor.read_humidity(temp)
                if (self.temp and self.rh) is not None:
                    #print(self.temp, self.rh)
                    return True
        except Exception as e:
            self.err_l(e)
            return False

    def write(self):
        try:
            conn = mariadb.connect(
                database = self.database,
                user = self.user,
                password = self.password,
                host = self.host,
                port = self.port
            )
            cur = conn.cursor()
            # format time without ms
            time_now = datetime.now()
            time_now = time_now.strftime('%Y-%m-%d %H:%M:%S')
            # get environmental readings
            if(self.read()):
                print(time_now, self.rh, self.temp)
                cur.execute("INSERT INTO environment VALUES (?, ?, ?)", (time_now, self.rh, self.temp))
                self.rh = None
                self.temp = None
            conn.commit()
            conn.close()

        except mariadb.Error as e:
            self.err_l(e)

def main():
    env = Environment()
    while True:
        # re-read config to allow configuration changes without restarting daemon
        env.read_config()
        env.write()
        time.sleep(env.sense_t)

if __name__ == '__main__':
    main()
