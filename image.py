from PIL import Image, ImageOps
import numpy as np

class ImageToEPaperBuffer:
    def __init__(self, image_path):
        self.image_path = image_path
        self.image = None
        self.rgb_matrix = None
        self.target_size = (250, 124)  # Target size for the image (width, height)
        self.img_buffer = np.zeros(7750, dtype=np.uint8)  # Buffer of length 7750
        self.rows, self.cols = self.target_size
        self.pixels = None

    def load_image(self):
        """Load an image from the file and convert it to RGB mode."""
        try:
            self.image = Image.open(self.image_path)
            self.image = self.image.convert('RGB')  # Convert to RGB if it's not
        except Exception as e:
            print(f"Error loading image: {e}")
    
    def resize_with_letterbox(self):
        """Resize the image to target size using letterbox method (padding with white)."""
        if self.image is None:
            raise ValueError("Image not loaded. Please load the image first.")
        
        # Use ImageOps to add padding and resize with maintaining aspect ratio
        self.image = ImageOps.pad(self.image, self.target_size, color=(255, 255, 255))
    
    def image_to_rgb_matrix(self):
        """Convert the resized image to a numpy RGB matrix."""
        if self.image is None:
            raise ValueError("Image not loaded or resized. Please load and resize the image first.")
        
        transpose_img = self.image.transpose(Image.FLIP_TOP_BOTTOM)
        self.rgb_matrix = np.array(transpose_img)
        return self.rgb_matrix

    def _rgb_to_pixel_color(self, r, g, b):
        """Convert an RGB color to one of the 4 pixel colors."""
        # Define the RGB values for each color
        white = np.array([255, 255, 255])
        black = np.array([0, 0, 0])
        red = np.array([255, 0, 0])
        yellow = np.array([255, 255, 0])

        # Compute distances to each color
        color_diffs = {
            'PIXEL_WHITE': np.linalg.norm([r, g, b] - white),
            'PIXEL_BLACK': np.linalg.norm([r, g, b] - black),
            'PIXEL_RED': np.linalg.norm([r, g, b] - red),
            'PIXEL_YELLOW': np.linalg.norm([r, g, b] - yellow),
        }

        # Return the corresponding enum based on the closest color
        return {
            'PIXEL_WHITE': 0x01,
            'PIXEL_BLACK': 0x00,
            'PIXEL_RED': 0x03,
            'PIXEL_YELLOW': 0x02,
        }[min(color_diffs, key=color_diffs.get)]
    
    def convert_image_to_4_colors(self):
        """Convert the RGB image to a 4-color image and display it."""
        if self.rgb_matrix is None:
            raise ValueError("RGB matrix not generated. Please convert the image to RGB matrix first.")
        
        height, width, _ = self.rgb_matrix.shape  
        
        # Create an empty image to hold the 4-color result
        color_image = Image.new("RGB", (width, height))
        pixels = color_image.load()

        # Convert each pixel to the closest of the 4 colors
        for row in range(height):
            for col in range(width):
                r, g, b = self.rgb_matrix[row, col]
                pixel_color = self._rgb_to_pixel_color(r, g, b)

                # Map the pixel color value back to actual RGB values
                if pixel_color == 0x00:  # Black
                    pixels[col, row] = (0, 0, 0)
                elif pixel_color == 0x01:  # White
                    pixels[col, row] = (255, 255, 255)
                elif pixel_color == 0x02:  # Yellow
                    pixels[col, row] = (255, 255, 0)
                elif pixel_color == 0x03:  # Red
                    pixels[col, row] = (255, 0, 0)

        # Show the converted image
        color_image = color_image.transpose(Image.FLIP_TOP_BOTTOM)
        color_image.show()
    def convert_and_dither(self):
        self.pixels = np.array(self.image, dtype=np.float32)
        """Apply Floyd-Steinberg dithering to an image."""
        for y in range(self.image.height - 1):
            for x in range(self.image.width - 1):
                old_pixel = self.pixels[y, x]
                new_pixel_enum = self._rgb_to_pixel_color(*old_pixel[:3])
                new_pixel = np.array([255, 0, 0], dtype=np.float32) if new_pixel_enum == 0x03 else \
                            np.array([255, 255, 0], dtype=np.float32) if new_pixel_enum == 0x02 else \
                            np.array([0, 0, 0], dtype=np.float32) if new_pixel_enum == 0x00 else \
                            np.array([255, 255, 255], dtype=np.float32)
                self.pixels[y, x] = new_pixel

                quant_error = old_pixel - new_pixel
                self.pixels[y, x + 1] += quant_error * 7 / 16
                self.pixels[y + 1, x - 1] += quant_error * 3 / 16
                self.pixels[y + 1, x] += quant_error * 5 / 16
                self.pixels[y + 1, x + 1] += quant_error * 1 / 16

        # Convert array back to Image, clipping values to [0, 255] and converting to uint8
        self.pixels = np.clip(self.pixels, 0, 255).astype(np.uint8)
        self.image = Image.fromarray(self.pixels)
        self.image.show()

    def process_image_to_buffer(self):
        """Convert the image to an ePaper buffer with 7750 uint8 elements."""
        if self.rgb_matrix is None:
            raise ValueError("RGB matrix not generated. Please convert the image to RGB matrix first.")

        height, width, _ = self.rgb_matrix.shape  

        for row in range(height):  # 124
            for col in range(width):  # 250
                # Get the RGB values of the pixel
                r, g, b = self.rgb_matrix[row, col]
                color = self._rgb_to_pixel_color(r, g, b)
                
                # Calculate the index in the buffer
                index = row + col * height  # Correct order: col * height + row
                byte_index = index // 4
                bit_offset = 6 - (index % 4) * 2

                # Set the pixel in the buffer
                self.img_buffer[byte_index] &= ~(0x03 << bit_offset)
                self.img_buffer[byte_index] |= (color << bit_offset)

        return self.img_buffer


def print_img_buffer_as_c_array(img_buffer):
    """Print img_buffer as a C-style array."""
    print("uint8_t img_buffer[7750] = {")
    for i, byte in enumerate(img_buffer):
        # Print 12 bytes per line for better readability
        if i % 12 == 0:
            print("    ", end="")

        # Print each byte in hexadecimal format
        print(f"0x{byte:02X}", end="")

        # Add commas and formatting
        if i < len(img_buffer) - 1:
            print(", ", end="")
        if (i + 1) % 12 == 0:
            print()  # Newline after every 12 bytes

    print("\n};")


# Example usage
image_path = 'test6.jpg'  # Replace with your image path
converter = ImageToEPaperBuffer(image_path)
converter.load_image()
converter.resize_with_letterbox()
converter.convert_and_dither()
converter.image_to_rgb_matrix()
img_buffer = converter.process_image_to_buffer()
# converter.image.show()
# converter.convert_image_to_4_colors()

print("Image Buffer:", img_buffer)

print_img_buffer_as_c_array(img_buffer)
# col = 0
# for i in range(7750):
#     print(img_buffer[i])
#     # col = col + 1
#     if((col % 100) == 0):
#         print(col)
    