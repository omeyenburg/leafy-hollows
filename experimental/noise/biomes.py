import numpy as np
import noise
import matplotlib.pyplot as plt


# Set the map dimensions and Perlin noise parameters
width = 100
height = 100
scale = 0.01
num_octaves = 4
persistence = 0.5
lacunarity = 2.0

# Generate biomes using Perlin noise
def generate_biome(x, y):
    biome = 0.0

    for i in range(num_octaves):
        freq = lacunarity ** i
        amp = persistence ** i
        biome += noise.pnoise2(x * freq * scale, y * freq * scale, octaves=num_octaves) * amp

    # Threshold the noise value to assign a biome
    if biome < -0.5:
        return 0  # Blue
    elif biome < 0.0:
        return 1  # Green
    elif biome < 0.5:
        return 2  # Yellow
    else:
        return 3  # Brown

# Create the biome map
biome_map = np.zeros((width, height), dtype=int)
for i in range(width):
    for j in range(height):
        biome_map[i, j] = generate_biome(i, j)

# Display the resulting biome map
#plt.imshow(biome_map, cmap='viridis')
#plt.colorbar(ticks=[0, 1, 2, 3])
#plt.show()

# Set the map dimensions and Perlin noise parameters
width = 100
height = 100
scale = 0.1

# Generate biomes using Perlin noise
def generate_biome(x, y):
    biome = noise.pnoise2(x * scale, y * scale)

    if biome < -0.333:
        return 0  # Blue
    elif biome < 0.333:
        return 1  # Green
    elif biome < 0.666:
        return 2  # Yellow
    else:
        return 3  # Brown

# Create the biome map
biome_map = np.zeros((width, height), dtype=int)
for i in range(width):
    for j in range(height):
        biome_map[i, j] = generate_biome(i, j)

# Display the resulting biome map
#plt.imshow(biome_map, cmap='viridis')
#plt.colorbar(ticks=[0, 1, 2, 3])
#plt.show()


import numpy as np
import noise

# Set the map dimensions and Perlin noise parameters
width = 100
height = 100
scale = 0.05

# Generate biomes using Perlin noise
def generate_biome(x, y):
    biome_1 = noise.pnoise3(x * scale, y * scale, 0.214)
    biome_2 = noise.pnoise3(x * scale, y * scale, 10.629864)

    if biome_1 < 0 and biome_2 < 0:
        return 0  # Blue
    elif biome_1 < 0 and biome_2 >= 0:
        return 1  # Green
    elif biome_1 >= 0 and biome_2 < 0:
        return 2  # Yellow
    else:
        return 3  # Brown

# Create the biome map
biome_map = np.zeros((width, height), dtype=int)
for i in range(width):
    for j in range(height):
        biome_map[i, j] = generate_biome(i, j)

# Display the resulting biome map
plt.imshow(biome_map, cmap='viridis')
plt.colorbar(ticks=[0, 1, 2, 3])
plt.show()