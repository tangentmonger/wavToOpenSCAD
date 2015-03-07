import wave
import struct
import math
from itertools import zip_longest

""" General idea: read a 5 channel wav file from the EEG, collate the values from each channel, scale and chunk the values, and generate OpenSCAD code for a representation of the data"""


def get_data_points_from_wav_channel(wav_file, channel):
    w = wave.open("cheryl.wav","r")
    data = []
    try:
        for x in range(w.getnframes()):
            values = struct.unpack("@%dh" % w.getnchannels(), w.readframes(1))
            data.append(values)
    except:
        #might be an unfinished frame, we don't care
        pass

    channel_data = list(zip(*data))
    return channel_data[channel]


def normalise_data_points(source, new_min, new_max):
    old_min = min(source)
    old_max = max(source)
    old_range = old_max - old_min
    new_range = new_max - new_min

    normalised_data = [(((x - old_min) / old_range ) * new_range) + new_min for x in source]
    return normalised_data


def compress_data_points(source, new_length):
    points_per_slice = int(len(source) / new_length)
    args = [iter(source)] * points_per_slice
    slices = list(zip(*args))
    
    compressed_data = [sum(slice) / len(slice) for slice in slices]
    return compressed_data


def remove_outliers_from_data(source, outliers):
    average = sum(source) / len(source)
    sorted_data = sorted(source)
    result = list(source)
    for i in range(outliers):
        value = None
        if (average - sorted_data[0]) > (sorted_data[-1] - average):
            value = sorted_data[0]
            del sorted_data[0]
        else:
            value = sorted_data[-1]
            del sorted_data[-1]
        print(value)
        result.remove(value)
            
    return result


def lstrip_data(source, value):
    result = list(source)
    while result[0] == value:
        result.remove(value)

    return result


def pairs(lst):
    for i in range(len(lst) - 1):
        yield lst[i], lst[i+1]
    

data = get_data_points_from_wav_channel("cheryl.wav", 1)
data = lstrip_data(data, 0)
data = compress_data_points(data, 100)
data = normalise_data_points(data, 0, 40)
#print(min(data), max(data), len(data))


THICKNESS = 2.0 #mm
MIN_SPINE = 3 #mm
MAX_SPINE = 30 #mm


points = []
    

for index, value in enumerate(data):
    percent_value = float(value) / float(max(data)) if value > 0 else 0.0
    current_max_width = MAX_SPINE #should actually be some kind of curve 
    current_value_height = (current_max_width * percent_value) + MIN_SPINE
    print(index, percent_value, current_max_width, current_value_height)
    #points.append("[%.2f, %.2f]" % (index, current_value_height))
    #points.insert(0, "[%.2f, %.2f]" % (index, -current_value_height))
    #spiral = 0 #math.log(len(data) -index) * 3 if index > 0 else 0
    spiral = 0 #math.log(len(data) -index) * 3 if index > 0 else 0
   
    print(spiral)
    points.append("[%.2f, %.2f]" % (index * 2, current_value_height + spiral))
    points.insert(0, "[%.2f, %.2f]" % (index * 2, -current_value_height + spiral))



with open("output.scad", "w") as output:
    for i in range(0,360,math.ceil(360/7)):
        print("rotate([0,0,%d]) { linear_extrude(height=%s) polygon([%s]);" % (i, THICKNESS, ",".join(points)), file=output)
        print("difference() {translate([%d, 0, 0]) cylinder(h=%d, r=%d, $fn=3);" % (len(data) * 2+ MIN_SPINE, THICKNESS, MIN_SPINE * 3), file=output)
        if i==0:
            print("} translate([%d, 0, 0]) cylinder(h=%d, r=%d, $fn=3);" % (len(data) * 2 + MIN_SPINE, THICKNESS*10, MIN_SPINE), file=output)
        else:
            print("translate([%d, 0, 0]) cylinder(h=%d, r=%d, $fn=3); }" % (len(data) * 2+ MIN_SPINE, THICKNESS, MIN_SPINE * 1.5), file=output)

        print ("}", file=output)
    

