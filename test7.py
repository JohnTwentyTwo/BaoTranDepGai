import re

html_str = open('match_sample.html', 'r', encoding='utf-8').read()
game_blocks = re.split(r'<div class="vm-stats-game\s', html_str)
gb = game_blocks[1]
header_html = gb.split('<table')[0] if '<table' in gb else gb 
clean_header = re.sub(r'<[^>]+>', ' ', header_html)
print("WORDS in header:", re.findall(r'[A-Za-z]+', clean_header)[:20])

gb_all_words = re.findall(r'[A-Za-z]+', re.sub(r'<[^>]+>', ' ', gb))
print("WORDS in all gb:", gb_all_words[:20])

known_maps = {'ascent', 'bind', 'haven', 'split', 'icebox', 'breeze', 'fracture', 'lotus', 'sunset', 'pearl', 'abyss'}
print("Map in header?", [w for w in re.findall(r'[A-Za-z]+', clean_header) if w.lower() in known_maps])
print("Map in gb?", [w for w in gb_all_words if w.lower() in known_maps])
