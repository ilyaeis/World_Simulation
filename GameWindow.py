import json
import pygame
import numpy as np
import Map

class GameWindow:
    def __init__(self, path, map):
        self.map = map

        with open(path, 'r') as json_file:
            parameters = json.load(json_file)

        self.map_width, self.map_height = parameters["MAP_WIDTH"], parameters["MAP_HEIGHT"]
        self.window_width, self.window_height = parameters["WINDOW_WIDTH"], parameters["WINDOW_HEIGHT"]
        self.block_size = parameters["MAP_BLOCK_SIZE"]
        self.zoom = 1
        self.x, self.y = self.map_width // 2, self.map_height // 2
        self.blocks_to_show_x = self.window_width // self.block_size
        self.blocks_to_show_y = self.window_height // self.block_size

        self.color_map = np.zeros((self.blocks_to_show_x, self.blocks_to_show_y, 3), dtype=np.uint8)

        pygame.init()
        pygame.display.set_caption("The World")
        self.screen = pygame.display.set_mode((self.window_width, self.window_height))
        
    def get_color_map(self):
        start_x = max(0, self.x // self.block_size - self.blocks_to_show_x // 2)
        start_y = max(0, self.y // self.block_size - self.blocks_to_show_y // 2)

        end_x = int(start_x + self.blocks_to_show_x)
        end_y = int(start_y + self.blocks_to_show_y)

        if end_x > self.map_width:
            end_x = self.map_width - 1
            start_x = end_x - self.blocks_to_show_x
        if end_y > self.map_height:
            end_y = self.map_height - 1
            start_y = end_y - self.blocks_to_show_y
            
        return map.get_color_map_part(start_x, start_y, end_x, end_y)
    
    def start_xy(self):
        x = (self.x // self.block_size - self.blocks_to_show_x // 2) * self.block_size - self.x
        y = (self.y // self.block_size - self.blocks_to_show_y // 2) * self.block_size - self.y

        x = max(0, min(x, self.map_width-1)) 
        y = max(0, min(y, self.map_height-1)) 
        
        return (x, y)
    
    def check_events(self):
        for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:  # Left mouse button
                        self.mouse_dragging = True
                        self.prev_mouse_x, self.prev_mouse_y = event.pos 
                        return True

                elif event.type == pygame.MOUSEBUTTONUP:
                    if event.button == 1:  # Left mouse button
                        self.mouse_dragging = False
                        return True

                elif event.type == pygame.MOUSEMOTION:
                    if self.mouse_dragging:
                        dx = event.pos[0] - self.prev_mouse_x
                        dy = event.pos[1] - self.prev_mouse_y

                        self.x -= dx
                        self.y -= dy
                        
                        self.prev_mouse_x, self.prev_mouse_y = event.pos
                        return True

                elif event.type == pygame.MOUSEWHEEL:
                    mouse_x, mouse_y = pygame.mouse.get_pos()
                    
                    map_mouse_x = (self.x) // self.block_size
                    map_mouse_y = (self.y) // self.block_size

                    if event.y > 0:  # Scroll up (zoom in)
                        self.block_size += self.zoom
                    elif event.y < 0:  # Scroll down (zoom out)
                        self.block_size -= self.zoom
                        self.block_size = max(1, self.block_size) 

                    self.blocks_to_show_x = self.window_width // self.block_size 
                    self.blocks_to_show_y = self.window_height // self.block_size 

                    self.x = map_mouse_x * self.block_size
                    self.y = map_mouse_y * self.block_size

                    return True
        return False
    
    def show_window_loop(self):
        running = True
        action = True
        self.mouse_dragging = False
        while running:
            if action:
                color_map = self.get_color_map()
                sx, sy = self.start_xy()
                x, y = sx, sy
                for i in range(color_map.shape[0]):
                    for j in range(color_map.shape[1]):
                        pygame.draw.rect(self.screen, tuple(color_map[i, j]), (x, y, self.block_size, self.block_size))
                        x += self.block_size
                    y += self.block_size
                    x = sx

                action = False

            action = self.check_events()

            self.x = max(0, min(self.x, (self.map_width - 2) * self.block_size))
            self.y = max(0, min(self.y, (self.map_height - 2) * self.block_size))

            pygame.display.flip()

        pygame.quit()

if __name__ == "__main__":
    map = Map.Map("res/config.json")
    window = GameWindow("res/config.json", map)
    window.show_window_loop()
