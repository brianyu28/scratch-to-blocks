import json
import re
import requests
import sys
import webbrowser

from urllib.parse import quote

OPEN_IN_BROWSER = True


def custom_block(block):
    """Formatting for a custom My Block"""
    proccode = block["mutation"]["proccode"].replace("%s", "{}").replace("%b", "{}")
    placeholders = re.findall("%[sb]", block["mutation"]["proccode"])
    inputs = json.loads(block["mutation"]["argumentids"])
    for i, input_id in enumerate(inputs):
        if input_id not in block["inputs"]:
            block["inputs"][input_id] = [1, [10, ""]] if placeholders[i] == "%s" else [1, ["BOOL", ""]]
    return proccode, inputs


FIELDS = {
    "_mouse_": "mouse-pointer",
    "_random_": "random position",
    "PAN": "pan left/right",
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
    "motion_setrotationstyle": ("set rotation style [{} v]", [["STYLE", {}]]),

    # Looks
    "looks_sayforsecs": ("say {} for {} seconds", ["MESSAGE", "SECS"]),
    "looks_say": ("say {}", ["MESSAGE"]),
    "looks_thinkforsecs": ("think {} for {} seconds", ["MESSAGE", "SECS"]),
    "looks_think": ("think {}", ["MESSAGE"]),
    "looks_switchcostumeto": ("switch costume to {}", ["COSTUME"]),
    "looks_nextcostume": ("next costume", []),
    "looks_switchbackdropto": ("switch backdrop to {}", ["BACKDROP"]),
    "looks_nextbackdrop": ("next backdrop", []),
    "looks_changesizeby": ("change size by {}", ["CHANGE"]),
    "looks_setsizeto": ("set size to {} %", ["SIZE"]),
    "looks_changeeffectby": ("change [{} v] effect by {}", [["EFFECT", {}], "CHANGE"]),
    "looks_seteffectto": ("set [{} v] effect to {}", [["EFFECT", {}], "VALUE"]),
    "looks_cleargraphiceffects": ("clear graphic effects", []),
    "looks_show": ("show", []),
    "looks_hide": ("hide", []),
    "looks_gotofrontback": ("go to [{} v] layer", [["FRONT_BACK", {}]]),
    "looks_goforwardbackwardlayers": ("go [{} v] {} layers", [["FORWARD_BACKWARD", {}], "NUM"]),

    # Sound
    "sound_playuntildone": ("play sound {} until done", ["SOUND_MENU"]),
    "sound_play": ("start sound {}", ["SOUND_MENU"]),
    "sound_stopallsounds": ("stop all sounds", []),
    "sound_changeeffectby": ("change [{} v] effect by {}", [["EFFECT", FIELDS], "VALUE"]),
    "sound_seteffectto": ("set [{} v] effect to {}", [["EFFECT", FIELDS], "VALUE"]),
    "sound_cleareffects": ("clear sound effects", []),
    "sound_changevolumeby": ("change volume by {}", ["VOLUME"]),
    "sound_setvolumeto": ("set volume to {} %", ["VOLUME"]),

    # Events
    "event_whenflagclicked": ("when flag clicked", []),
    "event_whenkeypressed": ("when [{} v] key pressed", [["KEY_OPTION", {}]]),
    "event_whenthisspriteclicked": ("when this sprite clicked", []),
    "event_whenbackdropswitchesto": ("when backdrop switches to [{} v]", [["BACKDROP", {}]]),
    "event_whengreaterthan": ("when [{} v] > {}", [["WHENGREATERTHANMENU", FIELDS], "VALUE"]),
    "event_whenbroadcastreceived": ("when I receive [{} v]", [["BROADCAST_OPTION", {}]]),
    "event_whenstageclicked": ("when stage clicked", []),

    # check these two
    "event_broadcast": ("broadcast {}", ["BROADCAST_INPUT"]),
    "event_broadcastandwait": ("broadcast {} and wait", ["BROADCAST_INPUT"]),

    # Control
    "control_wait": ("wait {} seconds", ["DURATION"]),
    "control_repeat": ("repeat {}", ["TIMES"]),
    "control_if": ("if {} then", ["CONDITION"]),
    "control_if_else": ("if {} then", ["CONDITION"]),
    "control_forever": ("forever", []),
    "control_repeat_until": ("repeat until {}", ["CONDITION"]),
    "control_stop": ("stop [{} v]", [["STOP_OPTION", {}]]),
    "control_start_as_clone": ("when I start as a clone", []),
    "control_create_clone_of": ("create clone of {}", ["CLONE_OPTION"]),
    "control_delete_this_clone": ("delete this clone", []),
    "control_wait_until": ("wait until {}", ["CONDITION"]),


    # Sensing
    "sensing_askandwait": ("ask {} and wait", ["QUESTION"]),
    "sensing_setdragmode": ("set drag mode [{} v]", [["DRAG_MODE", FIELDS]]),
    "sensing_resettimer": ("reset timer", []),


    # Variables
    "data_variable": ("({})", ["VARIABLE"]),
    "data_setvariableto": ("set [{} v] to {}", [["VARIABLE", FIELDS], "VALUE"]),
    "data_changevariableby": ("change [{} v] by {}", [["VARIABLE", FIELDS], "VALUE"]),
    "data_hidevariable": ("hide variable [{} v]", [["VARIABLE", FIELDS]]),
    "data_showvariable": ("show variable [{} v]", [["VARIABLE", FIELDS]]),

    # Lists
    "data_listcontents": ("<[{} v] contains {} >", [["LIST", FIELDS], "ITEM"]),
    "data_addtolist": ("add {} to [{} v]", ["ITEM", ["LIST", FIELDS]]),
    "data_deleteoflist": ("delete {} of [{} v]", ["INDEX", ["LIST", FIELDS]]),
    "data_deletealloflist": ("delete all of [{} v]", [["LIST", FIELDS]]),
    "data_insertatlist": ("insert {} at {} of [{} v] ", ["ITEM", "INDEX", ["LIST", FIELDS]]),
    "data_replaceitemoflist": ("replace item {} of [{} v] with {}", ["INDEX", ["LIST", FIELDS], "ITEM"]),
    "data_hidelist": ("show list [{} v]", [["LIST", FIELDS]]),
    "data_showlist": ("hide list [{} v]", [["LIST", FIELDS]]),

    # My Blocks
    "procedures_definition": ("define {}", ["custom_block"]),
    "procedures_call": custom_block,

    # Pen
    "pen_clear": ("erase all", []),
    "pen_stamp": ("stamp", []),
    "pen_penDown": ("pen down", []),
    "pen_penUp": ("pen up", []),
    "pen_setPenColorToColor": ("set pen color to {}", ["COLOR"]),
    "pen_changePenColorParamBy": ("change pen ({} v) by {}", ["COLOR_PARAM", "VALUE"]),
    "pen_setPenColorParamTo": ("set pen ({} v) to {}", ["COLOR_PARAM", "VALUE"]),
    "pen_changePenSizeBy": ("change pen size by {}", ["SIZE"]),
    "pen_setPenSizeTo": ("set pen size to {}", ["SIZE"]),
    "pen_changePenHueBy": ("change pen color by {}", ["HUE"]),

    # Music
    "music_playDrumForBeats": ("play drum ({} v) for {} beats", ["DRUM", "BEATS"]),
    "music_restForBeats": ("rest for {} beats", ["BEATS"]),
    "music_playNoteForBeats": ("play note ({}) for {} beats", ["NOTE", "BEATS"]), 
    "music_setInstrument": ("set instrument to ({} v)", ["INSTRUMENT"]),
    "music_setTempo": ("set tempo to {}", ["TEMPO"]),
    "music_changeTempo": ("change tempo by {}", ["TEMPO"]),

    # Video
    "videoSensing_whenMotionGreaterThan": ("when video motion > {}", ["REFERENCE"]),
    "videoSensing_videoToggle": ("turn video ({} v)", ["VIDEO_STATE"]),
    "videoSensing_setVideoTransparency": ("set video transparency to {}", ["TRANSPARENCY"]),

    # Text to Speech
    "text2speech_speakAndWait": ("speak {}:tts", ["WORDS"]),
    "text2speech_setVoice": ("set voice to ({} v):tts", ["VOICE"]),
    "text2speech_setLanguage": ("set language to ({} v):tts", ["LANGUAGE"]),
}

