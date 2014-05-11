import wave
import struct
from itertools import zip_longest


def grouper(iterable, n, fillvalue=None):
    "Collect data into fixed-length chunks or blocks"
    # grouper('ABCDEFG', 3, 'x') --> ABC DEF Gxx"
    args = [iter(iterable)] * n
    #return zip_longest(*args, fillvalue=fillvalue)
    return zip(*args)


def scale(raw, scale_min, scale_max, n):

    print(raw)
    scale_range = scale_max - scale_min
    max_value = max(raw)
    print(max_value)
    #min_value = min(filter(lambda a: a>0, raw))
    min_value = min( raw)
    range_value = max_value - min_value
    normaliseddata = [((x - min_value) / range_value * scale_range) + scale_min for x in filter(lambda a: a>= min_value, raw)]
    points_per_slice = int(len(normaliseddata) / n)
    points = grouper(normaliseddata, points_per_slice)
    return points

def get_average(grouper):
    group = next(grouper)
    return  sum(point for point in group) / len(group)
        

       

w = wave.open("D20140510_184849_137_2-BETA_cheryl.wav","r")
print(w)
sample_width = w.getsampwidth()
print(sample_width)
print(w.getnchannels())

max_x = 120 #millimetres
max_y = 200
min_y = 5
range_y = max_y - min_y

data = []

outlier = 32568 #by inspection

#print(struct.unpack_from("<H", w.readframes(w.getnframes())))

try:
    for x in range(w.getnframes()):
        values = struct.unpack("@5h", w.readframes(1))
        #print(values)
        #value = values[0]
        #if value < outlier:
        data.append(values)
except:
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
        
        
        
        #print("translate([%d,%d,0]) cube([%d,1,1]);" % ((avg0/2) * -1, x, avg0), file=output)
        #linear_extrude(height = fanwidth, center = true, convexity = 10)
        print("translate([%d,%d,0]) rotate([90,0,0]) linear_extrude(height=1) polygon(points=[[0,0], [%d,0], [%d,%d], [%d,%d], [%d,%d], [0,%d]]);" % ((avg0/2) * -1, x, avg0, avg0, avg1, avg0*.6, avg2, avg0*.3,avg3,avg4 ), file=output)
