/**
 * Schema normalization, room description assembly, and YAML serialization
 */

function assembleRoomDescription(room) {
  if (!room) return '';
  const parts = [];
  if (room.base_description && typeof room.base_description === 'string' && room.base_description.trim()) {
    parts.push(room.base_description.trim());
  }
  if (room.fixtures && typeof room.fixtures === 'object') {
    const sorted = Object.entries(room.fixtures).sort(([, a], [, b]) => (a.priority || 10) - (b.priority || 10));
    for (const [, fix] of sorted) {
      if (!fix) continue;
      const activeState = fix.state || 'default';
      const text = fix.states ? fix.states[activeState] : '';
      if (text && typeof text === 'string' && text.trim()) {
        parts.push(text.trim());
      }
    }
  }
  if (room.trailing_description && typeof room.trailing_description === 'string' && room.trailing_description.trim()) {
    parts.push(room.trailing_description.trim());
  }
  return parts.join('\n\n');
}

function cleanModularRoomsForExport(data) {
  if (!data || !Array.isArray(data.rooms)) return;
  data.rooms = data.rooms.map(room => {
    delete room.states;
    const ordered = {};
    if (room.name !== undefined) ordered.name = room.name;
    if (room.display_name !== undefined) ordered.display_name = room.display_name;

    // Defensive normalization: ensure exits is an array of strings
    if (room.exits !== undefined) {
      if (Array.isArray(room.exits)) {
        ordered.exits = room.exits.map(x => String(x).trim()).filter(Boolean);
      } else if (typeof room.exits === 'object' && room.exits !== null) {
        ordered.exits = Object.keys(room.exits).map(x => String(x).trim()).filter(Boolean);
      } else if (typeof room.exits === 'string') {
        ordered.exits = [room.exits.replace(/^[-–—\s]+/, '').trim()].filter(Boolean);
      } else {
        ordered.exits = [];
      }
    } else {
      ordered.exits = [];
    }

    ordered.base_description = typeof room.base_description === 'string' ? room.base_description : '';
    ordered.fixtures = (room.fixtures && typeof room.fixtures === 'object') ? room.fixtures : {};
    ordered.trailing_description = typeof room.trailing_description === 'string' ? room.trailing_description : '';
    if (room.items !== undefined) ordered.items = room.items;

    if (room.locked_exits !== undefined) {
      if (Array.isArray(room.locked_exits)) {
        ordered.locked_exits = room.locked_exits.map(x => String(x).trim()).filter(Boolean);
      } else if (typeof room.locked_exits === 'string') {
        ordered.locked_exits = [room.locked_exits.replace(/^[-–—\s]+/, '').trim()].filter(Boolean);
      } else {
        ordered.locked_exits = [];
      }
    } else {
      ordered.locked_exits = [];
    }

    if (room.exit_destinations !== undefined && typeof room.exit_destinations === 'object' && room.exit_destinations !== null) {
      if (Object.keys(room.exit_destinations).length > 0) {
        ordered.exit_destinations = room.exit_destinations;
      }
    }

    Object.keys(room).forEach(k => {
      if (ordered[k] === undefined && k !== 'states') ordered[k] = room[k];
    });
    return ordered;
  });
}

function dumpYaml(data) {
  cleanModularRoomsForExport(data);
  return window.jsyaml.dump(data, {
    lineWidth: 120,
    quotingType: '"',
    forceQuotes: false,
    noRefs: true
  });
}

function createBarebonesAdventure() {
  return {
    intro: {
      title: "New Adventure",
      text: "You awaken in a quiet entry hall. Dust motes drift in the faint light filtering through a high transom window.",
      instructions: "Type commands like 'look', 'take key', 'unlock gate with key', or 'go north'."
    },
    player: {
      starting_location: {
        floor: 0,
        x: 2,
        y: 2
      },
      starting_inventory: ["pocket_flashlight"]
    },
    items: {
      pocket_flashlight: {
        display_name: "Pocket Flashlight",
        keywords: ["flashlight", "light", "torch"],
        states: {
          default: {
            examine: "A compact brass flashlight. The bulb casts a steady warm beam.",
            use: "You click the flashlight on and off. The beam cuts clearly through the shadows."
          }
        }
      },
      brass_key: {
        display_name: "Brass Key",
        aliases: ["key", "brass key"],
        keywords: ["key", "brass key"],
        states: {
          default: {
            examine: "A heavy, notched brass key with an ornate clover bow.",
            use: "Try using this key on a locked door or gate."
          }
        }
      }
    },
    rooms: [
      {
        name: "entry_hall",
        display_name: "Grand Entry Hall",
        base_description: "You stand in a vaulted entry hall with checkered stone tiles underfoot.",
        fixtures: {
          pedestal: {
            display_name: "Stone Pedestal",
            priority: 10,
            state: "default",
            states: {
              default: "In the center of the hall stands a carved stone pedestal."
            },
            examine: {
              default: "The marble pedestal is carved with leaf motifs. A brass key rests on top."
            }
          }
        },
        items: ["brass_key"],
        exits: ["north"],
        locked_exits: [],
        trailing_description: "A wide arched corridor leads north toward the courtyard."
      },
      {
        name: "courtyard",
        display_name: "Sunlit Courtyard",
        base_description: "An open-air courtyard surrounded by stone columns and ivy.",
        fixtures: {
          heavy_gate: {
            display_name: "Heavy Iron Gate",
            priority: 10,
            state: "locked",
            states: {
              locked: "To the north, a towering iron gate is chained shut with a sturdy brass padlock.",
              unlocked: "To the north, the iron gate stands unlocked and slightly ajar."
            },
            examine: {
              locked: "Heavy iron bars sealed with a brass padlock. It looks like a key would fit.",
              unlocked: "The gate is unlocked and swings freely."
            }
          }
        },
        items: [],
        exits: ["south"],
        locked_exits: ["north"],
        trailing_description: "Stone arches lead south back to the entry hall."
      }
    ],
    floors: [
      [
        [null, null, null, null, null],
        [null, null, "courtyard", null, null],
        [null, null, "entry_hall", null, null],
        [null, null, null, null, null],
        [null, null, null, null, null]
      ]
    ],
    events: [
      {
        id: "unlock_gate",
        trigger: {
          type: "use_item",
          action: "use",
          source: "brass_key",
          target: "heavy_gate"
        },
        conditions: [
          {
            type: "in_room",
            room: "courtyard",
            on_fail_hint: "You need to be in the courtyard near the gate."
          }
        ],
        result: {
          set_fixture_state: [
            {
              room: "courtyard",
              fixture: "heavy_gate",
              state: "unlocked"
            }
          ],
          open_exit: [
            {
              room: "courtyard",
              direction: "north"
            }
          ],
          message: "You insert the brass key into the padlock. With a satisfying click, the lock springs open and the heavy iron gate swings ajar!"
        }
      }
    ],
    win_conditions: ["unlock_gate"],
    win_screen: {
      title: "You Have Escaped!",
      text: "You push past the iron gate and step into the sunlight beyond. Freedom is yours."
    },
    target_aliases: {
      heavy_gate: ["gate", "iron gate", "padlock"],
      pedestal: ["stone pedestal"]
    },
    custom_verbs: {}
  };
}

window.assembleRoomDescription = assembleRoomDescription;
window.cleanModularRoomsForExport = cleanModularRoomsForExport;
window.dumpYaml = dumpYaml;
window.createBarebonesAdventure = createBarebonesAdventure;