INPUTS = {
    # Motion
    "motion_goto_menu": ("({} v)", [["TO", FIELDS]]),
    "motion_glideto_menu": ("({} v)", [["TO", FIELDS]]),
    "motion_pointtowards_menu": ("({} v)", [["TOWARDS", FIELDS]]),
    "motion_xposition": ("(x position)", []),
    "motion_yposition": ("(y position)", []),
    "motion_direction": ("(direction)", []),

    # Looks
    "looks_costume": ("({} v)", [["COSTUME", {}]]),
    "looks_backdrops": ("({} v)", [["BACKDROP", {}]]),
    "looks_costumenumbername": ("(costume [{} v])", [["NUMBER_NAME", {}]]),
    "looks_backdropnumbername": ("(backdrop [{} v])", [["NUMBER_NAME", {}]]),
    "looks_size": ("(size)", []),

    # Sound
    "sound_sounds_menu": ("({} v)", [["SOUND_MENU", {"attrs": ["preservecase"]}]]),
    "sound_volume": ("(volume)", []),

    # Control -- check this block
    "control_create_clone_of_menu": ("({} v)", [["CLONE_OPTION", FIELDS]]),

    # Sensing
    "sensing_mousedown": ("<mouse down?>", []),
    "sensing_touchingobject": ("<touching [{} v]?>", ["TOUCHINGOBJECTMENU"]),
    "sensing_touchingobjectmenu": ("{}", [["TOUCHINGOBJECTMENU", FIELDS]]),
    "sensing_touchingcolor": ("<touching color {}?>", ["COLOR"]),
    "sensing_coloristouchingcolor": ("<color {} is touching {}?>", ["COLOR", "COLOR2"]),
    "sensing_distanceto": ("(distance to [{} v])", ["DISTANCETOMENU"]),
    "sensing_distancetomenu": ("{}", [["DISTANCETOMENU", FIELDS]]),
    "sensing_keypressed": ("<key [{} v] pressed?>", ["KEY_OPTION"]),
    "sensing_keyoptions": ("{}", [["KEY_OPTION", FIELDS]]),
    "sensing_mousex": ("(mouse x)", []),
    "sensing_mousey": ("(mouse y)", []),
    "sensing_loudness": ("(loudness)", []),
    "sensing_timer": ("(timer)", []),
    "sensing_of": ("([{} v] of {})", [["PROPERTY", FIELDS], "OBJECT"]),
    "sensing_of_object_menu": ("[{} v]", [["OBJECT", FIELDS]]),
    "sensing_current": ("(current [{} v])", [["CURRENTMENU", FIELDS]]),
    "sensing_dayssince2000": ("(days since 2000)", []),
    "sensing_username": ("(username)", []),
    "sensing_answer": ("(answer)", []),

    # Operators
    "operator_add": ("({} + {})", ["NUM1", "NUM2"]),
    "operator_subtract": ("({} - {})", ["NUM1", "NUM2"]),
    "operator_equals": ("<{} = {}>", ["OPERAND1", "OPERAND2"]),
    "operator_random": ("(pick random {} to {})", ["FROM", "TO"]),
    "operator_gt": ("<{} > {}>", ["OPERAND1", "OPERAND2"]),
    "operator_lt": ("<{} < {}>", ["OPERAND1", "OPERAND2"]),
    "operator_and": ("<{} and {}>", ["OPERAND1", "OPERAND2"]),
    "operator_round": ("(round {})", ["NUM"]),
    "operator_mathop": ("([{} v] of {} )", [["OPERATOR", FIELDS], "NUM"]),
    "operator_or": ("<{} or {}>", ["OPERAND1", "OPERAND2"]),
    "operator_not": ("<not {}>", ["OPERAND"]),
    "operator_join": ("(join {} {})", ["STRING1", "STRING2"]),
    "operator_letter_of": ("(letter {} of {}", ["LETTER", "STRING"]),
    "operator_length": ("(length of {})", ["STRING"]),
    "operator_contains": ("< {} contains {}?>", ["STRING1", "STRING2"]),
    "operator_mod": ("({} mod {})", ["NUM1", "NUM2"]),
    "operator_multiply": ("({} * {})", ["NUM1", "NUM2"]),
    "operator_divide": ("({} / {})", ["NUM1", "NUM2"]),

    # List
    "data_itemoflist": ("(item {} of [{} v])", ["INDEX", ["LIST", FIELDS]]),
    "data_itemnumoflist": ("(item # of {} in [{} v])", ["ITEM", ["LIST", FIELDS]]),
    "data_lengthoflist": ("(length of [{} v])", [["LIST", FIELDS]]),
    "data_listcontainsitem": ("<[{} v] contains {}?>", [["LIST", FIELDS], "ITEM"]),

    # My Blocks
    "procedures_prototype": custom_block,
    "argument_reporter_boolean": ("<{}>", [["VALUE", {}]]),
    "argument_reporter_string_number": ("({})", [["VALUE", {}]]),

    # Pen
    "pen_menu_colorParam": ("{}", [["colorParam", FIELDS]]),

    # Music
    "music_menu_DRUM": ("{}", [["DRUM", FIELDS]]),
    "note": ("{}", [["NOTE", FIELDS]]),
    "music_menu_INSTRUMENT": ("{}", [["INSTRUMENT", FIELDS]]),
    "music_getTempo": ("(tempo)", []),

    # Video
    "videoSensing_menu_VIDEO_STATE": ("{}", [["VIDEO_STATE", FIELDS]]),
    "videoSensing_videoOn": ("(video ({} v) on ({} v))", ["ATTRIBUTE", "SUBJECT"]),
    "videoSensing_menu_ATTRIBUTE": ("{}", [["ATTRIBUTE", FIELDS]]),
    "videoSensing_menu_SUBJECT": ("{}", [["SUBJECT", FIELDS]]),

    # Text to Speech
    "text2speech_menu_voices": ("{}", [["voices", FIELDS]]),
    "text2speech_menu_languages": ("{}", [["languages", FIELDS]]),

    # Translate
    "translate_menu_languages": ("{}", [["languages", FIELDS]]),
    "translate_getViewerLanguage": ("(language::translate)", []),
    "translate_getTranslate": ("(translate {} to ({} v)::translate)", ["WORDS", "LANGUAGE"]),
}


