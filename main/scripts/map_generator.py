# -*- coding: utf-8 -*-
import time
import wfc


dirt = wfc.State(
    "dirt",
    wfc.Rule(
        lambda x, y: {
            (x, y+1): ["dirt", "grass"],
            (x, y-1): ["stone", "dirt"]
        }
    )
)

stone = wfc.State(
    "stone",
    wfc.Rule(
        lambda x, y : {
            (x, y+1): ["stone", "dirt"]
        }
    )
)

air = wfc.State(
    "air",
    wfc.Rule(
        lambda x, y : {
            (x, y+1): ["air"]
        }
    )
)

def default_states(width: int, height: int) -> list:
    t0 = time.time()

    landscape_wave = wfc.Wave(
        (height, width),  # y
        [dirt, stone, air]
    )

    landscape = landscape_wave.collapse()
    block_map = []
    for row in landscape:
        block_map.append([item.state.name for item in row])

    print(f"wfc time: {time.time() - t0}")
    print(f"block count: {sum( [ len(listElem) for listElem in block_map])}")

    return block_map