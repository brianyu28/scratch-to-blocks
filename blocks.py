import json
import re
import requests
import sys


FIELDS = {
    "_mouse_": "mouse-pointer",
    "_random_": "random position",
    "all around": "all around",
    "don't rotate": "don't rotate",
    "left-right": "left-right",
}


BLOCKS = {

    # Motion
    "motion_movesteps": ("move {} steps", ["STEPS"]),
    "motion_turnright": ("turn right {} degrees", ["DEGREES"]),
    "motion_turnleft": ("turn left {} degrees", ["DEGREES"]),
    "motion_goto": ("go to {}", ["TO"]),
    "motion_gotoxy": ("go to x: {} y: {}", ["X", "Y"]),
    "motion_glideto": ("glide {} secs to {}", ["SECS", "TO"]),
    "motion_glidesecstoxy": ("glide {} secs to x: {} y: {}", ["SECS", "X", "Y"]),
    "motion_pointindirection": ("point in direction {}", ["DIRECTION"]),
    "motion_pointtowards": ("point towards {}", ["TOWARDS"]),
    "motion_changexby": ("change x by {}", ["DX"]),
    "motion_setx": ("set x to {}", ["X"]),
    "motion_changeyby": ("change y by {}", ["DY"]),
    "motion_sety": ("set y to {}", ["Y"]),
    "motion_ifonedgebounce": ("if on edge, bounce", []),
    "motion_setrotationstyle": ("set rotation style [{} v]", [["STYLE", FIELDS]]),

    # Events
    "event_whenflagclicked": ("when flag clicked", []),

    # Control
    "control_repeat": ("repeat {}", ["TIMES"]),
}



INPUTS = {
    # Motion
    "motion_goto_menu": ("{} v", [["TO", FIELDS]]),
    "motion_glideto_menu": ("{} v", [["TO", FIELDS]]),
    "motion_pointtowards_menu": ("{} v", [["TOWARDS", FIELDS]]),
    "motion_xposition": ("(x position)", []),
    "motion_yposition": ("(y position)", []),
    "motion_direction": ("(direction)", []),

    # Operators
    "operator_add": ("({} + {})", ["NUM1", "NUM2"]),
}


def get_project_from_url(url):
    """Return project data for a URL."""
    match = re.search("scratch.mit.edu/projects/(\\d+)/", url)
    if match is None:
        return None
    project_id = match.group(1)
    res = requests.get(f"https://projects.scratch.mit.edu/{project_id}")
    return res.json()


def generate_scratchblocks(project):
    targets = project["targets"]
    scripts = []
    for target in targets:
        for block_id, block in target["blocks"].items():
            is_start = (
                isinstance(block, dict) and block["parent"] is None
                and block["opcode"] in BLOCKS
            )
            if is_start:
                script = generate_script(block_id, target["blocks"])
                scripts.append(script)
    return scripts


def generate_script(block_id, blocks):
    block = blocks[block_id]
    opcode = block["opcode"]
    if opcode in BLOCKS:
        name, inputs = BLOCKS[opcode]
        script = format_block(block_id, blocks, name, inputs)
    else:
        raise Exception(f"MISSING handler for {opcode}")

    # Handle next block
    next_block = block["next"]
    if next_block:
        script["next"] = generate_script(next_block, blocks)

    # Handle substack
    if "SUBSTACK" in block["inputs"]:
        substack_id = block["inputs"]["SUBSTACK"][1]
        script["substack"] = generate_script(substack_id, blocks)

    return script


def generate_input(input_block, blocks):
    """Generate input based on the value of INPUTS for a block."""
    main_input = input_block[1]
    if isinstance(main_input, str):
        return generate_input_block(main_input, blocks)
    elif isinstance(main_input, list):
        input_type = main_input[0]
        input_value = main_input[1]
        if input_type in [4, 5, 6, 7, 8, 9, 12, 13]:  # number, variable
            return f"({input_value})"
        elif input_type in [10, 11]:  # string, broadcast
            return f"[{input_value}]"

    else:
        raise Exception(f"Missing handler for input type {type(main_input)}")


def generate_input_block(block_id, blocks):
    """Generate the value of an input reporter."""
    block = blocks[block_id]
    opcode = block["opcode"]
    if opcode in INPUTS:
        name, inputs = INPUTS[opcode]
        input_block = format_input(block_id, blocks, name, inputs)
        return input_block
    else:
        raise Exception(f"Missing handler for input {opcode}")


def format_block(block_id, blocks, name, inputs):
    block = blocks[block_id]

    # Generate inputs for block
    args = []
    for input_name in inputs:
        if isinstance(input_name, str):
            arg = generate_input(block["inputs"][input_name], blocks)
            args.append(arg)
        elif isinstance(input_name, list):
            field_name, mapping = input_name
            args.append(mapping[block["fields"][field_name][0]])
        else:
            raise Exception(f"unsupported block type {type(input_name)}")
    data = {
        "label": name.format(*args)
    }
    return data


def format_input(block_id, blocks, name, inputs):
    block = blocks[block_id]

    args = []
    for input_name in inputs:
        if isinstance(input_name, str):
            arg = generate_input(block["inputs"][input_name], blocks)
            args.append(arg)
        elif isinstance(input_name, list):
            field_name, mapping = input_name
            args.append(mapping[block["fields"][field_name][0]])
        else:
            raise Exception(f"unsupported argument type {type(input_name)}")
    return name.format(*args)


def print_blocks(scripts):
    def print_indent(block, indent):
        print(" " * indent, end="")
        print(block["label"])

        # Print substack
        if "substack" in block:
            print_indent(block["substack"], indent + 4)
            print(" " * indent, end="")
            print("end")

        # Print next block
        if "next" in block:
            print_indent(block["next"], indent)
    for script in scripts:
        print_indent(script, 0)
        print()


def main():

    # Get Scratch project URL
    if len(sys.argv) > 2:
        sys.exit("Usage: python blocks.py SCRATCH_PROJECT_URL")
    elif len(sys.argv) == 2:
        url = sys.argv[1]
    else:
        url = input("Scratch Project URL: ")

    # Download project data
    data = get_project_from_url(url)
    if data is None:
        sys.exit("Could not download project.")

    # Generate blocks
    blocks = generate_scratchblocks(data)
    print_blocks(blocks)


if __name__ == "__main__":
    main()
