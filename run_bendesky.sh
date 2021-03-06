#!/bin/bash

## Custom setup for this workflow.
source .dlamirc

export PATH="/home/ubuntu/anaconda3/bin:$PATH"

source activate dlcami
## Import functions for workflow management. 
## Get the path to this function: 
execpath="$0"
echo execpath
scriptpath="$(dirname "$execpath")/ncap_utils"

source "$scriptpath/workflow.sh"
## Import functions for data transfer 
source "$scriptpath/transfer.sh"

## Set up error logging. 
errorlog

## Declare variables: bucketname,inputpath,groupdir,resultdir,dataname,configname given standard arguments to bin script.
parseargsstd "$1" "$2" "$3" "$4"

errorrep

## Declare local storage locations: 
userhome="/home/ubuntu"
datastore="ncapdata/localdata/"
outstore="ncapdata/localdata/analysis_vids/"
## Make local storage locations
accessdir "$userhome/$datastore" "$userhome/$outstore"

## Stereotyped download script for data. The only reason this comes after something custom is because we depend upon the AWS CLI and installed credentials. 
download "$inputpath" "$bucketname" "$datastore"

## Stereotyped download script for config: 
download "$configpath" "$bucketname" "$datastore"

###############################################################################################
## Video preprocessing:
## Import variables from the configuration file: 
read -r XS XA YS YA <<< $(jq -r .Coordinates[] "$userhome/$datastore/$configname")
read -r ext <<< $(jq -r .Ext "$userhome/$datastore/$configname")

## Preprocess videos 

## Run deeplabcut analysis: 
cd ../../DeepLabCut/Analysis-tools

python AnalyzeVideos_new.py
cd "$userhome"
## Custom bulk processing. 

###############################################################################################
## Stereotyped upload script for the data
upload "$outstore" "$bucketname" "$groupdir" "$resultdir" "mp4"

