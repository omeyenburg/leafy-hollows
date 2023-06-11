from cfunctions import graphics
import sys

failed = graphics.window("Test", 1000)
if failed:
    print("Window creation failed.")
    sys.exit()

#tree_image = graphics.load_image("tree.jpg")

# Use the window object
running = True
while running:
    # render
    
    graphics.blit(0, (20, 40))
    graphics.rect((255, 0, 0), (*graphics.get_mousepos(), 110, 80))
    running = graphics.update()

# Destroy the window
graphics.quit()