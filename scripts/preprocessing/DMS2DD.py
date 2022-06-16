"""Conversion of Latitude and Longitude column values in 
Degree Minutes and Seconds to Degree Decimals for an input file of csv or
excel format. The output will be in csv.

python DMS2DD.py -h
for help on usage of the script.
"""

import pandas as pd
import os
import re
import getopt
import sys

argumentList = sys.argv[1:]
options = "hi:y:x:o:"
long_options = ["help", "input=", "latitude=", "longitude=", "output="]

help_text = """\nDMS2DD\nConverts DMS value of latitude and longitude columns \
of input file (csv or excel) to DD.\n\nUsage:\npython DMS2DD.py [arguments]\n\n\
Arguments:\n\
[-h | --help] : display help doc\n\
[-i | --input] : input file path\n\
[-y | --latitude] : latitude column name in input file\n\
[-x | --longitude] : longitude column name in input file\n\
[-o | --output] : output (csv) file path\n\nExample:\n\
python DMS2DD.py -i C:\Docs\\file.csv -y LAT -x LONG -o C:\Desktop\output.csv"""


def progress(step, text):
    perc = int((step/4)*100)
    spaces = ' '*80
    sys.stdout.write(f'\r{spaces}')
    sys.stdout.flush()
    sys.stdout.write(f'\r {perc:03d}% : {text}')
    sys.stdout.flush()


if not argumentList:
    sys.exit(help_text)

try:
    arguments, values = getopt.getopt(argumentList, options, long_options)
    for currentArgument, currentValue in arguments:
        if currentArgument in ("-h", "--help"):
            sys.exit(help_text)
        elif currentArgument in ("-i", "--input"):
            file = currentValue
        elif currentArgument in ("-y", "--latitude"):
            lat_col = currentValue
        elif currentArgument in ("-x", "--longitude"):
            long_col = currentValue
        elif currentArgument in ("-o", "--output"):
            output = currentValue
except getopt.error as e:
    print(str(e))

progress(0, 'checking inputs...')
if 'file' not in globals():
    sys.exit('input file path is required')
if 'lat_col' not in globals():
    sys.exit('latitude column name is required')
if 'long_col' not in globals():
    sys.exit('longitude column name is required')
if 'output' not in globals():
    home = os.path.expanduser('~')
    output = os.path.join(home, 'Desktop', 'DMS2DD.csv')

progress(1, 'reading input file...')
if os.path.splitext(file)[1] == '.csv':
    try:
        df = pd.read_csv(file)
    except UnicodeDecodeError:
        df = pd.read_csv(file, encoding='cp1252')
else:
    df = pd.read_excel(file)


def correction(location):
    if location and str(location) != 'nan':
        direction = str(location).strip()[-1]
        split = re.split('[^\d\.]+', str(location))
        if len(split) > 2:
            try:
                degree = float(split[0]) if split[0] else 0
                minutes = float(split[1]) if split[1] else 0
                seconds = float(split[2]) if split[2] else 0
                value = degree + minutes/60 + seconds/3600
            except ValueError:
                raise ValueError(f'Could not convert {str(location)}')
            if direction == 'W' or direction == 'S':
                value *= -1
        else:
            value = split[0]
        return value
    else:
        return location


progress(2, 'correcting latitude...')
df[lat_col] = df[lat_col].apply(correction)

progress(3, 'correcting longitude...')
df[long_col] = df[long_col].apply(correction)

progress(4, f'output at {output}')
df.to_csv(os.path.splitext(output)[0]+'.csv')
