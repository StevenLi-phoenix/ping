import json
import numpy as np
import matplotlib.pyplot as plt
tn = 256
ipv4 = dict(json.load(open(f"ipv4.json","r")))

print(list(ipv4.values()))
mask_16 = ipv4['47']['95']

plot = np.zeros((256,256), dtype=int)
for key1 in mask_16.keys():
    for key2 in mask_16[key1].keys():
        plot[int(key1), int(key2)] = mask_16[key1][key2]

plot = plot > 0
plt.imshow(plot)
# plt.imsave(f"47.95.223.{tn}.png", frame)
plt.show()