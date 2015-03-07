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
data = compress_data_points(data, 200)
data = normalise_data_points(data, 0, 50)
#print(min(data), max(data), len(data))


THICKNESS = 4.0 #mm
BASE_HEIGHT = 10 #mm
DATA_HEIGHT = 5.0 #mm
START_ANGLE = 10 #degrees
ANGLE_CHANGE = -0.1 #percentage change
ANGLE_DELTA = 0  # percentage change
SECTION_WIDTH = 5 #mm
MIN_SPINE = 3 #mm
MAX_SPINE = 30 #mm

objects = []
last_x = 0
last_y = 0
angle = 0
next_angle = START_ANGLE

points = []

for index, value in enumerate(data):
    percent_value = float(value) / float(max(data)) if value > 0 else 0.0
    current_max_width = MAX_SPINE #should actually be some kind of curve 
    current_value_height = (current_max_width * percent_value) + MIN_SPINE
    print(index, percent_value, current_max_width, current_value_height)
    points.append("[%.2f, %.2f]" % (index, current_value_height))
    points.insert(0, "[%.2f, %.2f]" % (index, -current_value_height))


#for index, value in enumerate(reversed(data)):
#    points.append("[%.2f, %.2f]" % (len(data) - index - 1, (value / len(data) * index)))

with open("output.scad", "w") as output:
    for i in range(0,359,math.ceil(360/7)):
        print("rotate([0,0,%d]) { linear_extrude(height=%s) polygon([%s]);" % (i, THICKNESS, ",".join(points)), file=output)
        print("difference() {translate([%d, 0, 0]) cylinder(h=%d, r=%d);" % (len(data), THICKNESS, MIN_SPINE * 3), file=output)
        if i==0:
            print("} translate([%d, 0, 0]) cylinder(h=%d, r=%d);" % (len(data), THICKNESS*10, MIN_SPINE), file=output)
        else:
            print("translate([%d, 0, 0]) cylinder(h=%d, r=%d); }" % (len(data), THICKNESS, MIN_SPINE * 1.1), file=output)

        print ("}", file=output)
    
exit()

for index, pair in enumerate(pairs(data)):
    print(index, pair)
    points.append("[%.2f, %.2f]" % (0, 0))
    points.append("[%.2f, %.2f]" % (0, BASE_HEIGHT + pair[0]))
    points.append("[%.2f, %.2f]" % (SECTION_WIDTH, BASE_HEIGHT + pair[1]))
    points.append("[%.2f, %.2f]" % (SECTION_WIDTH, 0))
    shift = ""
    shift_back = ""
    match_y = THICKNESS
    if next_angle > 0:
        shift = "translate([0, %d, 0])" % THICKNESS
        #shift_back = "translate([0,  %d, 0])" % -THICKNESS
        match_y = 0.0
        pass
    objects.append("%s translate([%.2f, %.2f, 0]) rotate([0,0,%.2f]) %s rotate([90, 0, 0])  linear_extrude(height=%s) polygon([%s]);" % (shift_back, last_x, last_y,  angle, shift, THICKNESS, ",".join(points)))
    


    change_x = ((SECTION_WIDTH) * math.cos(math.radians(angle))) - (match_y * math.sin(math.radians(angle)))
    change_y = ((SECTION_WIDTH) * math.sin(math.radians(angle))) - (match_y * math.cos(math.radians(angle))) 
    last_x += change_x
    last_y += change_y 
    
    ANGLE_CHANGE += ANGLE_DELTA
    next_angle += ANGLE_CHANGE
    angle = (angle + next_angle) % 360

def divide_into_two_unions(objects):
    if len(objects) == 1:
        return objects[0]
    elif len(objects) == 2:
        return "\n".join(objects)
    else:
        halfway = int(len(objects) / 2)
        return "union() {%s}\nunion() {%s}" % (divide_into_two_unions(objects[:halfway]), divide_into_two_unions(objects[halfway:]))

with open("output.scad", "w") as output:
    print(divide_into_two_unions(objects), file=output)
    exit()

    objects_per_union = 100
    args = [iter(objects)] * objects_per_union
    unions = list(zip(*args))
            
            
    for index, union in enumerate(unions):
        print("union() {", file=output)
        objects_per_inner_union = 40
        inner_args = [iter(union)] * objects_per_inner_union
        inner_unions = list(zip(*inner_args))
        for inner_union in inner_unions:
            print("union() {", file=output)
            for box in inner_union:
                print(box, file=output)
            print("}", file=output)
        print("}", file=output)



