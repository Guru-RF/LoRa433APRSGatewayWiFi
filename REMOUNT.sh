#!/bin/bash 

sudo umount /Volumes/CIRCUITPY
sudo mkdir /Volumes/CIRCUITPY
sudo mount -o noasync -t msdos /dev/disk4s1 /Volumes/CIRCUITPY
