import numpy as np
from noise import snoise2
import json
from scipy.ndimage import distance_transform_edt
import pygame
import os

class Map:
    def __init__(self, path):
        self.map = self.load_map_from_file()

        with open(path, 'r') as json_file:
            parameters = json.load(json_file)

        self.width, self.height = parameters["MAP_WIDTH"], parameters["MAP_HEIGHT"]
        self.num_ellipses = parameters["MAP_NUM_ELLIPSES"]
        self.warp_frequency = parameters["MAP_WARP_FREQUENCY"]
        self.warp_magnitude = parameters["MAP_WARM_MAGNITUDE"]

        self.scale = parameters["NOISE_SCALE"]
        self.octaves = parameters["NOISE_OCTAVES"]
        self.persistence = parameters["NOISE_PERSISTENCE"]
        self.lacunarity = parameters["NOISE_LACUNARITY"]
        
        self.green_shades = parameters["COLORS_GREEN_SHADES"]
        self.blue_shades = parameters["COLORS_BLUE_SHADES"]

        self.rever_min_proximity = parameters["RIVER_MIN_PROXIMITY"]
        self.river_min_length = parameters["RIVER_MIN_LENGTH"]
        self.river_max_length = parameters["RIVER_MAX_LENGTH"]
        self.river_max_branches = parameters["RIVER_MAX_BRANCHES"]
        self.start_height = parameters["RIVER_START_HEIGHT_THRESHOLD"]
        self.sea_level = parameters["RIVER_SEA_LEVEL"]
        self.max_attempts = parameters["RIVER_MAX_ATTEMPTS"]

        if self.map is None:    
            mask = np.zeros((self.height, self.width))
            mask = self.create_landmass(mask)
            self.map = self.create_heightmap(42, mask)

            self.write_map_to_file(self.map)
        
        self.color_map = self.generate_color_map(self.map)

    def create_heightmap(self, seed, mask):
        np.random.seed(seed)
        distance_until_coastline = self.calculate_distance_field(mask)

        heightmap = np.zeros((self.height, self.width))
        for i in range(self.height):
            for j in range(self.width):
                noise_value = snoise2(j / self.scale,
                                  i / self.scale,
                                  octaves=self.octaves,
                                  persistence=self.persistence,
                                  lacunarity=self.lacunarity,
                                  base=seed)  # Seed value for consistency
                
                heightmap[i, j] = noise_value
        heightmap += 1.1 * distance_until_coastline

        min_value = np.min(heightmap)
        max_value = np.max(heightmap)
        heightmap = 2 * ((heightmap - min_value) / (max_value - min_value)) - 1
    
        return heightmap

    def normalise_mask(self, mask):
        min_value = np.min(mask)
        max_value = np.max(mask)
        
        normalized_mask = (mask - min_value) / (max_value - min_value)
        return normalized_mask
    
    def calculate_distance_field(self, mask):
        inverted_mask = 1 - mask  # Water becomes land and vice versa
        distance_terrain = distance_transform_edt(mask) 
        distance_water = distance_transform_edt(inverted_mask)

        distance_field = self.normalise_mask(distance_terrain) - self.normalise_mask(distance_water)
        
        return distance_field

    def create_landmass(self, mask):
        mask = self.spawn_ellipses(mask)
        mask = self.distort_mask(mask)
        mask = self.distort_mask(mask)

        return mask
    
    def spawn_ellipses(self, mask):
        y, x = np.meshgrid(range(self.height), range(self.width))
        x = x / self.width * 2 - 1  # Normalize to range [-1, 1]
        y = y / self.height * 2 - 1

        for _ in range(self.num_ellipses):
            # Randomize ellipse properties
            center_x = np.random.uniform(-0.5, 0.5)
            center_y = np.random.uniform(-0.5, 0.5)
            scale_x = np.random.uniform(0.1, 0.6)
            scale_y = np.random.uniform(0.1, 0.6)
            rotation = np.random.uniform(0, 2 * np.pi)

            # Compute ellipse mask
            cos_r = np.cos(rotation)
            sin_r = np.sin(rotation)
            ellipse_x = cos_r * (x - center_x) + sin_r * (y - center_y)
            ellipse_y = -sin_r * (x - center_x) + cos_r * (y - center_y)
            ellipse = ((ellipse_x / scale_x) ** 2 + (ellipse_y / scale_y) ** 2) <= 1
            mask = np.maximum(mask, ellipse)

        return mask

    def distort_mask(self, mask):
        for i in range(self.height):
            for j in range(self.width):
                nx = j / self.width * self.warp_frequency
                ny = i / self.height * self.warp_frequency
                warp_x = j + snoise2(nx, ny) * self.warp_magnitude
                warp_y = i + snoise2(nx + 100, ny + 100) * self.warp_magnitude
                if 0 <= int(warp_x) < self.width and 0 <= int(warp_y) < self.height:
                    mask[i, j] = mask[int(warp_y), int(warp_x)]

        return mask 
    
    def generate_color_map(self, heightmap):
        color_map = np.zeros((heightmap.shape[0], heightmap.shape[1], 3), dtype=np.uint8)

        for i in range(heightmap.shape[0]):
            for j in range(heightmap.shape[1]):
                value = heightmap[i, j]
                
                if value < 0:
                    normalized_value  = np.clip(-value / 1, 0, 1)  # Clamp to [0, 255]
                    index = int(normalized_value * (len(self.blue_shades) - 1))
                    color_map[i, j] = self.blue_shades[index]  # Light to Dark Green
                else:
                    normalized_value  = np.clip(value / 1, 0, 1)  # Clamp to [0, 255]
                    index = int(normalized_value * (len(self.green_shades) - 1))
                    color_map[i, j] = self.green_shades[index]  # Light to Dark Green
        
        return color_map

    def display(self, window_size=(1000, 1000)):
        pygame.init()

        # Create a window to display the map
        screen = pygame.display.set_mode(window_size)
        pygame.display.set_caption("Heightmap with Custom Colormap")
        
        # Convert heightmap to RGB colors using the custom color map
        self.color_map = self.generate_color_map(self.map)

        # Create a Pygame surface to display the color map
        surface = pygame.Surface(window_size)
        
        # Fill the surface with color_map data
        for i in range(window_size[0]):
            for j in range(window_size[1]):
                surface.set_at((i, j), tuple(self.color_map[j, i]))

        # Main loop to display the surface
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

            # Draw the surface on the screen
            screen.blit(surface, (0, 0))

            # Update the display
            pygame.display.flip()

        pygame.quit()

    def export_image(self, window_size=(1000, 1000)):
        pygame.init()

        # Create a window to display the map
        screen = pygame.display.set_mode(window_size)
        pygame.display.set_caption("Heightmap with Custom Colormap")
        
        # Convert heightmap to RGB colors using the custom color map
        self.color_map = self.generate_color_map(self.map)

        # Create a Pygame surface to display the color map
        surface = pygame.Surface(window_size)
        
        # Fill the surface with color_map data
        for i in range(window_size[0]):
            for j in range(window_size[1]):
                surface.set_at((i, j), tuple(self.color_map[j, i]))

        pygame.image.save(surface, "res/map.png")

    def write_map_to_file(self, map, file_path="res/map.json"):
        map_list = np.round(map, 4).tolist()
    
        data = {
            "map": map_list
        }
        
        with open(file_path, "w") as file:
            json.dump(data, file, indent=4)

    def load_map_from_file(self, file_path="res/map.json"):
        if os.path.exists(file_path):
            try:
                with open(file_path, "r") as file:
                    data = json.load(file)
                
                mask = np.array(data["map"], dtype=np.float32)  
                mask = np.round(mask, 4)

                return mask
            except Exception as e:
                print(f"Error loading map from file: {e}")
                return None
        return None
        
    def get_color_map_part(self, start_x, start_y, end_x, end_y):
        if not (0 <= start_x < self.width and 0 <= end_x <= self.width and
                0 <= start_y < self.height and 0 <= end_y <= self.height):
            raise ValueError("Specified coordinates are out of map bounds.")
        
        if start_x >= end_x or start_y >= end_y:
            raise ValueError("Start coordinates must be less than end coordinates.")

        return self.color_map[start_y:end_y, start_x:end_x]
    
if __name__ == "__main__":
    m = Map("res/config.json")
    m.export_image()