LE_pins = {
    1: "GP23",
    2: "GP24",
    3: "GP25",
    4: "GP27"
}

electrode_mappings = {
    1: {
        "cathode": ["GP5"],
        "anode": ["GP6"],
        "ground": ["GP5", "GP6"]
    },
    2: {
        "cathode": ["GP12"],
        "anode": ["GP13"],
        "ground": ["GP12", "GP13"]
    },
    3: {
        "cathode": ["GP16"],
        "anode": ["GP19"],
        "ground": ["GP16", "GP19"]
    },
    4: {
        "cathode": ["GP20"],
        "anode": ["GP21"],
        "ground": ["GP20", "GP21"]
    }
}

for i in range(5, 17):
    le_group = (i - 1) // 4
    electrode_mappings[i] = electrode_mappings[i % 4 or 4]
print(electrode_mappings)