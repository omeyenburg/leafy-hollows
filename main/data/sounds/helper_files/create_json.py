import glob
import json
import os


suffix = "wav"
options = {
    "name": "player_swim",
    "speed": 0.6,
    "volume": 0.4,
    "category": "player",
}

directory = os.path.dirname(__file__)
files = sorted(glob.glob(directory + "/*." + suffix))
options["sounds"] = [os.path.basename(file) for file in files]


with open(directory + "/" + options["name"] + ".json", "w") as f:
    json.dump(options, f, indent=4)