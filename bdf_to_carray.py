def bdf_to_c_array_with_null_pointer(bdf_data):
    """
    Converts BDF format data to C language arrays, creates a pointer array for all characters, and adds a 'null' character array.
    Only processes ASCII visible characters and the degree symbol (U+00B0).
    
    Args:
    bdf_data (str): BDF font data as a string.

    Returns:
    str: C arrays for each character and a pointer array for all characters including a 'null' array.
    """
    import re

    # This pattern matches each character block in the BDF data
    char_pattern = re.compile(
        r"STARTCHAR\s*(.*?)\n"  # Start of character block
        r"ENCODING\s*(8451|\d+)\n"  # Character encoding number
        r".*?"  # Skip intermediate lines
        r"BBX\s*(\d+)\s*(\d+)\s*(-?\d+)\s*(-?\d+)\n"  # Bounding box (width, height, x-offset, y-offset)
        r"BITMAP\s*(.*?)\nENDCHAR",  # Bitmap data
        re.DOTALL)

    # Match all characters in the data
    characters = char_pattern.findall(bdf_data)

    # Filter and convert only ASCII visible characters and degree symbol (176)
    # ASCII visible characters are from 33 to 126, degree symbol is 176
    valid_encodings = set(range(33, 127)) | {176}
    
    c_arrays = ""
    pointer_array = ["char_null"] * 256  # Initialize pointer array for all 256 ASCII values with 'char_null'

    for char_name, encoding, width, height, xoff, yoff, bitmap_data in characters:
        encoding = int(encoding)
        if encoding in valid_encodings:
            # Normalize the character name for C variable (replace spaces and special characters)
            char_var_name = re.sub(r'\W+', '_', char_name.lower())
            bitmap_lines = bitmap_data.strip().split('\n')
            
            # Convert hex data in bitmap to binary strings, ensure each line is padded correctly based on width
            bitmap_bin = []

            for line in bitmap_lines:
                # remove '0' tail
                line = line[:-1]    
                expected_length = int(width)
                binary_length = len(line) * 4

                decimal_value = int(line, 16)

                if binary_length >= expected_length:
                    formatted_binary = f"{decimal_value:0{expected_length}b}"
                else:
                    formatted_binary = f"{decimal_value:0>{expected_length}b}"

                bitmap_bin.append(formatted_binary)
            
            # Create the C array string, considering correct padding for binary representation
            c_array = f"const uint8_t char_{char_var_name}[{height}][{width}] = {{\n"
            for line in bitmap_bin:
                c_array += "    {" + ", ".join('1' if x == '1' else '0' for x in line) + "},\n"
            c_array += "};\n\n"
            
            c_arrays += c_array
            pointer_array[encoding] = f"char_{char_var_name}"  # Update pointer array at the specific ASCII index

    # Add the 'null' character array for unmatched characters
    c_arrays += "const uint8_t char_null[24][12] = {\n"
    c_arrays += "    {" + ", ".join("0" for _ in range(12)) + "},\n" * 24
    c_arrays += "};\n\n"

    # Generate the pointer array string
    pointers = "const uint8_t* font_pointers[256] = {\n"
    pointers += ",\n".join(f"    [{i}] = {ptr}" for i, ptr in enumerate(pointer_array))
    pointers += "\n};\n"

    return c_arrays + pointers

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
c_code = bdf_to_c_array_with_null_pointer(bdf_data)

# You can now print the C code or write it to a file
print(c_code)

# Write the output to a file
output_file_path = 'test_front\spleen-12x24.h'
with open(output_file_path, 'w') as file:
    file.write(c_code)
