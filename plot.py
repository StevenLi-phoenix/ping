import multiprocessing
from multiprocessing import current_process
import os
import time

from PIL import Image, ImageDraw
import json
from tqdm import tqdm
from multiprocessing import Pool

import CONFIG


# Define the Hilbert curve function
def hilbert_curve(x0, y0, xi, xj, yi, yj, n):
    if n <= 0:
        return [(x0 + (xi + yi) / 2, y0 + (xj + yj) / 2)]

    # Hilbert curve construction
    step = 2 ** (n - 1)
    points = []
    points.extend(hilbert_curve(x0, y0, yi / 2, yj / 2, xi / 2, xj / 2, n - 1))
    points.extend(hilbert_curve(x0 + xi / 2, y0 + xj / 2, xi / 2, xj / 2, yi / 2, yj / 2, n - 1))
    points.extend(hilbert_curve(x0 + xi / 2 + yi / 2, y0 + xj / 2 + yj / 2, xi / 2, xj / 2, yi / 2, yj / 2, n - 1))
    points.extend(hilbert_curve(x0 + xi / 2 + yi, y0 + xj / 2 + yj, -yi / 2, -yj / 2, -xi / 2, -xj / 2, n - 1))
    return points


# Define the function to draw the Hilbert curve and input string
def draw_hilbert_curve(input_string):
    p = current_process()
    # Determine the order n of the Hilbert curve from the length of the input string
    n = 1
    while 2 ** (2 * n) < len(input_string):
        n += 1

    # Create a new PIL image of size (2 ** n, 2 ** n) and initialize all pixels to black
    size = 2 ** n
    image = Image.new("1", (size, size), color=0)

    if size == 4096 and n == 12 and not prebuilt_hilbertCurve_4096 is None:
        for index in tqdm(range(len(input_string)), position=p._identity[0]):
            if input_string[index] == '1':
                image.putpixel(tuple(prebuilt_hilbertCurve_4096[str(index)]), 1)
    else:
        # Iterate over all pixels in the image and set the color based on the input string
        for i in tqdm(range(size), position=p._identity[0]):
            for j in range(size):
                index = xy_to_hilbert(i, j, n)
                if input_string[index] == '1':
                    image.putpixel((i, j), 1)

    # Display the image
    # image.show()
    return image


def xy_to_hilbert(x, y, n):
    # Convert the x and y coordinates to a Hilbert curve index
    d = 0
    s = (1 << n) // 2
    index = 0
    while s > 0:
        rx = (x & s) > 0
        ry = (y & s) > 0
        if rx:
            if ry:
                d = (d + 3) % 4
            else:
                d = (d + 2) % 4
            x = (1 << n) - 1 - x
        else:
            if ry:
                d = (d + 1) % 4
            else:
                d = (d + 0) % 4
        index += s * s * d
        tx = (x & s) > 0
        ty = (y & s) > 0
        x, y = rot(s, x, y, tx, ty, d)
        s //= 2
    return index


def rot(n, x, y, rx, ry, d):
    # Apply a rotation and flip to the x and y coordinates
    if ry == 0:
        if rx == 1:
            x = n - 1 - x
            y = n - 1 - y
        x, y = y, x
    if d == 1:
        y = n - 1 - y
    elif d == 2:
        x = n - 1 - x
        y = n - 1 - y
    elif d == 3:
        x, y = y, x
        x = n - 1 - x
    return x, y

def process(index):
    print(f"PROCESS {index}")
    s = ""
    for ip2 in tqdm(range(256)):
        try:
            ipdata = json.load(open(os.path.join("ip", str(index), str(ip2)), "r"))
            try:
                assert len(ipdata.get("result_data")) == 65536
                s += ipdata["result_data"]
            except AssertionError:
                print(f"{index}-{ip2}: Data Error")
                sub = ipdata.get("result_data")
                sub = sub + (65536 - len(sub)) * "0"
                s += sub[:65536]
        except FileNotFoundError:
            print(f"{index}-{ip2}: Data Missing")
            s += "0" * 65536
        except json.decoder.JSONDecodeError:
            try:
                ipdata = open(os.path.join("ip", str(index), str(ip2)), "r").read()
                assert len(ipdata) == 65536
                print("[WARN] You are using older version of data structure, switch to new one if possible")
                s += ipdata
            except AssertionError:
                print(f"No idea what the data is check {os.path.join('ip', str(index), str(ip2))}")
                raise

    image = draw_hilbert_curve(s)
    path = os.path.join("picture", str(index) + ".png")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    image.save(path, format="png")
    return


def build_cache():
    print("BUILDING CACHE")
    prebuilt_hilbertCurve_4096 = {
        "INFO": "This is a prebuilt 4096 hilbert curve, mapping from index to x,y coordinate",
        "n": 12,
        "size": 4096,
        "mapping": "index to x,y coordinate",
        "createDate": time.time(),
    }
    DATA = {}
    for i in tqdm(range(4096)):
        for j in range(4096):
            index = xy_to_hilbert(i, j, 12)
            DATA[index] = (i, j)
    prebuilt_hilbertCurve_4096["DATA"] = DATA
    print("DUMPING FILE")
    json.dump(prebuilt_hilbertCurve_4096, open("prebuilt_hilbertCurve_4096.json", "w+"))
    return DATA

if __name__ == '__main__':
    if not CONFIG.PLOTCACHEBYPASS:
        print("Start to load prebuild hilbert curve, usually it will take 30 second or more")
        time_start = time.time()
        try:  # try to load cache
            prebuilt_hilbertCurve_4096 = json.load(open("prebuilt_hilbertCurve_4096.json", "r"))["DATA"]
        except FileNotFoundError:
            prebuilt_hilbertCurve_4096 = build_cache()
        print(f"Loaded prebuilt hilbert curve, take {round(time.time() - time_start, 2)} seconds")
    else:
        print("[WARNING] cache is bypassed manually.")
    with Pool(multiprocessing.cpu_count() // 2) as p:
        p.map(process, os.listdir("ip"))

