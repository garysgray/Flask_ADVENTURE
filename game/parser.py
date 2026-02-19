class Parser:
    def __init__(self, controller):
        self.ctrl = controller

    def parse(self, user_input):
        cmd_info = {}
        split_input = user_input.split()

        if len(split_input) == 1:
            cmd_info["CMD"] = split_input[-1]
            cmd_info["OBJ"] = "NO_ITEM_IN_CMD"
        elif "drop" in split_input:
            cmd_info["CMD"] = "drop"
            cmd_info["OBJ"] = split_input
        elif "pickup" in split_input or "get" in split_input:
            cmd_info["CMD"] = "pickup"
            cmd_info["OBJ"] = split_input
        elif "help" in split_input:
            cmd_info["CMD"] = "help"
            cmd_info["OBJ"] = "NO_ITEMS_FOR_HELP_WIP"
        elif "look" in split_input:
            cmd_info["CMD"] = "look"
            cmd_info["OBJ"] = split_input
        elif "go" in split_input or "move" in split_input:
            cmd_info["CMD"] = "move"
            cmd_info["OBJ"] = split_input
        elif "use" in split_input:
            cmd_info["CMD"] = "use"
            if "with" in split_input:
                use_index = split_input.index("use")
                with_index = split_input.index("with")
                cmd_info["OBJ"] = {
                    'item': split_input[use_index + 1],
                    'target': split_input[with_index + 1]
                }
            else:
                cmd_info["OBJ"] = split_input
        elif "changedesc" in split_input:
            cmd_info["CMD"] = "changedesc"
            cmd_info["OBJ"] = split_input
        else:
            cmd_info["CMD"] = user_input
            cmd_info["OBJ"] = "NO_ITEM"

        return cmd_info