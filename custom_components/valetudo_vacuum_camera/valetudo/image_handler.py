
import logging
from custom_components.valetudo_vacuum_camera.const import *
import numpy as np
from PIL import Image, ImageDraw

_LOGGER = logging.getLogger(__name__)


class ImageHandler(Image):
    def __init__(self, json_data):
        self._name = "Valetudo Image Handler"
        self.map_json = json_data
        self.pixel_size = None
        self.flour_pixels = None
        self.walls_pixels = None
        self.path_pixels = None
        self.robot_pos = None
        self.charger_pos = None
        self.robot_position_angle = None
        self.go_to = None
        self.map_data = self.parsed_data(self.map_json)

    def sublist(self, lst, n):
        sub = []
        result = []
        for ni in lst:
            sub += [ni]
            if len(sub) == n:
                result += [sub]
                sub = []
        if sub:
            result += [sub]
        return result

    def sublist_join(self, lst, n):
        result = []
        sub = [lst[0]]
        for i in range(1, len(lst)):
            sub.append(lst[i])
            if len(sub) == n:
                result.append(sub)
                sub = [lst[i]]
        if sub:
            result.append(sub)
        return result

    def find_points_entities(self, json_obj, entity_dict=None):
        if entity_dict is None:
            entity_dict = {}
        if isinstance(json_obj, dict):
            if '__class' in json_obj and json_obj['__class'] == 'PointMapEntity':
                entity_type = json_obj.get('type')
                if entity_type:
                    if entity_type not in entity_dict:
                        entity_dict[entity_type] = []
                    entity_dict[entity_type].append(json_obj)
            for key, value in json_obj.items():
                self.find_points_entities(value, entity_dict)
        elif isinstance(json_obj, list):
            for item in json_obj:
                self.find_points_entities(item, entity_dict)
        return entity_dict

    def from_json_to_image(self, data, pixel_size, color):
        # Create an array of zeros for the image
        image_array = np.zeros((5120, 5120, 4), dtype=np.uint8)

        # Draw rectangles for each point in data
        for x, y, z in data:
            for i in range(z):
                col = (x + i) * pixel_size
                row = y * pixel_size
                image_array[row:row + pixel_size, col:col + pixel_size] = color

        # Convert the image array to a PIL image
        return image_array

    def crop_array(self, image_array, crop_percentage):
        """Crops a numpy array and returns the cropped image and scale factor."""
        center_x = image_array.shape[1] // 2
        center_y = image_array.shape[0] // 2
        crop_size = int(min(center_x, center_y) * crop_percentage / 100)
        cropbox = (center_x - crop_size, center_y - crop_size, center_x + crop_size, center_y + crop_size)
        cropped = image_array[cropbox[1]:cropbox[3], cropbox[0]:cropbox[2]]
        return cropped

    def draw_robot(self, layers, x, y, angle, robot_color):
        radius = 25
        tmpimg = Image.fromarray(np.zeros_like(layers))
        draw = ImageDraw.Draw(tmpimg)
        draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=robot_color, outline=robot_color)
        lidar_angle = np.deg2rad(angle - 90)  # Convert angle to radians and adjust for LIDAR orientation
        lidar_x = int(x + 9 * np.cos(lidar_angle))  # Calculate LIDAR endpoint x-coordinate
        lidar_y = int(y + 9 * np.sin(lidar_angle))  # Calculate LIDAR endpoint y-coordinate
        draw.line((x, y, lidar_x, lidar_y), fill=color_grey, width=5)
        # Convert the PIL image back to a Numpy array
        return np.array(tmpimg)

    def draw_battery_charger(self, layers, x, y, color):
        charger_width = 10
        charger_height = 20
        # Get the starting and ending indices of the charger rectangle
        start_row = y - charger_height // 2
        end_row = start_row + charger_height
        start_col = x - charger_width // 2
        end_col = start_col + charger_width
        # Fill in the charger rectangle with the specified color
        layers[start_row:end_row, start_col:end_col] = color

        return layers

    def draw_go_to_flag(self, center, layer):
        # Define flag color
        flag_color = (0, 255, 0)  # RGB color (green)
        # Define flag size and position
        flag_size = 40
        x1 = center[0] - flag_size // 2
        y1 = center[1] - flag_size // 2
        x2 = center[0] + flag_size // 2
        y2 = center[1] + flag_size // 2
        # Create an Image object from the layer array
        img = Image.fromarray(layer)

        # Draw flag on layer
        draw = ImageDraw.Draw(img)
        draw.rectangle((x1, y1, x2, y2), fill=flag_color)
        # Draw flag pole
        pole_width = 5
        pole_color = (0, 0, 255, 255)  # RGB color (blue)
        draw.rectangle((center[0] - pole_width // 2, y1, center[0] + pole_width // 2, y2), fill=pole_color)

        # Convert the Image object back to the numpy array
        layer = np.array(img)

        return layer

    def draw_lines(self, arr, coords, width, color):
        for coord in coords:
            # Use Bresenham's line algorithm to get the coordinates of the line pixels
            x0, y0 = coord[0]
            try:
                x1, y1 = coord[1]
            except:
                x1 = x0
                y1 = y0
            dx = abs(x1 - x0)
            dy = abs(y1 - y0)
            sx = 1 if x0 < x1 else -1
            sy = 1 if y0 < y1 else -1
            err = dx - dy
            line_pixels = []
            while True:
                line_pixels.append((x0, y0))
                if x0 == x1 and y0 == y1:
                    break
                e2 = 2 * err
                if e2 > -dy:
                    err -= dy
                    x0 += sx
                if e2 < dx:
                    err += dx
                    y0 += sy

            # Iterate over the line pixels and draw filled rectangles with the specified width
            for pixel in line_pixels:
                x, y = pixel
                for i in range(width):
                    for j in range(width):
                        if 0 <= x + i < arr.shape[0] and 0 <= y + j < arr.shape[1]:
                            arr[y + i, x + j] = color
        return arr

    def get_image_from_json(self, m_json):

        entity_dict = self.find_points_entities(m_json)
        self.robot_pos = entity_dict.get("robot_position")
        charger_pos = entity_dict.get("charger_location")
        self.charger_pos = charger_pos[0]["points"]
        self.flour_pixels = m_json["layers"][0]["compressedPixels"]
        self.walls_pixels = m_json["layers"][1]["compressedPixels"]
        self.path_pixels = m_json["entities"][0]["points"]

        # Numpy array pixels positions and colours computation
        img_np_array = self.from_json_to_image(self.flour_pixel,
                                               self.pixel_size,
                                               color_home_background)
        img_np_array = img_np_array + self.from_json_to_image(self.wall_pixel,
                                                              self.pixel_size,
                                                              color_wall)
        img_np_array = self.draw_lines(img_np_array, self.path_pixel2, 5, color_move)
        img_np_array = self.draw_battery_charger(img_np_array,
                                                 self._charger_pos[0],
                                                 self._selcharger_pos[1],
                                                 color_charger)
        if self.go_to:
            img_np_array = self.draw_go_to_flag((self.go_to[0]["points"][0],
                                                 self.go_to[0]["points"][1]),
                                                img_np_array)
        img_np_array = img_np_array + self.draw_robot(img_np_array,
                                                      self.robot_position[0],
                                                      self.robot_position[1],
                                                      self.robot_position_angle,
                                                      color_robot)

        img_np_array = self.crop_array(img_np_array, 25)

        pil_img = Image.fromarray(img_np_array)

        return pil_img