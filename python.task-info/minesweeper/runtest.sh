#!/bin/bash

coverage3 erase
find . -iname 'test_*.py' -type f -exec coverage3 run -a {} \;
coverage3 report -m
