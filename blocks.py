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
    opcode = block["opcode"]
    try:
        script = BLOCKS[opcode](block_id, blocks)
    except KeyError:
        return f"missing handler for {opcode}"
    return script


def block_noinput(name):
    def f(block_id, blocks):
        block = blocks[block_id]
        next_block = block["next"]
        return {
            "label": name,
            "substack": None,
            "next": generate_script(next_block, blocks) if next_block else None
        }
    return f

BLOCKS = {
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
    print(blocks)

if __name__ == "__main__":
    main()
