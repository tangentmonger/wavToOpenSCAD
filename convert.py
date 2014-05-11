import wave
import struct
from itertools import zip_longest

""" General idea: read a 5 channel wav file from the EEG, collate the values from each channel, scale and chunk the values, and generate OpenSCAD code for a representation of the data"""


def grouper(iterable, n, fillvalue=None):
    "Collect data into fixed-length chunks or blocks"
    # grouper('ABCDEFG', 3, 'x') --> ABC DEF Gxx"
    args = [iter(iterable)] * n
    #return zip_longest(*args, fillvalue=fillvalue)
    return zip(*args)


def scale(raw, scale_min, scale_max, n):
    """Given a list of raw values, scale the values from scale_min to scale_max and build an iterator that breaks up the list into n chunks"""
    #TODO: doesn't handle data with outliers very well
    scale_range = scale_max - scale_min
    max_value = max(raw)
    #min_value = min(filter(lambda a: a>0, raw))
    min_value = min( raw)
    range_value = max_value - min_value
    normaliseddata = [((x - min_value) / range_value * scale_range) + scale_min for x in filter(lambda a: a>= min_value, raw)]
    points_per_slice = int(len(normaliseddata) / n)
    points = grouper(normaliseddata, points_per_slice)
    return points

def get_average(grouper):
    """Calculate the average of the values in the next group"""
    group = next(grouper)
    return  sum(point for point in group) / len(group)
        

       

w = wave.open("cheryl.wav","r")
sample_width = w.getsampwidth()
print(sample_width)
print(w.getnchannels())

max_x = 120 #millimetres (each slice of the mountain is 1mm)
max_y = 200 #millimetres
min_y = 5   #millimetres
range_y = max_y - min_y

data = []
try:
    for x in range(w.getnframes()):
        #assumption: this was a 5-channel wav file
        values = struct.unpack("@5h", w.readframes(1))
        data.append(values)
except:
    #might be an unfinished frame, we don't care
    pass

data0, data1, data2, data3, data4 = zip(*data)

ndata0 = scale(data0, 10, 200, max_x)
ndata1 = scale(data1, 2, 30, max_x)
ndata2 = scale(data2, 2, 30, max_x)
ndata3 = scale(data3, 2, 30, max_x)
ndata4 = scale(data4, 2, 30, max_x)

with open("output.scad", "w") as output:
    for x in range(max_x):
        avg0 = get_average(ndata0)
        avg1 = get_average(ndata1)
        avg2 = get_average(ndata2)
        avg3 = get_average(ndata3)
        avg4 = get_average(ndata4)
        
        
        #early version that produced a flat shape representing one channel
        #print("translate([%d,%d,0]) cube([%d,1,1]);" % ((avg0/2) * -1, x, avg0), file=output)
        
        #produce a "mountain" type shape representing all 5 channels
        print("translate([%d,%d,0]) rotate([90,0,0]) linear_extrude(height=1) polygon(points=[[0,0], [%d,0], [%d,%d], [%d,%d], [%d,%d], [0,%d]]);" % ((avg0/2) * -1, x, avg0, avg0, avg1, avg0*.6, avg2, avg0*.3,avg3,avg4 ), file=output)
