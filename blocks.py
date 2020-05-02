import json
import re
import requests
import sys


BLOCKS = {

    # Motion
    "motion_movesteps": ("move ({}) steps", ["STEPS"]),
    "motion_turnright": ("turn right ({}) degrees", ["DEGREES"]),
    "motion_turnleft": ("turn left ({}) degrees", ["DEGREES"]),

    # Events
    "event_whenflagclicked": ("when flag clicked", []),

    # Control
    "control_repeat": ("repeat ({})", ["TIMES"]),
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
            if block["parent"] is None:
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
        return {"label": f"MISSING handler for {opcode}"}

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
    main_input = input_block[1]
    identifier = main_input[0]
    if identifier in [4, 5, 6, 7, 8]:  # number
        return main_input[1]
    else:
        return f"MISSING handler for input type {identifier}"


def format_block(block_id, blocks, name, inputs):
    block = blocks[block_id]

    # Generate inputs for block
    args = [
        generate_input(block["inputs"][input_name], blocks)
        for input_name in inputs
    ]
    data = {
        "label": name.format(*args)
    }
    return data


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
