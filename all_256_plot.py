from tqdm import tqdm
import os
from PIL import Image
from hilbertcurve.hilbertcurve import HilbertCurve

# Number of images
num_images = 256

original_image_size = 8192  # should be times of 16
image_size = int(original_image_size / 16)

order = 1
while 2 ** (2 * order) < num_images:
    order += 1

hilbert_curve = HilbertCurve(order, 2)

arranged_image = Image.new('L', (original_image_size, original_image_size))

# Load and arrange the images
for i in tqdm(range(num_images)):
    image_path = os.path.join(os.getcwd(), f"picture/{i}.png")
    image = Image.open(image_path).convert('L')

    image = image.resize((image_size, image_size))

    x, y = hilbert_curve.point_from_distance(i)

    x_coord = x * image_size
    y_coord = y * image_size

    arranged_image.paste(image, (x_coord, y_coord))

arranged_image.save(f'ip_{original_image_size}.png')

