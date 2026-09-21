import re


class Parser:
    """
    Classic Adventure-grade text parser engine.
    """

    DIRECTIONS = {'north', 'south', 'east', 'west', 'up', 'down', 'portal'}

    DIRECTION_SHORTHAND = {
        'n': 'north',
        's': 'south',
        'e': 'east',
        'w': 'west',
        'u': 'up',
        'd': 'down',
        'p': 'portal',
    }

    MOVE_VERBS = {
        'go', 'move', 'walk', 'run', 'head', 'proceed', 'travel',
        'climb', 'step', 'navigate', 'wander', 'enter'
    }

    PICKUP_VERBS = {
        'pick up', 'pickup', 'take', 'get', 'grab', 'collect',
        'retrieve', 'acquire', 'pick', 'lift', 'gather'
    }

    DROP_VERBS = {
        'drop', 'put down', 'discard', 'leave', 'toss', 'dump',
        'throw away', 'set down', 'place down'
    }

    LOOK_VERBS = {
        'look at', 'look inside', 'look in', 'look into', 'look around',
        'look', 'examine', 'inspect', 'peer at', 'check', 'view',
        'study', 'x', 'l', 'search', 'observe'
    }

    READ_VERBS = {
        'read', 'peruse'
    }

    INVENTORY_VERBS = {
        'inventory', 'inv', 'i', 'items', 'carrying', 'pockets', 'check inventory'
    }

    JOURNAL_VERBS = {
        'journal', 'log', 'notes', 'field notes'
    }

    HELP_VERBS = {
        'help', 'commands', 'instructions', 'info', '?'
    }

    WAIT_VERBS = {
        'wait', 'z', 'rest', 'pause', 'wait a turn'
    }

    CORE_INTERACTION_VERBS = {
        'use', 'activate', 'turn on', 'switch on', 'press', 'push',
        'pull', 'trigger', 'operate', 'apply', 'interact with', 'interact',
        'engage', 'fire', 'work', 'open', 'unlock', 'insert', 'put', 'place',
        'combine', 'drink', 'eat', 'sip', 'turn', 'flip', 'close', 'shut', 'pack'
    }

    LEADING_ARTICLES = {'the', 'a', 'an', 'some', 'my', 'that', 'this'}
    FILLER_WORDS     = {'please', 'carefully', 'quickly', 'gently', 'slowly'}

    CONNECTORS_INSTRUMENT = {'with', 'using', 'by'}
    CONNECTORS_LOCATIVE   = {'on', 'onto', 'in', 'into', 'to', 'against', 'through'}
    CONNECTORS_AND        = {'and'}
    ALL_CONNECTORS        = CONNECTORS_INSTRUMENT | CONNECTORS_LOCATIVE | CONNECTORS_AND

    PHRASAL_VERB_PREFIXES = {'listen', 'look', 'peer', 'talk', 'speak', 'adhere', 'check'}

    def __init__(self, controller=None, item_aliases=None, target_aliases=None, custom_verbs=None, custom_solo_verbs=None):
        self.ctrl = controller
        self._item_aliases = item_aliases or {}
        self._target_aliases = target_aliases or {}
        self._custom_verbs = custom_verbs or []
        self._custom_solo_verbs = custom_solo_verbs or {}

    def _get_action_verbs(self):
        verbs = set(self.CORE_INTERACTION_VERBS)

        custom = getattr(self.ctrl.map, 'custom_verbs', {}) if self.ctrl and hasattr(self.ctrl, 'map') else self._custom_verbs
        if isinstance(custom, dict):
            for v_list in custom.values():
                if isinstance(v_list, (list, set, tuple)):
                    verbs.update(v_list)
        elif isinstance(custom, (list, set, tuple)):
            verbs.update(custom)

        for v in self._custom_solo_verbs.keys():
            verbs.add(v)

        if self.ctrl and hasattr(self.ctrl, 'map'):
            item_recipes = getattr(self.ctrl.map, 'item_recipes', {})
            for item_data in item_recipes.values():
                if isinstance(item_data, dict):
                    for kw in item_data.get('action_keywords', []):
                        if len(kw) > 1:
                            verbs.add(kw)

        return verbs

    def _get_entity_display_name(self, entity_id):
        item_recipes = getattr(self.ctrl.map, 'item_recipes', {})
        if entity_id in item_recipes:
            data = item_recipes[entity_id]
            if isinstance(data, dict) and 'display_name' in data:
                return data['display_name']
        return entity_id.replace('_', ' ')

    def _format_ambiguity_message(self, candidates):
        names = [self._get_entity_display_name(c) for c in sorted(candidates)]
        if len(names) == 2:
            return f"Which one do you mean: {names[0]} or {names[1]}?"
        if len(names) > 2:
            return f"Which one do you mean: {', '.join(names[:-1])} or {names[-1]}?"
        return "Which one do you mean?"

    def normalize(self, text):
        if not text:
            return ""
        s = text.lower().strip()
        if s in {'?', 'help', 'i', 'x', 'l', 'inv'}:
            return s
        s = re.sub(r'^[^\w\s]+|[^\w\s]+$', '', s)
        s = re.sub(r'[,;!?"]+', ' ', s)
        s = re.sub(r'\s+', ' ', s).strip()

        for polite in ('please ', 'could you ', 'would you ', 'can you '):
            if s.startswith(polite):
                s = s[len(polite):].strip()

        return s

    def _get_entity_vocabulary(self):
        vocab = {}
        ambiguous_vocab = {}

        def register(alias, entity_id):
            cleaned = self.normalize(alias)
            if not cleaned:
                return
            if cleaned in vocab and vocab[cleaned] != entity_id:
                existing = vocab[cleaned]
                if cleaned not in ambiguous_vocab:
                    ambiguous_vocab[cleaned] = {existing, entity_id}
                else:
                    ambiguous_vocab[cleaned].add(entity_id)
            else:
                vocab[cleaned] = entity_id

        if self.ctrl and hasattr(self.ctrl, 'map'):
            item_recipes = getattr(self.ctrl.map, 'item_recipes', {})
            for item_name, data in item_recipes.items():
                register(item_name, item_name)
                register(item_name.replace('_', ' '), item_name)
                for alias in data.get('aliases', []):
                    register(alias, item_name)

        for item_name, aliases in self._item_aliases.items():
            register(item_name, item_name)
            register(item_name.replace('_', ' '), item_name)
            for alias in aliases:
                register(alias, item_name)

        target_aliases = getattr(self.ctrl.map, 'target_aliases', {}) if self.ctrl and hasattr(self.ctrl, 'map') else self._target_aliases
        for target_name, aliases in target_aliases.items():
            register(target_name, target_name)
            for alias in aliases:
                register(alias, target_name)

        if self.ctrl and hasattr(self.ctrl, 'map'):
            for event in getattr(self.ctrl.map, 'event_recipes', []):
                if hasattr(event, 'target') and event.target:
                    t = event.target
                    register(t, t)
                    register(t.replace('_', ' '), t)

            room = self.ctrl.get_room()
            if room:
                # Also register fixtures in the current room
                if hasattr(room, 'fixtures') and room.fixtures:
                    for fix_name, fixture in room.fixtures.items():
                        register(fix_name, fix_name)
                        register(fix_name.replace('_', ' '), fix_name)
                        if hasattr(fixture, 'display_name') and fixture.display_name:
                            register(fixture.display_name, fix_name)

                if hasattr(room, 'description'):
                    em_targets = re.findall(r'<em>(.*?)</em>', room.description)
                    for em in em_targets:
                        register(em, em)

        return vocab, ambiguous_vocab

    def _strip_noise_words(self, phrase):
        tokens = phrase.split()
        while tokens and (tokens[0] in self.LEADING_ARTICLES or tokens[0] in self.FILLER_WORDS or tokens[0] == 'at'):
            tokens.pop(0)
        while tokens and tokens[-1] in self.FILLER_WORDS:
            tokens.pop()
        return " ".join(tokens)

    def _resolve_entity(self, phrase, vocab=None, ambiguous_vocab=None):
        if vocab is None or ambiguous_vocab is None:
            vocab, ambiguous_vocab = self._get_entity_vocabulary()

        cleaned = self._strip_noise_words(phrase)
        if not cleaned:
            return None, False, None

        if cleaned in ambiguous_vocab:
            entities = ambiguous_vocab[cleaned]
            in_scope = [e for e in entities if self._is_in_scope(e)]
            if len(in_scope) == 1:
                return in_scope[0], False, None
            return None, True, self._format_ambiguity_message(entities)

        if cleaned in vocab:
            return vocab[cleaned], False, None

        sorted_keys = sorted(vocab.keys(), key=lambda k: len(k), reverse=True)

        candidates = set()
        for key in sorted_keys:
            if key == cleaned:
                candidates.add(vocab[key])
            elif " " + key + " " in " " + cleaned + " ":
                candidates.add(vocab[key])

        if len(candidates) == 1:
            return next(iter(candidates)), False, None
        elif len(candidates) > 1:
            in_inventory = [c for c in candidates if self._is_in_player_inventory(c)]
            in_room = [c for c in candidates if self._is_in_room_inventory(c)]

            if len(in_inventory) == 1:
                return in_inventory[0], False, None
            if len(in_room) == 1:
                return in_room[0], False, None

            return None, True, self._format_ambiguity_message(candidates)

        for key in sorted_keys:
            if cleaned.endswith(" " + key) or cleaned.startswith(key + " "):
                return vocab[key], False, None

        return cleaned, False, None

    def _is_in_player_inventory(self, item_name):
        return any(i.name == item_name for i in getattr(self.ctrl.player, 'inventory', []))

    def _is_in_room_inventory(self, item_name):
        room = self.ctrl.get_room()
        if room and hasattr(room, 'inventory'):
            return any(i.name == item_name for i in room.inventory)
        return False

    def _is_in_scope(self, item_name):
        room = self.ctrl.get_room()
        if room and hasattr(room, 'fixtures') and item_name in room.fixtures:
            return True
        return self._is_in_player_inventory(item_name) or self._is_in_room_inventory(item_name)

    def _match_direction(self, text):
        text = text.strip()
        if text in self.DIRECTIONS:
            return text
        if text in self.DIRECTION_SHORTHAND:
            return self.DIRECTION_SHORTHAND[text]
        if text in {'portal', 'the portal', 'into portal', 'into the portal', 'through portal', 'through the portal'}:
            return 'portal'
        if text in {'upstairs', 'up the stairs', 'the stairs up', 'ladder up'}:
            return 'up'
        if text in {'downstairs', 'down the stairs', 'the stairs down', 'ladder down'}:
            return 'down'
        return None

    def _parse_two_object_command(self, norm_text, vocab, ambiguous_vocab):
        words = norm_text.split()

        connector = None
        conn_idx = -1

        for i in range(1, len(words)):
            w = words[i]
            if w in self.ALL_CONNECTORS:
                if i == 1 and words[0] in self.PHRASAL_VERB_PREFIXES:
                    continue
                connector = w
                conn_idx = i
                break

        if not connector or conn_idx <= 0 or conn_idx >= len(words):
            return None

        left_words  = words[:conn_idx]
        right_words = words[conn_idx + 1:]

        all_action_verbs = self._get_action_verbs()
        lead_verb = None
        remaining_left = left_words

        for v in sorted(all_action_verbs, key=lambda x: len(x), reverse=True):
            v_words = v.split()
            if left_words[:len(v_words)] == v_words:
                lead_verb = v
                remaining_left = left_words[len(v_words):]
                break

        if not remaining_left:
            return None

        if not right_words:
            item_phrase = self._strip_noise_words(" ".join(remaining_left))
            return {"CMD": "respond", "OBJ": f"What do you want to use the {item_phrase} on?"}

        left_phrase  = " ".join(remaining_left).strip()
        right_phrase = " ".join(right_words).strip()

        left_entity, left_ambig, left_msg   = self._resolve_entity(left_phrase, vocab, ambiguous_vocab)
        if left_ambig:
            return {"CMD": "respond", "OBJ": left_msg}

        right_entity, right_ambig, right_msg = self._resolve_entity(right_phrase, vocab, ambiguous_vocab)
        if right_ambig:
            return {"CMD": "respond", "OBJ": right_msg}

        item, target = self._align_item_and_target(left_entity, right_entity, connector, lead_verb)

        result_obj = {"item": item, "target": target}
        if lead_verb:
            result_obj["action"] = lead_verb

        return {"CMD": "use", "OBJ": result_obj}

    def _align_item_and_target(self, ent1, ent2, connector, lead_verb):
        if connector in self.CONNECTORS_INSTRUMENT:
            if lead_verb in {'combine', 'assemble', 'join', 'merge', 'fit', 'piece together', 'use'}:
                return ent1, ent2
            return ent2, ent1
        else:
            return ent1, ent2

    def _check_solo_keywords(self, norm_text, vocab, ambiguous_vocab):
        words = norm_text.split()
        item_recipes = getattr(self.ctrl.map, 'item_recipes', {}) if self.ctrl and hasattr(self.ctrl, 'map') else {}

        for item_name, data in item_recipes.items():
            solo_keywords = data.get('solo_keywords', [])
            for kw in solo_keywords:
                if kw in self.LOOK_VERBS or kw in self.PICKUP_VERBS or kw in self.DROP_VERBS:
                    continue
                if kw in words or norm_text.startswith(kw + " "):
                    phrase = norm_text
                    if kw in words:
                        w_copy = [w for w in words if w != kw and w not in self.LEADING_ARTICLES and w != 'to']
                        phrase = " ".join(w_copy)
                    resolved, ambig, msg = self._resolve_entity(phrase, vocab, ambiguous_vocab)
                    if ambig:
                        return {"CMD": "respond", "OBJ": msg}
                    if resolved == item_name or any(a in norm_text for a in data.get('aliases', [])):
                        return {"CMD": "use", "OBJ": [item_name]}

        for verb, target_items in self._custom_solo_verbs.items():
            if norm_text.startswith(verb + " ") or norm_text == verb:
                noun_phrase = norm_text[len(verb):].strip()
                cleaned_words = [w for w in noun_phrase.split() if w not in self.LEADING_ARTICLES and w != 'to']
                target_noun = " ".join(cleaned_words)
                resolved, ambig, msg = self._resolve_entity(target_noun, vocab, ambiguous_vocab)
                if resolved:
                    return {"CMD": "use", "OBJ": {"item": resolved, "action": verb}}

        return None

    def parse(self, user_input):
        norm = self.normalize(user_input)
        if not norm:
            return {"CMD": "", "OBJ": ""}

        words = norm.split()
        first_word = words[0]

        dir_match = self._match_direction(norm)
        if dir_match:
            return {"CMD": "move", "OBJ": dir_match}

        if norm in {
            "use portal", "enter portal", "take portal", "step into portal",
            "step through portal", "go into portal", "go through portal",
            "enter the portal", "step into the portal", "step through the portal",
            "go into the portal", "go through the portal"
        }:
            return {"CMD": "move", "OBJ": "portal"}

        if norm in {"climb ladder", "take stairs", "use stairs", "go upstairs"}:
            return {"CMD": "move", "OBJ": "up"}

        if norm in {"climb down ladder", "go downstairs"}:
            return {"CMD": "move", "OBJ": "down"}

        if len(words) == 1:
            shorthand = self.DIRECTION_SHORTHAND.get(norm)
            if shorthand:
                return {"CMD": "move", "OBJ": shorthand}
            if norm in self.DIRECTIONS:
                return {"CMD": "move", "OBJ": norm}

        if first_word in self.MOVE_VERBS:
            if len(words) == 1:
                return {"CMD": "respond", "OBJ": "Which direction do you want to go?"}
            target_dir = None
            for w in words[1:]:
                d = self._match_direction(w)
                if d:
                    target_dir = d
                    break
            if target_dir:
                return {"CMD": "move", "OBJ": target_dir}
            return {"CMD": "respond", "OBJ": f"You can't go {' '.join(words[1:])}."}

        if norm in self.HELP_VERBS:
            return {"CMD": "help", "OBJ": ""}

        if norm in self.INVENTORY_VERBS:
            return {"CMD": "inv", "OBJ": ""}

        if norm in self.JOURNAL_VERBS or norm == "read journal" or norm == "check journal":
            return {"CMD": "journal", "OBJ": ""}

        if norm in self.WAIT_VERBS:
            return {"CMD": "wait", "OBJ": ""}

        if first_word == "changedesc":
            return {"CMD": "changedesc", "OBJ": words}

        vocab, ambiguous_vocab = self._get_entity_vocabulary()

        two_obj = self._parse_two_object_command(norm, vocab, ambiguous_vocab)
        if two_obj is not None:
            return two_obj

        solo_cmd = self._check_solo_keywords(norm, vocab, ambiguous_vocab)
        if solo_cmd is not None:
            return solo_cmd

        if norm in {'look', 'l', 'look around', 'look room', 'examine room'}:
            return {"CMD": "look", "OBJ": ""}

        for v in sorted(self.LOOK_VERBS, key=lambda x: len(x), reverse=True):
            if norm == v:
                return {"CMD": "respond", "OBJ": "Look at what?"}
            if norm.startswith(v + " "):
                noun_phrase = norm[len(v):].strip()
                entity, ambig, msg = self._resolve_entity(noun_phrase, vocab, ambiguous_vocab)
                if ambig:
                    return {"CMD": "respond", "OBJ": msg}
                return {"CMD": "look", "OBJ": entity}

        for v in sorted(self.PICKUP_VERBS, key=lambda x: len(x), reverse=True):
            if norm == v:
                return {"CMD": "respond", "OBJ": "Take what?"}
            if norm.startswith(v + " "):
                noun_phrase = norm[len(v):].strip()
                entity, ambig, msg = self._resolve_entity(noun_phrase, vocab, ambiguous_vocab)
                if ambig:
                    return {"CMD": "respond", "OBJ": msg}
                return {"CMD": "pickup", "OBJ": entity}

        for v in sorted(self.DROP_VERBS, key=lambda x: len(x), reverse=True):
            if norm == v:
                return {"CMD": "respond", "OBJ": "Drop what?"}
            if norm.startswith(v + " "):
                noun_phrase = norm[len(v):].strip()
                entity, ambig, msg = self._resolve_entity(noun_phrase, vocab, ambiguous_vocab)
                if ambig:
                    return {"CMD": "respond", "OBJ": msg}
                return {"CMD": "drop", "OBJ": entity}

        for v in sorted(self.READ_VERBS, key=lambda x: len(x), reverse=True):
            if norm == v:
                return {"CMD": "respond", "OBJ": "Read what?"}
            if norm.startswith(v + " "):
                noun_phrase = norm[len(v):].strip()
                if noun_phrase in {"journal", "log", "notes"}:
                    return {"CMD": "journal", "OBJ": ""}
                entity, ambig, msg = self._resolve_entity(noun_phrase, vocab, ambiguous_vocab)
                if ambig:
                    return {"CMD": "respond", "OBJ": msg}
                target_entity = entity if entity else noun_phrase.replace(' ', '_')
                return {"CMD": "read", "OBJ": target_entity}

        action_verbs = self._get_action_verbs()
        for v in sorted(action_verbs, key=lambda x: len(x), reverse=True):
            if norm == v:
                v_title = v.capitalize()
                return {"CMD": "respond", "OBJ": f"{v_title} what?"}
            if norm.startswith(v + " "):
                noun_phrase = norm[len(v):].strip()
                entity, ambig, msg = self._resolve_entity(noun_phrase, vocab, ambiguous_vocab)
                if ambig:
                    return {"CMD": "respond", "OBJ": msg}
                target_entity = entity if entity else noun_phrase.replace(' ', '_')
                if v == 'use':
                    return {"CMD": "use", "OBJ": [target_entity]}
                return {"CMD": "use", "OBJ": {"item": target_entity, "action": v}}

        entity, ambig, msg = self._resolve_entity(norm, vocab, ambiguous_vocab)
        if ambig:
            return {"CMD": "respond", "OBJ": msg}
        if entity and entity in vocab.values():
            return {"CMD": "look", "OBJ": entity}

        return {"CMD": norm, "OBJ": ""}
