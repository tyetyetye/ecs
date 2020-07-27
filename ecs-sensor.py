#!/usr/bin/env python3

import RPi.GPIO as GPIO
from pi_sht1x import SHT1x
from datetime import datetime
import configparser, time, mariadb, syslog

config_file = '/opt/ecs/ecs-sensor.ini'

class environment:
    def __init__(self):
        self.log_d('Starting ECS Sensor Daemon...')
        self.read_config()
        self.create_tables()
        self.temp = None
        self.rh = None
        # Check if db connection is successful for logging purposes
        self.db_chk()

    def db_chk(self):
        self.log_d('Trying to connect to MariaDB database on ' + self.db_host + '...')
        try:
            conn = mariadb.connect(
                user = self.db_user,
                password = self.db_pass,
                host = self.db_host,
                port = self.db_port,
                database = self.db_database
            )
            self.log_d('Connection to MariaDB is succesful!')
            return True
        except mariadb.Error as e:
            self.err_l(e)
            return False

    # log message to daemon log
    def log_d(self, log_m):
        syslog.openlog(logoption=syslog.LOG_PID, facility=syslog.LOG_DAEMON)
        syslog.syslog(log_m)

    # error logging
    def err_l(self, error):
        syslog.openlog(logoption=syslog.LOG_PID, facility=syslog.LOG_DAEMON)
        syslog.syslog(syslog.LOG_ERR, str(error))

    def read_config(self):
        config = configparser.ConfigParser()
        config.read(config_file)
        self.sense_t = int(config['Sensor']['Rate'])
        self.data_pin = int(config['Sensor']['DataPin'])
        self.sck_pin = int(config['Sensor']['SckPin'])
        self.db_database = config['Database']['Database']
        self.db_user = config['Database']['DbUser']
        self.db_pass = config['Database']['DbPass']
        self.db_host = config['Database']['DbHost']
        self.db_port= int(config['Database']['DbPort'])

    def create_tables(self):
        try:
            conn = mariadb.connect(
                user = self.db_user,
                password = self.db_pass,
                host = self.db_host,
                port = self.db_port,
                database = self.db_database
            )
            cur = conn.cursor()
	    # drop tables for testing purposes
            #cur.execute('''DROP TABLE environment;''')
            #cur.execute('''DROP TABLE onoff;''')
            #cur.execute('''DROP TABLE device;''')

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
            return False

    def read(self):
        # get env readings
        try:
            with SHT1x(self.data_pin, self.sck_pin, gpio_mode=GPIO.BCM) as sensor:
                temp = sensor.read_temperature()
                self.temp = sensor.temperature_fahrenheit
                self.rh = sensor.read_humidity(temp)
                return True
        except Exception as e:
            self.err_l(e)
            return False


    def write(self):
        try:
            conn = mariadb.connect(
                user = self.db_user,
                password = self.db_pass,
                host = self.db_host,
                port = self.db_port,
                database = self.db_database
            )
            cur = conn.cursor()
            # format time without ms
            time_now = datetime.now()
            time_now = time_now.strftime('%Y-%m-%d %H:%M:%S')
            # get environmental readings
            if(self.read()):
                cur.execute('''INSERT INTO environment VALUES (?, ?, ?)''',
                        (time_now, self.rh, self.temp))
            conn.close()

        except mariadb.Error as e:
            self.err_l(e)

def main():
    env = environment()
    while True:
        # re-read config to allow configuration changes without restarting daemon
        env.read_config()
        env.write()
        time.sleep(env.sense_t)

if __name__ == '__main__':
    main()
