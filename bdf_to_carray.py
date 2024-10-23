def bdf_to_c_array(bdf_data):
    """
    Converts BDF format data to C language arrays.
    Only processes ASCII visible characters and the degree symbol (U+00B0).

    Args:
    bdf_data (str): BDF font data as a string.

    Returns:
    str: C arrays for each character.
    """
    import re

    # This pattern matches each character block in the BDF data
    char_pattern = re.compile(
        r"STARTCHAR\s*(.*?)\n"  # Start of character block
        r"ENCODING\s*(\d+)\n"  # Character encoding number
        r".*?"  # Skip intermediate lines
        r"BBX\s*(\d+)\s*(\d+)\s*(-?\d+)\s*(-?\d+)\n"  # Bounding box
        r"BITMAP\s*(.*?)\nENDCHAR",  # Bitmap data
        re.DOTALL)

    # Match all characters in the data
    characters = char_pattern.findall(bdf_data)

    # Filter and convert only ASCII visible characters and degree symbol (176)
    valid_encodings = set(range(33, 127)) | {176}
    
    c_arrays = ""

    for char_name, encoding, width, height, xoff, yoff, bitmap_data in characters:
        encoding = int(encoding)
        if encoding in valid_encodings:
            char_var_name = re.sub(r'\W+', '_', char_name.lower())
            bitmap_lines = bitmap_data.strip().split('\n')
            bitmap_bin = []

            for line in bitmap_lines:
                bin_line = f"{int(line, 16):0>{int(width)}b}"[:int(width)]  # Truncate to the specified width
                bitmap_bin.append(bin_line)

            c_array = f"const uint8_t char_{char_var_name}[{height}][{width}] = {{\n"
            for line in bitmap_bin:
                c_array += "    {" + ", ".join('1' if x == '1' else '0' for x in line) + "},\n"
            c_array += "};\n\n"
            c_arrays += c_array

    return c_arrays

# Read a BDF file
def read_bdf_file(file_path):
    with open(file_path, 'r') as file:
        bdf_data = file.read()
    return bdf_data

# File path to your BDF file
bdf_file_path = 'test_front\spleen-12x24.bdf'

# Read the BDF file data
bdf_data = read_bdf_file(bdf_file_path)

# Convert to C arrays
c_code = bdf_to_c_array(bdf_data)

# You can now print the C code or write it to a file
print(c_code)
