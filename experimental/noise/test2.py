import numpy as np
import matplotlib.pyplot as plt
from scipy.spatial import Voronoi, voronoi_plot_2d

# Set the map dimensions and number of biomes
width = 100
height = 100
num_biomes = 20

# Generate random points as the biome centers
points = np.random.rand(num_biomes, 2) * [width, height]

# Generate Voronoi diagram
vor = Voronoi(points)

# Create a map with the corresponding biome index for each block
biome_map = np.zeros((width, height), dtype=int)
for i in range(width):
    for j in range(height):
        distances = np.linalg.norm(points - [i, j], axis=1)
        closest_biome = np.argmin(distances)
        biome_map[i, j] = closest_biome

# Plot the Voronoi diagram
voronoi_plot_2d(vor)
plt.xlim([0, width])
plt.ylim([0, height])
plt.show()

# Display the resulting biome map
plt.imshow(biome_map)
plt.colorbar()
plt.show()