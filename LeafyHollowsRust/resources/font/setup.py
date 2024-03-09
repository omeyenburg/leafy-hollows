import json


chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789äÄöÖüÜß_.,:;?!<>=#%'\"+-*/()[]{}°^~$&"
data = {
    "width": 5,
    "height": 10,
    "chars": {}
}

for i, char in enumerate(chars):
    data["chars"][char] = [i % 26, i // 26]
with open("font.json", "w+") as f:
    json.dump(data, f, indent=4, ensure_ascii=False)
