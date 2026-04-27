import re

html_str = open('match_sample.html', 'r', encoding='utf-8').read()

# 1. Team Names
teams = re.findall(r'<div class="wf-title-med">\s*([^<]+)', html_str)
print("Team names from wf-title-med:", teams)
# Look for team names in the actual header
title_m = re.search(r'<title>([^<]+)', html_str)
print("Title:", title_m.group(1) if title_m else "None")

# 2. Map casing
game_blocks = re.split(r'<div class="vm-stats-game\s', html_str)
for gb in game_blocks[1:2]:
    header_html = gb.split('<table')[0] if '<table' in gb else gb 
    clean_header = re.sub(r'<[^>]+>', ' ', header_html)
    words = re.findall(r'[A-Za-z]+', clean_header)
    print("Words extracted:", words[:10])
    
    known_maps = {'ascent', 'bind', 'haven', 'split', 'icebox', 'breeze', 'fracture', 'lotus', 'sunset', 'pearl', 'abyss'}
    for w in words:
        if w.lower() in known_maps:
            print("MATCHED MAP:", w.title())
            break
