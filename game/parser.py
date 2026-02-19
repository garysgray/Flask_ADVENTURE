
class Parser:
    DIRECTIONS = {'north', 'south', 'east', 'west', 'up', 'down'}
    MOVE_WORDS  = {'go', 'move', 'walk', 'run', 'head'}
    PICKUP_WORDS = {'get', 'pickup', 'take', 'grab'}

    def __init__(self, controller):
        self.ctrl = controller

    def parse(self, user_input):
        words = user_input.lower().strip().split()
        if not words:
            return {"CMD": "", "OBJ": ""}

        # Single direction word
        if len(words) == 1 and words[0] in self.DIRECTIONS:
            return {"CMD": "move", "OBJ": words}

        # Move command
        if words[0] in self.MOVE_WORDS or any(w in self.DIRECTIONS for w in words):
            return {"CMD": "move", "OBJ": words}

        # Use with
        if "use" in words and "with" in words:
            use_i = words.index("use")
            with_i = words.index("with")
            return {"CMD": "use", "OBJ": {
                "item": words[use_i + 1],
                "target": words[with_i + 1]
            }}

        # Keyword commands
        for word in words:
            if word in self.PICKUP_WORDS:
                return {"CMD": "pickup", "OBJ": words}
            if word == "drop":
                return {"CMD": "drop", "OBJ": words}
            if word == "look":
                return {"CMD": "look", "OBJ": words}
            if word == "use":
                return {"CMD": "use", "OBJ": words}
            if word == "help":
                return {"CMD": "help", "OBJ": ""}
            if word == "changedesc":
                return {"CMD": "changedesc", "OBJ": words}

        return {"CMD": user_input, "OBJ": ""}