def get_project_from_url(url):
    """Return project data for a URL."""

    # Validate project URL
    match = re.search("scratch.mit.edu/projects/(\\d+)/", url)
    if match is None:
        return None
    project_id = match.group(1)

    # Query for project JSON
    res = requests.get(f"https://projects.scratch.mit.edu/{project_id}")
    return res.json()


def generate_scratchblocks(project):
    """Generates all blocks in a project.
    
    Args:
        project (dict): the Scratch project to process.
        surrounding (list): list of blocks allowed to added
    Returns:
        A list of scripts in the project that can be turned into text.
    """
    targets = project["targets"]
    scripts = []

    # Check each target for a new script
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


def generate_script(block_id, blocks, block_ids=None, find_block=True):
    """Generates a script.
    
    Args:
        block_id (str): the start block.
        blocks (array-like): the list of blocks within this target.
        block_ids (array-like) (optional): the set of block IDs that are allowed to be added.
            If not set, then all blocks are allowed.
        find_block (bool) (optional): whether to find the closest parent block
            that can form a script, as when a script uses input blocks.
            Defaults to True.
    
    Returns:
        A dictionary with the nesting of this script as appropriate.
    """

    # If we just want everything
    if block_ids is None:
        block_ids = list(blocks)

    # If the current block isn't allowed, we're not adding it.
    if block_id not in block_ids:
        return None

    block = blocks[block_id]
    opcode = block["opcode"]

    # Format current block
    if opcode in BLOCKS:
        block_structure = BLOCKS[opcode]
        if callable(block_structure):
            name, inputs = block_structure(block)
        else:
            name, inputs = block_structure
        label = format_block(block_id, blocks, name, inputs)
        script = {
            "label": label
        }

    # By default, try to get the closest parent block that can start a script
    elif opcode in INPUTS and block["parent"] is not None and find_block:
        block_ids.append(block["parent"])
        return generate_script(block["parent"], blocks, block_ids)

    else:
        raise Exception(f"MISSING handler for {opcode}")

    # Handle next block
    next_block = block["next"]
    if next_block in block_ids:
        script["next"] = generate_script(next_block, blocks, block_ids)

    # Handle substacks
    if "SUBSTACK" in block["inputs"]:
        substack_id = block["inputs"]["SUBSTACK"][1]
        script["substack"] = generate_script(substack_id, blocks, block_ids)

    if "SUBSTACK2" in block["inputs"]:
        substack_id = block["inputs"]["SUBSTACK2"][1]
        script["substack2"] = generate_script(substack_id, blocks, block_ids)

    return script


