import re

html_str = open('match_sample.html', 'r', encoding='utf-8').read()
game_blocks = re.split(r'<div class="vm-stats-game\s', html_str)

known_maps = {'Ascent', 'Bind', 'Haven', 'Split', 'Icebox', 'Breeze', 'Fracture', 'Lotus', 'Sunset', 'Pearl', 'Abyss'}
for i, gb in enumerate(game_blocks[1:]):
    # Extract ALL word chunks
    words = re.findall(r'>\s*([A-Za-z]+)', gb)
    matched = False
    for w in words:
        if w in known_maps:
            print(f"Map {i+1} found:", w)
            matched = True
            break
    if not matched:
        print(f"Map {i+1} NOT FOUND. Words:", words[:20])
