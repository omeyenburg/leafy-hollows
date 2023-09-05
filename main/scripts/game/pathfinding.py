import pygame
import random

# Constants
WIDTH, HEIGHT = 800, 600
CELL_SIZE = 20
GRID_WIDTH = WIDTH // CELL_SIZE
GRID_HEIGHT = HEIGHT // CELL_SIZE

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
YELLOW = (255, 255, 0)


class Maze:
    def __init__(self):
        self.grid = [[True for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]
        self.start_tile, self.end_tile = None, None
        self.generate_maze()

    def generate_maze(self):
        # Initialize a grid with walls
        visited = set()
        stack = [(1, 1)]
        self.grid[1][1] = False

        while stack:
            x, y = stack[-1]
            visited.add((x, y))
            neighbors = [(x+2, y), (x-2, y), (x, y+2), (x, y-2)]
            unvisited_neighbors = [(nx, ny) for nx, ny in neighbors if 0 < nx < GRID_WIDTH - 1 and 0 < ny < GRID_HEIGHT - 1 and (nx, ny) not in visited]

            if unvisited_neighbors:
                nx, ny = random.choice(unvisited_neighbors)
                wall_x, wall_y = (nx + x) // 2, (ny + y) // 2
                self.grid[ny][nx] = False
                self.grid[wall_y][wall_x] = False
                stack.append((nx, ny))
            else:
                stack.pop()

    def draw(self, screen):
        for y in range(GRID_HEIGHT):
            for x in range(GRID_WIDTH):
                if self.start_tile == [x, y]:
                    pygame.draw.rect(screen, RED, (x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE))
                elif self.end_tile == [x, y]:
                    pygame.draw.rect(screen, GREEN, (x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE))
                elif self.grid[y][x]:
                    pygame.draw.rect(screen, BLACK, (x*CELL_SIZE, y*CELL_SIZE, CELL_SIZE, CELL_SIZE))


class Node:
    def __init__(self, position: [int, int], parent: [int, int]):
        self.pos = position
        self.parent = parent

        self.f = 0
        self.g = 0
        self.h = 0

    def __eq__(self, other):
        return self.pos == other.pos


def a_star(maze, start_pos, end_pos, screen):
    start_node, end_node = Node(start_pos, None), Node(end_pos, None)

    open_list, closed_list = [start_node], []

    while open_list:
        for i in open_list:
            pygame.draw.rect(screen, RED, (i.pos[0] * CELL_SIZE, i.pos[1] * CELL_SIZE, CELL_SIZE, CELL_SIZE))

        current_node = open_list[0]
        current_index = 0
        for index, node in enumerate(open_list):    # find next node to search
            if node.f < current_node.f:
                current_node = node
                current_index = index
        open_list.pop(current_index)
        closed_list.append(current_node)

        if current_node == end_node:    # finished
            path = []
            backtrack_node = current_node
            while backtrack_node:
                path.append(backtrack_node.pos)
                backtrack_node = backtrack_node.parent

            return path.reverse()

        for direction in [[1, 0], [-1, 0], [0, 1], [0, -1]]:    # find neighbours
            neighbour_pos = [current_node.pos[0] + direction[0], current_node.pos[1] + direction[1]]
            if maze.grid[neighbour_pos[0]][neighbour_pos[1]]:   # check if wall
                continue
            neighbour_node = Node(neighbour_pos, current_node)

            for closed_node in closed_list: # no duplicates
                if neighbour_node == closed_node:
                    continue

            neighbour_node.g = current_node.g + 1
            neighbour_node.h = (abs(neighbour_pos[0]) - abs(end_pos[0])) + (abs(neighbour_pos[1]) - abs(end_pos[1]))    # manhatten distance
            neighbour_node.f = neighbour_node.g + neighbour_node.h

            for open_node in open_list: # Child is already in the open list
                if neighbour_node == open_node and neighbour_node.g > open_node.g:
                    continue

            open_list.append(neighbour_node)


def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Connected Wall Maze Generator")

    maze = Maze()

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        mouse_x, mouse_y = [v // CELL_SIZE for v in pygame.mouse.get_pos()]
        if not maze.grid[mouse_y][mouse_x]:
            if pygame.mouse.get_pressed()[0]:
                maze.start_tile = [mouse_x, mouse_y]
            elif pygame.mouse.get_pressed()[2]:
                maze.end_tile = [mouse_x, mouse_y]

            if maze.start_tile and maze.end_tile:
                print(a_star(maze, maze.start_tile, maze.end_tile, screen))
                return

        screen.fill(WHITE)
        maze.draw(screen)
        pygame.display.flip()

    pygame.quit()

if __name__ == "__main__":
    main()