def generate_input(input_block, blocks):
    """Generate input based on the value of INPUTS for a block."""
    main_input = input_block[1]

    # Handle inputs that are references to other blocks
    if isinstance(main_input, str):
        return generate_input_block(main_input, blocks)

    # Handle inputs that do not refer to other blocks
    elif isinstance(main_input, list):
        input_type = main_input[0]
        input_value = main_input[1]
        if input_type in [4, 5, 6, 7, 8, 9, 12, 13]:  # number, variable
            return f"({input_value})"
        elif input_type == 10:  # string
            return f"[{input_value}]"
        elif input_type == 11: # broadcast
            return f"({input_value} v)"
        elif input_type == "BOOL":
            return f"<{input_value}>"

    else:
        raise Exception(f"Missing handler for input type {type(main_input)}")


def generate_input_block(block_id, blocks):
    """Generate the value of an input reporter."""
    block = blocks[block_id]
    opcode = block["opcode"]
    if opcode in INPUTS:
        block_structure = INPUTS[opcode]
        if callable(block_structure):
            name, inputs = block_structure(block)
        else:
            name, inputs = block_structure
        input_block = format_block(block_id, blocks, name, inputs)
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
            args.append(get_field_name(mapping, block, field_name))
        else:
            raise Exception(f"unsupported block type {type(input_name)}")
    return name.format(*args)


def get_field_name(mapping, block, field_name):
    value = str(block["fields"][field_name][0])
    if mapping.get(value):
        return mapping.get(value)
    elif "preservecase" in mapping.get("attrs", []):
        return value
    else:
        return value.lower()


def block_string(scripts):
    def indent_string(block, indent):
        # If block isn't allowed, we just ignore it.
        if block is None:
            return ""

        output = " " * indent + block["label"] + "\n"

        # Print substack
        if "substack" in block:
            output += indent_string(block["substack"], indent + 4)
            if "substack2" in block:
                output += " " * indent + "else\n"
                output += indent_string(block["substack2"], indent + 4)
            output += " " * indent + "end\n"

        # Print next block
        if "next" in block:
            output += indent_string(block["next"], indent)

        return output

    output = ""
    for script in scripts:
        output += indent_string(script, 0)
        output += "\n"
    return output


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
    print("data", data)
    # Generate blocks
    blocks = generate_scratchblocks(data)
    text = block_string(blocks)
    print(text)
    if OPEN_IN_BROWSER:
        data = quote(text)
        url = f"http://scratchblocks.github.io/#?style=scratch3&script={data}"
        webbrowser.open(url)


if __name__ == "__main__":
    main()
