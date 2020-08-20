#!/bin/bash

ECS_INSTALL_DIR="/opt/ecs_sensor"
ECS_DAEMON="ecs_sensor"

sudo systemctl daemon-reload
sudo systemctl stop $ECS_DAEMON
sudo cp sensor.py $ECS_INSTALL_DIR
sudo cp config.py $ECS_INSTALL_DIR
sudo cp -r config $ECS_INSTALL_DIR
sudo chmod 644 $ECS_INSTALL_DIR/sensor.py
sudo chmod -R 644 $ECS_INSTALL_DIR/config
sudo systemctl start $ECS_DAEMON
