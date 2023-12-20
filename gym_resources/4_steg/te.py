import numpy as np  # type: ignore
import matplotlib  # type: ignore

try:
    import Image  # type: ignore
except ImportError:
    from PIL import Image  # type: ignore


# hrsCTF{solv3d!} in binary
flag = [
    "01101000",
    "01110010",
    "01110011",
    "01000011",
    "01010100",
    "01000110",
    "01111011",
    "01110011",
    "01101111",
    "01101100",
    "01110110",
    "00110011",
    "01100100",
    "00100001",
    "01111101",
]


def to_binary(value):
    return bin(value)[2:].zfill(8)


# convert image to np array
image = Image.open("exerciseImage.png")
image_array = np.asarray(image)

# create empty np array of same shape as image array
binary_image_array = np.empty(image_array.shape, dtype=object)

# recreate image with binary pixel values
for i in range(image_array.shape[0]):
    for j in range(image_array.shape[1]):
        binary_image_array[i, j] = [to_binary(image_array[i, j, k]) for k in range(3)]

flag = "".join(flag)

# steg algorithm encrypts two bits per color channel, so pair up two bits of flag
bit_pairs = []
for i in range(0, len(flag), 2):
    bit_pairs.append(flag[i : i + 2])

# embed bit pairs into last two bits of each color channel
ticker = 0
for row in range(binary_image_array.shape[0]):
    for col in range(binary_image_array.shape[1]):
        for chan_index in range(len(binary_image_array[row, col])):
            binary_image_array[row, col][chan_index] = (
                binary_image_array[row, col][chan_index][:-2] + bit_pairs[ticker]
            )
            ticker += 1


# encryption part complete, now produce new image
def binary_to_int(binary_str):
    return int(binary_str, 2)


height, width, channels = binary_image_array.shape
new_image_array = np.zeros((height, width, channels), dtype=np.uint8)

for row in range(height):
    for col in range(width):
        for chan in range(channels):
            new_image_array[row, col, chan] = binary_to_int(
                binary_image_array[row, col][chan]
            )

new_image = Image.fromarray(new_image_array, "RGB")
new_image.save("modified_image.png")


"""# image part complete, now test decryption

image2 = Image.open("modified_image.png")
image_array2 = np.asarray(image2)

# create empty np array of same shape as image array
binary_image_array2 = np.empty(image_array2.shape, dtype=object)

# recreate image with binary pixel values
for i in range(image_array2.shape[0]):
    for j in range(image_array2.shape[1]):
        binary_image_array2[i, j] = [to_binary(image_array2[i, j, k]) for k in range(3)]

flag2 = []
for row in range(image_array2.shape[0]):
    for col in range(image_array2.shape[1]):
        for chan in range(len(binary_image_array2[row, col])):
            flag2.append(binary_image_array2[row, col, chan][6:8])
            print(binary_image_array2[row, col, chan][:-2])
flag2 = "".join(flag2)

grouped = []

for i in range(0, len(flag2), 8):
    grouped.append(flag2[i:i+8])

print(grouped) # IT WORKS!!!!"""
