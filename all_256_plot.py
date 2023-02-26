# import os
# from PIL import Image
# from hilbertcurve.hilbertcurve import HilbertCurve
from tqdm import tqdm
#
# # Number of images
# num_images = 256
#
# # Image size (assuming all images have the same size)
# image_size = (4096, 4096)
#
# # Determine the order of the Hilbert curve based on the number of images
# order = 1
# while 2 ** (2 * order) < num_images:
#     order += 1
#
# # Create a Hilbert curve of the appropriate order
# hilbert_curve = HilbertCurve(order, 2)
#
# # Create a blank image to hold the arranged images
# arranged_image = Image.new('L', (image_size[0] * 2 ** order, image_size[1] * 2 ** order))
#
# # Load and arrange the images
# for i in tqdm(range(num_images)):
#     # Load the image
#     image_path = os.path.join(os.getcwd(), f"picture/{i}.png")
#     image = Image.open(image_path).convert('L')
#
#     # Determine the position of the image in the Hilbert curve
#     x, y = hilbert_curve.point_from_distance(i)
#
#     # Paste the image into the arranged image
#     arranged_image.paste(image, (x * image_size[0], y * image_size[1]))
#
# # Display the arranged image
# # arranged_image.show()
# arranged_image.save("ip.jpg")

import os
from PIL import Image
from hilbertcurve.hilbertcurve import HilbertCurve

# Number of images
num_images = 256

# Image size (assuming all images have the same size)
original_image_size = 8192  # should be times of 16
image_size = int(original_image_size / 16)

# Determine the order of the Hilbert curve based on the number of images
order = 1
while 2 ** (2 * order) < num_images:
    order += 1

# Create a Hilbert curve of the appropriate order
hilbert_curve = HilbertCurve(order, 2)

# Create a blank image to hold the arranged images
arranged_image = Image.new('L', (original_image_size, original_image_size))

# Load and arrange the images
for i in tqdm(range(num_images)):
    # Load the image as grayscale
    image_path = os.path.join(os.getcwd(), f"picture/{i}.png")
    image = Image.open(image_path).convert('L')

    # Resize the image to the desired size
    image = image.resize((image_size, image_size))

    # Determine the position of the image in the Hilbert curve
    x, y = hilbert_curve.point_from_distance(i)

    # Calculate the coordinates of the image in the arranged image
    x_coord = x * image_size
    y_coord = y * image_size

    # Paste the image into the arranged image
    arranged_image.paste(image, (x_coord, y_coord))

# Save the arranged image as a PNG file
arranged_image.save(f'ip_{original_image_size}.png')

