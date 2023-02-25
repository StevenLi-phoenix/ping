import os

from PIL import Image, ImageDraw
import json
from tqdm import tqdm

import logger

log = logger.create_default_logger()


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
    # Determine the order n of the Hilbert curve from the length of the input string
    n = 1
    while 2 ** (2 * n) < len(input_string):
        n += 1

    # Create a new PIL image of size (2 ** n, 2 ** n) and initialize all pixels to black
    size = 2 ** n
    image = Image.new("1", (size, size), color=0)

    # Iterate over all pixels in the image and set the color based on the input string
    for i in tqdm(range(size)):
        for j in range(size):
            index = xy_to_hilbert(i, j, n)
            if input_string[index] == '1':
                image.putpixel((i, j), 1)

    # Display the image
    image.show()


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


# Run the function with an example input string
# input_string = "1100101001110110" * 4096  # 65536 bits
s = ""
for ip2 in tqdm(range(256)):
    ipdata = json.load(open(os.path.join("ip","47",str(ip2)), "r"))
    assert ipdata["success"] == True
    assert len(ipdata["result_data"]) == 65536
    s += ipdata["result_data"]
draw_hilbert_curve(s)
