import json
import re
import requests
import sys

def get_project_from_url(url):
    """Return project data for a URL."""
    match = re.search("scratch.mit.edu/projects/(\d+)/", url)
    if match is None:
        return None
    project_id = match.group(1)
    data = requests.get(f"https://projects.scratch.mit.edu/{project_id}").json()
    return data

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
    next_block = block["next"]
    opcode = block["opcode"]
    if opcode in BLOCKS:
        script = BLOCKS[opcode](block_id, blocks)
    else:
        return f"MISSING handler for {opcode}"
    if next_block:
        script["next"] = generate_script(next_block, blocks)
    return script


def generate_input(input_block, blocks):
    main_input = input_block[1]
    identifier = main_input[0]
    if identifier == 4: # number
        return main_input[1]
    else:
        return f"MISSING handler for input type {identifier}"


def block_noinput(name):
    def f(block_id, blocks):
        block = blocks[block_id]
        next_block = block["next"]
        return {
            "label": name
        }
    return f

def block_inputs(name, inputs):
    def f(block_id, blocks):
        block = blocks[block_id]
        args = [
            generate_input(block["inputs"][input_name], blocks)
            for input_name in inputs
        ]
        return {
            "label": name.format(*args)
        }
    return f


def print_blocks(scripts):
    def print_indent(block, indent):
        print(" " * indent, end="")
        print(block["label"])
        if "next" in block:
            print_indent(block["next"], indent)
    for script in scripts:
        print_indent(script, 0)
        print()

BLOCKS = {
    "motion_movesteps": block_inputs("move ({}) steps", ["STEPS"]),
    "event_whenflagclicked": block_noinput("when flag clicked")
}

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
