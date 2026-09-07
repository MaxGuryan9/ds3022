import pandas as pd
import numpy as np
import requests
from PIL import Image
from io import BytesIO

image = "https://s3.amazonaws.com/uvasds-systems/images/vuelta.jpg"

response = requests.get(image)
img = Image.open(BytesIO(response.content)).convert("RGB")
pixels = np.array(img)

# flatten the (height, width, 3) array into rows of x, y, R, G, B
height, width, _ = pixels.shape
y_coords, x_coords = np.indices((height, width))

df = pd.DataFrame({
    "x": x_coords.flatten(),
    "y": y_coords.flatten(),
    "R": pixels[:, :, 0].flatten(),
    "G": pixels[:, :, 1].flatten(),
    "B": pixels[:, :, 2].flatten(),
})

print(df.head())

# a simple filter: boost red channel, kill blue channel
df["R"] = (df["R"] * 1.5).clip(0, 255).astype(np.uint8)
df["B"] = 0

# rebuild the array back into an image and save it
filtered_pixels = df[["R", "G", "B"]].to_numpy().reshape(height, width, 3).astype(np.uint8)
Image.fromarray(filtered_pixels).save("filtered.jpg")
