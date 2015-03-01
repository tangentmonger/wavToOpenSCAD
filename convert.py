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
data = compress_data_points(data, 500)
data = normalise_data_points(data, 0, 20)
#print(min(data), max(data), len(data))


THICKNESS = 2.0 #mm
BACKGROUND_HEIGHT = 0 #mm
HEIGHT = 5.0 #mm



with open("output.scad", "w") as output:
    print("""
            // Bend flat object on the cylinder width specified radius
            // dimensions: vector with dimensions of the object that should be bent
            // radius:     distance of the cylinder axis
            // nsteps:     number of parts the object will be split into before being bent 
            module cylindric_bend(dimensions, radius, nsteps = $fn) {
            assign(step_angle = nsteps == 0 ? $fa : atan(dimensions.y/(radius * nsteps)))
            assign(steps = nsteps == 0 ? dimensions.y/ (tan(step_angle) * radius) : nsteps)
            assign(step_width = dimensions.y / steps)
            {
            intersection() {
            child();
            cube([dimensions.x, step_width/2, dimensions.z]);
            }      
            for (step = [1:ceil(steps)]) {
            translate([0, radius * sin(step * step_angle), radius * (1 - cos(step * step_angle))])
            rotate(step_angle * step, [1, 0, 0])
            translate([0, -step * step_width, 0])
            intersection() {
            child();
            translate([0, (step - 0.5) * step_width, 0])
                cube([dimensions.x, step_width, dimensions.z]);
            }
            }
            }
            }
""", file=output)

    print("rotate([0,90,0]) cylindric_bend([%.2f, %.2f, %.2f], 100, $fn=10){" % (THICKNESS, len(data), 20), file=output)
    print("translate([0, %.2f, %.2f]) rotate([270,0,0]) rotate([0,90,0]) union() {" % (len(data), 20), file=output)
    #for index, pair in enumerate(pairs(data[0:2])):
    for index, pair in enumerate(pairs(data)):
        #circle at joint, for better joining
        print("\ttranslate([%.2f,%.2f,0]) linear_extrude(height=%.2f) circle(d=%.2f, $fn=6);" % (index, pair[0], HEIGHT, THICKNESS), file=output)

        length = math.sqrt(math.pow(pair[0] - pair[1], 2) + 1)
        cube = "translate([0, -%.2f, 0]) cube([%.2f, %.2f, %.2f])" % (THICKNESS / 2, length, THICKNESS, HEIGHT)
        angle = math.degrees(math.atan(pair[1] - pair[0]))
        print("\ttranslate([%.2f, %.2f, 0]) rotate([0, 0, %.2f]) %s;" % (index, pair[0], angle, cube), file=output)

    #final circle at last point
    print("\ttranslate([%.2f,%.2f,0]) linear_extrude(height=%.2f) circle(d=%.2f);" % (len(data) - 1, data[-1], HEIGHT, THICKNESS), file=output)

    #backgroud
    print("\tcube([%.2f, %.2f, %.2f]);" % (len(data) - 1, max(data), BACKGROUND_HEIGHT), file=output)

    print("}}", file=output)
