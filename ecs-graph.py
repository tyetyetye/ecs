#!/usr/bin/env python3

import pandas as pd
import matplotlib.pyplot as plt
import mariadb, configparser
import matplotlib.dates as mdates

config_file = 'ecs-sensor.ini'
config = configparser.ConfigParser()
config.read(config_file)
db_database = config['Database']['Database']
db_user = config['Database']['DbUser']
db_pass = config['Database']['DbPass']
db_host = config['Database']['DbHost']
db_port= int(config['Database']['DbPort'])

conn = mariadb.connect(
    user = db_user,
    password = db_pass,
    host = db_host,
    port = db_port,
    database = db_database
)
cur = conn.cursor()
cur = conn.cursor()
cur.execute('select datetime, humidity, temp from environment')
rows = cur.fetchall()

# create dataframe
df = pd.DataFrame( [[ij for ij in i] for i in rows] )
df.rename(columns={0: 'DateTime', 1: 'Humidity', 2: 'Temperature'}, inplace=True)
# Get hour from datetime format
df['HourDT'] = pd.to_datetime(df['DateTime'], format='%Y-%m-%d %H:%M:%S').dt.time
# Convert hour datetime to string
df['Hour'] = df['HourDT'].map(lambda ts: ts.strftime("%I:%M %p"))
# Set index by datetime
df = df.set_index(['DateTime'])
df2 = df.last("24H")
df2 = df2.set_index(['Hour'])
print(df2)

fig, ax = plt.subplots()
fig.set_size_inches(16, 12)
ax.plot(df2['Humidity'])
ax.xaxis.set_major_locator(mdates.AutoDateLocator())

fig.suptitle('24-Hour Humidity', fontsize=20)
plt.xlabel('Time', fontsize=18)
plt.ylabel('Relative Humidity', fontsize=16)
plt.savefig('24H_humidity.png')

plt.clf()

fig, ax = plt.subplots()
fig.set_size_inches(16, 12)
ax.plot(df2['Temperature'])
ax.xaxis.set_major_locator(mdates.AutoDateLocator())

fig.suptitle('24-Hour Temperature', fontsize=20)
plt.xlabel('Time', fontsize=18)
plt.ylabel('Temperature', fontsize=16)
plt.savefig('24H_temperature')
