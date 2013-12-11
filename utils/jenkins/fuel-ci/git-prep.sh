#!/bin/bash

REPO_PATH=$JENKINS_HOME

if [ ! -d $REPO_PATH/fuel-main ]
then
    cd $REPO_PATH
    git clone https://github.com/stackforge/fuel-main.git
else
    cd $REPO_PATH/fuel-main
    git fetch origin master
    git checkout FETCH_HEAD
fi
