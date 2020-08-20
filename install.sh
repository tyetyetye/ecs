#!/bin/bash

ECS_INSTALL_DIR="/opt/ecs"

sudo systemctl daemon-reload
sudo systemctl stop ecs_sensor
sudo cp sensor.py $ECS_INSTALL_DIR
sudo cp plot.py $ECS_INSTALL_DIR
sudo cp config.py $ECS_INSTALL_DIR
sudo cp -r config $ECS_INSTALL_DIR
sudo chmod 755 $ECS_INSTALL_DIR/sensor.py
sudo chmod 755 $ECS_INSTALL_DIRopt/plot.py
sudo chmod -R 755 $ECS_INSTALL_DIRopt/config
sudo systemctl start ecs_sensor
