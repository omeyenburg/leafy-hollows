class Node:
    def __init__(self, position: list[int, int], parent):
        self.pos = position
        self.parent = parent

        self.f = 0
        self.g = 0
        self.h = 0

    def __eq__(self, other):
        return self.pos == other.pos


def print_path(grid: list[list[int]], path: list[list[int, int]]):
    for y, _ in enumerate(grid):
        for x, value in enumerate(grid[y]):
            if [x, y] in path:
                print("\x1b[42m" + " " + "\x1b[0m", end="")

            else:
                if value == 0:
                    print("\x1b[47m" + " " + "\x1b[0m", end="")
                elif value == 1:
                    print("\x1b[40m" + " " + "\x1b[0m", end="")
                else:
                    print("\x1b[41m" + " " + "\x1b[0m", end="")

        print()


def print_grid(grid: list[list[int]], open_list, closed_list, current_node):
    print()
    print(f"open list: {[n.pos for n in open_list]}")
    print(f"closed list: {[n.pos for n in closed_list]}")

    print(" " * len(str(len(grid))), end="")
    for x in range(len(grid[0])):
        print(x % 10, end="")
    print()

    for y, _ in enumerate(grid):
        print(str(y).zfill(len(str(len(grid)))), end="")
        for x, value in enumerate(grid[y]):
            if current_node.pos == [x, y]:
                print(f"\x1b[42m{hex(node.f % 16)[2:]}\x1b[0m", end="")
                continue

            for node in open_list:
                if node.pos == [x, y]:
                    print(f"\x1b[44m{hex(node.f % 16)[2:]}\x1b[0m", end="")
                    written = True
            if written:
                continue

            for node in closed_list:
                if node.pos == [x, y]:
                    print(f"\x1b[43m{hex(node.f % 16)[2:]}\x1b[0m", end="")
                    written = True
            if written:
                continue

            if value == 0:
                print("\x1b[47m" + " " + "\x1b[0m", end="")
            elif value == 1:
                print("\x1b[40m" + " " + "\x1b[0m", end="")
            else:
                print("\x1b[41m" + " " + "\x1b[0m", end="")

        print()
    print()


def a_star(grid, start_pos: list[int, int], end_pos: list[int, int], path_requirements: list[list[int, int]] = [], full_path: bool = True) -> list[list[int, int]] | list[int, int]:
    start_node, end_node = Node(start_pos, None), Node(end_pos, None)

    open_list, closed_list = [start_node], []
    while open_list:
        open_list.sort(key=lambda x: x.f)   # sort open list with respect to f value of nodes
        current_node = open_list[0]
        open_list.pop(0)
        closed_list.append(current_node)

        if current_node == end_node:    # finished
            path = []
            backtrack_node = current_node
            while backtrack_node:
                path.append(backtrack_node.pos)
                backtrack_node = backtrack_node.parent

            if full_path:
                path.reverse()
                return path
            else:
                return path[-1]

        for direction in [[1, 0], [0, -1], [-1, 0], [0, 1]]:    # find neighbours
            def valid_neighbour(pos) -> bool:
                def check_if_in_grid(pos: list[int, int]) -> bool:
                    if (-1 < pos[1] < len(grid)) and (-1 < pos[0] < len(grid[pos[1]])):
                        return True
                    return False

                if not check_if_in_grid(neighbour_pos):  # neighbour is outside of the grid
                    return False

                if grid[neighbour_pos[1]][neighbour_pos[0]] != 0:  # check if walkable
                    return False
                
                for requirement in path_requirements:
                    requirement_pos = [neighbour_pos[0] + requirement[0], neighbour_pos[1] + requirement[1]]
                    if check_if_in_grid(requirement_pos):
                        if grid[neighbour_pos[1] + requirement[1]][neighbour_pos[0] + requirement[0]] != 0:
                            return False
                    else:
                        return False

                for closed_node in closed_list:  # not searching again
                    if closed_node.pos == neighbour_pos:
                        if closed_node.g > current_node.g:    # found a better way
                            closed_list.remove(closed_node)
                            return True
                        return False

                for open_node in open_list:  # already marked for search
                    if open_node.pos == neighbour_pos:
                        if open_node.g > current_node.g:    # found a better way
                            open_list.remove(open_node)
                            return True
                        else:
                            return False

                return True

            neighbour_pos = [current_node.pos[0] + direction[0], current_node.pos[1] + direction[1]]

            if not valid_neighbour(neighbour_pos):
                continue

            neighbour_node = Node(neighbour_pos, current_node)
            neighbour_node.g = current_node.g + 1
            neighbour_node.h = abs(end_pos[0] - neighbour_pos[0]) + abs(end_pos[1] - neighbour_pos[1])  # manhatten distance
            neighbour_node.f = neighbour_node.g + neighbour_node.h

            open_list.append(neighbour_node)
        #print_grid(grid, open_list, closed_list, current_node)

def main():
    """
    grid = [[0, 1, 0, 0, 0],
            [0, 0, 0, 0, 0],
            [0, 1, 1, 1, 0],
            [0, 1, 0, 0, 0],
            [0, 1, 0, 1, 1],
            [0, 1, 0, 0, 0]]
    """
    """
    grid = [[0, 0, 0],
            [None, 0],
            [1, 0, 0]]
    """
    """
    grid = [[0, 0, 0],
            [0, 1, 0],
            [0, 1, 0]]
    """
    #"""
    grid = [[0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 1, 1, 1, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 1, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 1, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],]
    #"""
    start_pos = [1, 8]
    end_pos = [9, 2]

    path = a_star(grid, start_pos, end_pos, full_path=True)
    print()
    print(f"Path: {path}")
    if path:
        print_path(grid, path)


if __name__ == '__main__':
    main()
