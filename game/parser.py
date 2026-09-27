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
    CONNECTORS_LOCATIVE   = {'on', 'onto', 'in', 'into', 'to', 'against', 'through', 'over', 'across'}
    CONNECTORS_AND        = {'and'}
    ALL_CONNECTORS        = CONNECTORS_INSTRUMENT | CONNECTORS_LOCATIVE | CONNECTORS_AND

    PHRASAL_VERB_PREFIXES = {'listen', 'look', 'peer', 'talk', 'speak', 'adhere', 'check'}

    TRANSIT_VERBS = MOVE_VERBS | {'take', 'use'}
    TRANSIT_PREPOSITIONS = {'through', 'into', 'in', 'to', 'onto', 'on', 'at', 'across'}
    STAIRS_WORDS = {'stairs', 'ladder', 'steps', 'staircase', 'stairway'}
    UP_WORDS = {'up', 'upstairs'}
    DOWN_WORDS = {'down', 'downstairs'}

    def __init__(self, controller=None, item_aliases=None, target_aliases=None, custom_verbs=None, custom_solo_verbs=None):
        self.ctrl = controller
        self._item_aliases = item_aliases or {}
        self._target_aliases = target_aliases or {}
        self._custom_verbs = custom_verbs or []
        self._custom_solo_verbs = custom_solo_verbs or {}
        self.pending_disambiguation = None
        self._last_ambiguity_candidates = []

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

        if s.startswith('do '):
            s = s[3:].strip()

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
        while tokens and (tokens[0] in self.LEADING_ARTICLES or tokens[0] in self.FILLER_WORDS or tokens[0] == 'at' or tokens[0] in self.CONNECTORS_LOCATIVE):
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
            cands = sorted(in_scope if in_scope else entities)
            self._last_ambiguity_candidates = list(cands)
            return None, True, self._format_ambiguity_message(cands)

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

            cands = sorted(candidates)
            self._last_ambiguity_candidates = list(cands)
            return None, True, self._format_ambiguity_message(cands)

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

    def _resolve_stairs_direction(self):
        room = self.ctrl.get_room() if self.ctrl and hasattr(self.ctrl, 'get_room') else None
        if room and hasattr(room, 'exits'):
            dest_keys = getattr(room, 'exit_destinations', {}) or {}
            room_exits = set(getattr(room, 'exits', []) or []) | set(dest_keys.keys())
            has_up = 'up' in room_exits
            has_down = 'down' in room_exits
            if has_up and not has_down:
                return {"CMD": "move", "OBJ": "up"}
            if has_down and not has_up:
                return {"CMD": "move", "OBJ": "down"}
        return {"CMD": "respond", "OBJ": "Do you want to go up or down?"}

    def _parse_transit(self, norm):
        words = norm.split()
        if not words:
            return None

        tokens = list(words)
        if tokens[0] in self.TRANSIT_VERBS:
            tokens.pop(0)

        if not tokens:
            return None

        filtered = [w for w in tokens if w not in self.TRANSIT_PREPOSITIONS and w not in self.LEADING_ARTICLES]
        if not filtered:
            return None

        if filtered == ['portal']:
            return {"CMD": "move", "OBJ": "portal"}

        all_vertical_vocab = self.STAIRS_WORDS | self.UP_WORDS | self.DOWN_WORDS
        if all(w in all_vertical_vocab for w in filtered):
            has_up = any(w in self.UP_WORDS for w in filtered)
            has_down = any(w in self.DOWN_WORDS for w in filtered)

            if has_up and not has_down:
                return {"CMD": "move", "OBJ": "up"}
            if has_down and not has_up:
                return {"CMD": "move", "OBJ": "down"}
            if has_up and has_down:
                return {"CMD": "respond", "OBJ": "Do you want to go up or down?"}

            if any(w in self.STAIRS_WORDS for w in filtered):
                return self._resolve_stairs_direction()

        return None

    def _entity_match_score(self, phrase, vocab, ambiguous_vocab):
        cleaned = self._strip_noise_words(phrase)
        if not cleaned:
            return 0
        if cleaned in vocab or cleaned.replace(' ', '_') in vocab or cleaned in ambiguous_vocab:
            return 2
        ent, ambig, _ = self._resolve_entity(phrase, vocab, ambiguous_vocab)
        if ambig:
            return 2
        if ent and (ent in vocab.values() or ent in vocab):
            return 1
        return 0

    def _parse_two_object_command(self, norm_text, vocab, ambiguous_vocab):
        words = norm_text.split()
        if len(words) < 2:
            return None

        all_action_verbs = self._get_action_verbs()
        lead_verb = None
        v_len = 0

        for v in sorted(all_action_verbs, key=lambda x: len(x), reverse=True):
            v_words = v.split()
            if words[:len(v_words)] == v_words:
                lead_verb = v
                v_len = len(v_words)
                break

        start_idx = max(1, v_len + 1)
        candidate_indices = []

        for i in range(start_idx, len(words)):
            w = words[i]
            if w in self.ALL_CONNECTORS:
                if i == 1 and words[0] in self.PHRASAL_VERB_PREFIXES:
                    continue
                candidate_indices.append(i)

        if not candidate_indices:
            return None

        best_candidate = None
        best_score = -999.0

        for idx in candidate_indices:
            left_words = words[v_len:idx]
            right_words = words[idx + 1:]

            if not left_words:
                continue

            left_phrase = " ".join(left_words).strip()
            score_left = self._entity_match_score(left_phrase, vocab, ambiguous_vocab)

            if right_words:
                right_phrase = " ".join(right_words).strip()
                score_right = self._entity_match_score(right_phrase, vocab, ambiguous_vocab)
                cand_score = score_left + score_right
            else:
                cand_score = score_left - 0.5

            if cand_score > best_score:
                best_score = cand_score
                best_candidate = idx

        if best_candidate is None:
            return None

        conn_idx = best_candidate
        connector = words[conn_idx]
        left_words = words[v_len:conn_idx]
        right_words = words[conn_idx + 1:]

        if not left_words:
            return None

        if not right_words:
            item_phrase = self._strip_noise_words(" ".join(left_words))
            return {"CMD": "respond", "OBJ": f"What do you want to use the {item_phrase} on?"}

        left_phrase  = " ".join(left_words).strip()
        right_phrase = " ".join(right_words).strip()

        left_entity, left_ambig, left_msg   = self._resolve_entity(left_phrase, vocab, ambiguous_vocab)
        if left_ambig:
            right_entity, right_ambig, _ = self._resolve_entity(right_phrase, vocab, ambiguous_vocab)
            self.pending_disambiguation = {
                "CMD": "use",
                "candidates": list(self._last_ambiguity_candidates),
                "two_obj": {
                    "slot": "left",
                    "fixed_entity": right_entity if not right_ambig else right_phrase,
                    "connector": connector,
                    "lead_verb": lead_verb
                }
            }
            return {"CMD": "respond", "OBJ": left_msg}

        right_entity, right_ambig, right_msg = self._resolve_entity(right_phrase, vocab, ambiguous_vocab)
        if right_ambig:
            self.pending_disambiguation = {
                "CMD": "use",
                "candidates": list(self._last_ambiguity_candidates),
                "two_obj": {
                    "slot": "right",
                    "fixed_entity": left_entity,
                    "connector": connector,
                    "lead_verb": lead_verb
                }
            }
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
                        self.pending_disambiguation = {
                            "CMD": "use",
                            "candidates": list(self._last_ambiguity_candidates),
                            "action_verb": "use",
                            "is_read": False,
                            "is_action": True,
                        }
                        return {"CMD": "respond", "OBJ": msg}
                    if resolved == item_name or any(a in norm_text for a in data.get('aliases', [])):
                        return {"CMD": "use", "OBJ": [item_name]}

        for verb, target_items in self._custom_solo_verbs.items():
            if norm_text.startswith(verb + " ") or norm_text == verb:
                noun_phrase = norm_text[len(verb):].strip()
                cleaned_words = [w for w in noun_phrase.split() if w not in self.LEADING_ARTICLES and w != 'to']
                target_noun = " ".join(cleaned_words)
                resolved, ambig, msg = self._resolve_entity(target_noun, vocab, ambiguous_vocab)
                if ambig:
                    self.pending_disambiguation = {
                        "CMD": "use",
                        "candidates": list(self._last_ambiguity_candidates),
                        "action_verb": verb,
                        "is_read": False,
                        "is_action": True,
                    }
                    return {"CMD": "respond", "OBJ": msg}
                if resolved:
                    return {"CMD": "use", "OBJ": {"item": resolved, "action": verb}}

        return None

    def _match_verb_and_object(self, norm, verbs, empty_prompt, cmd, vocab, ambiguous_vocab, is_action=False, is_read=False):
        for v in sorted(verbs, key=lambda x: len(x), reverse=True):
            if norm == v:
                prompt = empty_prompt(v) if callable(empty_prompt) else empty_prompt
                return {"CMD": "respond", "OBJ": prompt}
            if norm.startswith(v + " "):
                noun_phrase = norm[len(v):].strip()
                if is_read and noun_phrase in {"journal", "log", "notes"}:
                    return {"CMD": "journal", "OBJ": ""}
                entity, ambig, msg = self._resolve_entity(noun_phrase, vocab, ambiguous_vocab)
                if ambig:
                    self.pending_disambiguation = {
                        "CMD": "use" if is_action else ("read" if is_read else cmd),
                        "candidates": list(self._last_ambiguity_candidates),
                        "action_verb": v if is_action else None,
                        "is_read": is_read,
                        "is_action": is_action,
                    }
                    return {"CMD": "respond", "OBJ": msg}
                if is_action:
                    target_entity = entity if entity else noun_phrase.replace(' ', '_')
                    if v == 'use':
                        return {"CMD": "use", "OBJ": [target_entity]}
                    return {"CMD": "use", "OBJ": {"item": target_entity, "action": v}}
                elif is_read:
                    target_entity = entity if entity else noun_phrase.replace(' ', '_')
                    return {"CMD": "read", "OBJ": target_entity}
                else:
                    return {"CMD": cmd, "OBJ": entity}
        return None

    def _resolve_candidate_phrase(self, phrase, candidates, vocab, ambiguous_vocab):
        if not phrase:
            return None

        for c in candidates:
            if phrase == c or phrase == c.replace('_', ' '):
                return c

        for c in candidates:
            disp = self._get_entity_display_name(c).lower()
            if phrase == disp or phrase == self._strip_noise_words(disp):
                return c

        ent, ambig, _ = self._resolve_entity(phrase, vocab, ambiguous_vocab)
        if not ambig and ent in candidates:
            return ent

        matching = []
        for c in candidates:
            disp_words = set(self._get_entity_display_name(c).lower().split())
            id_words = set(c.split('_'))
            cand_words = disp_words | id_words
            if phrase in cand_words:
                matching.append(c)

        if len(matching) == 1:
            return matching[0]

        return None

    def _match_disambiguation_candidate(self, norm, candidates, vocab, ambiguous_vocab):
        cleaned = self._strip_noise_words(norm)
        if not cleaned:
            return None

        words = cleaned.split()
        if len(words) > 1:
            all_verbs = (
                self.MOVE_VERBS | self.PICKUP_VERBS | self.DROP_VERBS |
                self.LOOK_VERBS | self.READ_VERBS | self._get_action_verbs()
            )
            for v in sorted(all_verbs, key=lambda x: len(x), reverse=True):
                if cleaned.startswith(v + " "):
                    stripped = self._strip_noise_words(cleaned[len(v):].strip())
                    match = self._resolve_candidate_phrase(stripped, candidates, vocab, ambiguous_vocab)
                    if match:
                        return match

        return self._resolve_candidate_phrase(cleaned, candidates, vocab, ambiguous_vocab)

    def _complete_disambiguated_command(self, pending, matched_candidate):
        if "two_obj" in pending:
            two_obj = pending["two_obj"]
            lead_verb = two_obj.get("lead_verb")
            connector = two_obj.get("connector", "with")
            if two_obj.get("slot") == "left":
                left_entity = matched_candidate
                right_entity = two_obj["fixed_entity"]
            else:
                left_entity = two_obj["fixed_entity"]
                right_entity = matched_candidate

            item, target = self._align_item_and_target(left_entity, right_entity, connector, lead_verb)
            result_obj = {"item": item, "target": target}
            if lead_verb:
                result_obj["action"] = lead_verb
            return {"CMD": "use", "OBJ": result_obj}

        cmd = pending.get("CMD", "use")
        if pending.get("is_action"):
            action_verb = pending.get("action_verb")
            if action_verb == 'use' or not action_verb:
                return {"CMD": "use", "OBJ": [matched_candidate]}
            return {"CMD": "use", "OBJ": {"item": matched_candidate, "action": action_verb}}
        elif pending.get("is_read"):
            return {"CMD": "read", "OBJ": matched_candidate}
        else:
            return {"CMD": cmd, "OBJ": matched_candidate}

    def parse(self, user_input):
        norm = self.normalize(user_input)
        if not norm:
            return {"CMD": "", "OBJ": ""}

        if self.pending_disambiguation:
            pending = self.pending_disambiguation
            self.pending_disambiguation = None

            if norm in {'cancel', 'nevermind', 'never mind', 'stop', 'abort'}:
                return {"CMD": "respond", "OBJ": "Cancelled."}

            vocab, ambiguous_vocab = self._get_entity_vocabulary()
            matched_candidate = self._match_disambiguation_candidate(
                norm, pending["candidates"], vocab, ambiguous_vocab
            )
            if matched_candidate:
                return self._complete_disambiguated_command(pending, matched_candidate)

        words = norm.split()
        first_word = words[0]

        dir_match = self._match_direction(norm)
        if dir_match:
            return {"CMD": "move", "OBJ": dir_match}

        transit_match = self._parse_transit(norm)
        if transit_match is not None:
            return transit_match

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

        vocab, ambiguous_vocab = self._get_entity_vocabulary()

        two_obj = self._parse_two_object_command(norm, vocab, ambiguous_vocab)
        if two_obj is not None:
            return two_obj

        solo_cmd = self._check_solo_keywords(norm, vocab, ambiguous_vocab)
        if solo_cmd is not None:
            return solo_cmd

        if norm in {'look', 'l', 'look around', 'look room', 'examine room'}:
            return {"CMD": "look", "OBJ": ""}

        res = self._match_verb_and_object(norm, self.LOOK_VERBS, "Look at what?", "look", vocab, ambiguous_vocab)
        if res is not None:
            return res

        res = self._match_verb_and_object(norm, self.PICKUP_VERBS, "Take what?", "pickup", vocab, ambiguous_vocab)
        if res is not None:
            return res

        res = self._match_verb_and_object(norm, self.DROP_VERBS, "Drop what?", "drop", vocab, ambiguous_vocab)
        if res is not None:
            return res

        res = self._match_verb_and_object(norm, self.READ_VERBS, "Read what?", "read", vocab, ambiguous_vocab, is_read=True)
        if res is not None:
            return res

        action_verbs = self._get_action_verbs()
        res = self._match_verb_and_object(norm, action_verbs, lambda v: f"{v.capitalize()} what?", "use", vocab, ambiguous_vocab, is_action=True)
        if res is not None:
            return res

        entity, ambig, msg = self._resolve_entity(norm, vocab, ambiguous_vocab)
        if ambig:
            self.pending_disambiguation = {
                "CMD": "look",
                "candidates": list(self._last_ambiguity_candidates),
                "action_verb": None,
                "is_read": False,
                "is_action": False,
            }
            return {"CMD": "respond", "OBJ": msg}
        if entity and entity in vocab.values():
            return {"CMD": "look", "OBJ": entity}

        return {"CMD": norm, "OBJ": ""}
