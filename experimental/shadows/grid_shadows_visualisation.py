import numpy
import pygame
import time


world_array = numpy.array([
    [0, 0, 0, 0, 0, 0, 0],
    [0, 1, 0, 1, 1, 0, 0],
    [0, 0, 1, 1, 0, 1, 0],
    [0, 0, 1, 1, 1, 1, 0],
    [0, 1, 1, 1, 1, 0, 0],
    [0, 0, 1, 0, 0, 0, 0],
    [0, 0, 0, 1, 0, 0, 0],
], dtype=int)


view = world_array.copy()
view[0, :] = 0
view[:, 0] = 0
view[view.shape[0] - 1, :] = 0
view[:, view.shape[1] - 1] = 0

"""
corners = set()

# Find corners
for x, y in numpy.ndindex((view.shape[0] - 1, view.shape[1] - 1)):
    count_air_blocks = 0
    for dx, dy in numpy.ndindex((2, 2)):
        if view[x + dx, y + dy] == 0:
            count_air_blocks += 1
        
    if count_air_blocks == 1 or count_air_blocks == 3:
        corners.add((x, y))
"""
view_shifted_right = numpy.roll(view, shift=-1, axis=0)
view_shifted_down = numpy.roll(view, shift=-1, axis=1)
view_shifted_diag = numpy.roll(view, shift=(-1, -1), axis=(0, 1))

count_air_blocks = (view == 0).astype(int) + (view_shifted_right == 0).astype(int) + (view_shifted_down == 0).astype(int) + (view_shifted_diag == 0).astype(int)
corner_indices = numpy.where((count_air_blocks == 1) | (count_air_blocks == 3))
corners = set(zip(corner_indices[0], corner_indices[1]))

# Find vertical edges
sorted_corners = sorted(corners, key=lambda corner: (corner[0], corner[1]))
flattened_corners = [coord for corner in sorted_corners for coord in corner]
edges = flattened_corners

# Find horizontal edges
sorted_corners = sorted(corners, key=lambda corner: (corner[1], corner[0]))
flattened_corners = [coord for corner in sorted_corners for coord in corner]
edges.extend(flattened_corners)


# In fragment shader
def get_collision(start, end, edges):
    for i in range(len(edges) // 4):
        edge = (
            edges[i * 4 + 0],
            edges[i * 4 + 1],
            edges[i * 4 + 2],
            edges[i * 4 + 3]
        )
        if edge[0] == edge[2]: # same x value
            distance = max(0.001, abs(start[0] - end[0]))
            distance_start = abs(start[0] - edge[0]) / distance
            distance_end = abs(end[0] - edge[0]) / distance
            
            x = edge[0]
            y = start[1] * distance_end + end[1] * distance_start
            if min(edge[1], edge[3]) < y < max(edge[1], edge[3]) and min(start[0], end[0]) < x < max(start[0], end[0]):
                pygame.draw.circle(window, (255, 0, 0), P(x, y), BLOCKSIZE / 8)
                p1 = P(edges[i * 4 + 0], edges[i * 4 + 1])
                p2 = P(edges[i * 4 + 2], edges[i * 4 + 3])
                pygame.draw.line(window, (255, 0, 0), p1, p2, 3)
                return True
            
        elif edge[1] == edge[3]: # same y value
            distance = max(0.001, abs(start[1] - end[1]))
            distance_start = abs(start[1] - edge[1]) / distance
            distance_end = abs(end[1] - edge[1]) / distance
            
            y = edge[1]
            x = start[0] * distance_end + end[0] * distance_start
            if min(edge[0], edge[2]) < x < max(edge[0], edge[2]) and min(start[1], end[1]) < y < max(start[1], end[1]):
                pygame.draw.circle(window, (255, 0, 0), P(x, y), BLOCKSIZE / 8)
                p1 = P(edges[i * 4 + 0], edges[i * 4 + 1])
                p2 = P(edges[i * 4 + 2], edges[i * 4 + 3])
                pygame.draw.line(window, (255, 0, 0), p1, p2, 3)
                return True
    return False


# Pygame visualisation
BLOCKSIZE = 64
window_size = (view.shape[0] * BLOCKSIZE, view.shape[1] * BLOCKSIZE)
pygame.init()
window = pygame.display.set_mode(window_size)
fragCoord = (2.9, 2.9)


# Drawing functions
def P(x, y):
    x += 1
    y += 1
    return (x * BLOCKSIZE, y * BLOCKSIZE)
def R(x, y):
    return (x * BLOCKSIZE, y * BLOCKSIZE, BLOCKSIZE, BLOCKSIZE)
        

quit = 0
while not quit:
    window.fill((0, 0, 0))
    mousePos = (pygame.mouse.get_pos()[0] / BLOCKSIZE - 1, pygame.mouse.get_pos()[1] / BLOCKSIZE - 1)
    
    for x, y in numpy.ndindex(view.shape):
        if view[x, y]:
            pygame.draw.rect(window, (255, 255, 255), R(x, y))
    for x, y in corners:
        pygame.draw.circle(window, (255, 0, 0), P(x, y), BLOCKSIZE / 8)
    for i in range(len(edges) // 4):
        p1 = P(edges[i * 4 + 0], edges[i * 4 + 1])
        p2 = P(edges[i * 4 + 2], edges[i * 4 + 3])
        pygame.draw.line(window, (0, 255, 0), p1, p2, 3)
    for x, y in (fragCoord, mousePos):
        pygame.draw.circle(window, (100, 100, 255), P(x, y), BLOCKSIZE / 8)
    if get_collision(mousePos, fragCoord, edges):
        pygame.draw.line(window, (255, 0, 0), P(*mousePos), P(*fragCoord), 3)
    else:
        pygame.draw.line(window, (0, 255, 0), P(*mousePos), P(*fragCoord), 3)

    pygame.display.flip()
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            quit = 1
