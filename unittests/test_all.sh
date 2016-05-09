#!/bin/bash

TEST_FILES=`find . -name "test_*.py"`

#TEST_FILES=customize_node/*
for test_file in $TEST_FILES
do
    echo "Running -> $PWD ---- $test_file"
    `python3 $test_file -q`
done

#./test_package_0ad_data.py -q
#./test_package_album.py -q
#./test_task.py -q
#./test_tmcmd_module.py -q
