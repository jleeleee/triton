import re

location_map_cache = {}


def parse_location_mappings(ir_file):
    """
    Parses the IR file content from a file object to extract the mapping of loc references to their source locations.

    Returns a dictionary with loc references as keys and the corresponding source location strings as values.
    """
    location_mapping = {}
    loc_pattern = re.compile(r'(#loc\d+)\s*=\s*loc\((.*)\)')

    for line in ir_file:
        match = loc_pattern.match(line.strip())
        if match:
            loc_ref = match.group(1)
            loc_content = match.group(2)
            location_mapping[loc_ref] = loc_content

    return location_mapping


def resolve_loc_reference(loc_ref, location_mapping):
    """
    Resolves a loc reference to its corresponding source location. Handles simple and complex callsite references.
    """
    if loc_ref.startswith('callsite'):
        # Handle callsite references
        callsite_pattern = re.compile(r'callsite\((#loc\d+)\s*at\s*(#loc\d+)\)')
        match = callsite_pattern.match(loc_ref)
        if match:
            called_loc = resolve_loc_reference(match.group(1), location_mapping)
            caller_loc = resolve_loc_reference(match.group(2), location_mapping)
            return f"{caller_loc} -> {called_loc}"
    else:
        # Simple loc reference
        return location_mapping.get(loc_ref, 'unknown')


def extract_loc_reference(line):
    """
    Extracts the loc reference from a line of IR code.
    """
    loc_pattern = re.compile(r'loc\((#loc\d+)\)')
    match = loc_pattern.search(line)
    if match:
        return match.group(1)
    return None


def get_source_location_from_line(line, location_mapping):
    """
    Given a line of IR code, extract the loc reference and return the corresponding source location.
    """
    loc_ref = extract_loc_reference(line)
    if loc_ref:
        return resolve_loc_reference(loc_ref, location_mapping)
    return "No location found"


def get_line_from_file(filename, line_number):
    with open(filename, 'r') as file:
        for current_line_number, line in enumerate(file, start=1):
            if current_line_number == line_number:
                return line.strip()  # Remove any leading/trailing whitespace
    return None  # If the line number is out of range


def extract_file_and_line(input_string):
    # Regular expression to match the file path and line number
    pattern = re.compile(r'(.+):[^@]+@(\d+)')
    match = pattern.match(input_string)
    if match:
        file_path = match.group(1)
        line_number = int(match.group(2))
        return file_path, line_number
    return None, None


def attribute_ttgir_frame_up(input_frame):
    file_path, line_number = extract_file_and_line(input_frame)

    if file_path and "ttgir" in file_path:
        line_content = get_line_from_file(file_path, line_number)

        # Parse the location mappings from the file content
        if file_path not in location_map_cache:
            with open(file_path, 'r') as f:
                location_map_cache[file_path] = parse_location_mappings(f)

        s = get_source_location_from_line(line_content, location_map_cache[file_path])
        return s.replace("\"", "").replace(":", ":@", 1).replace(":", "_")
    else:
        return input_frame
