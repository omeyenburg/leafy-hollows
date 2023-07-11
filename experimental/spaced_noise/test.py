dest_rect = [-0.022283531409168077, -0.050000000000000044, 0.012733446519524618, 0.035653650254668934]
stencil = [0, 0, 0.5, 0.5]

org = dest_rect[:]
dest_rect[0] = max(stencil[0], dest_rect[0])
dest_rect[1] = max(stencil[1], dest_rect[1])
stencil_offset = (dest_rect[0] - org[0], dest_rect[1] - org[1])
dest_rect[2] -= stencil_offset[0]
dest_rect[3] -= stencil_offset[1]

org_left = dest_rect[0] + dest_rect[2]
stencil_left = stencil[0] + stencil[2]
if org_left > stencil_left:
    dest_rect[2] = stencil_left - dest_rect[0]
else:
    dest_rect[2] = org_left - dest_rect[0] - stencil[0]


org_top = dest_rect[1] + dest_rect[3]
stencil_top = stencil[1] + stencil[3]
if org_top > stencil_top:
    dest_rect[3] = stencil_top - dest_rect[1]
else:
    dest_rect[3] = org_top - dest_rect[1] - stencil[1]

print(dest_rect)


left = max(dest_rect[0], stencil[0])
right = min(dest_rect[0] + dest_rect[2], stencil[0] + stencil[2])
top = max(dest_rect[1], stencil[1])
bottom = min(dest_rect[1] + dest_rect[3], stencil[1] + stencil[3])

if left > right and top > bottom:
    overlap_width = right - left
    overlap_height = bottom - top
else:
    overlap_width = overlap_height = 0

dest_rect = [left, top, overlap_width, overlap_height]

print(dest_rect)
