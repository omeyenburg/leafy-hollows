import glob
import os


prefix = "player_swim"
suffix = "wav"


directory = os.path.dirname(__file__)
files = sorted(glob.glob(directory + "/*." + suffix), key=lambda name: str(int(not name.startswith(prefix))) + name)


for i, file in enumerate(files):
    new_file = directory + "/" + eval('prefix + f"{i:number_length}.".replace(" ", "0") + suffix'.replace("number_length", str(len(str(len(files) - 1)))))
    os.rename(file, new_file)