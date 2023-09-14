import glob
import json
import os


suffix = "wav"
options = {
    "name": "player_walk_gravel",
    "speed": 0.5,
    "volume": 0.2,
    "category": "player",
}

directory = os.path.dirname(__file__)
files = sorted(glob.glob(directory + "/*." + suffix))
options["sounds"] = [os.path.basename(file) for file in files]


with open(directory + "/" + options["name"] + ".json", "w") as f:
    json.dump(options, f, indent=4)