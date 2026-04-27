import re, urllib.request, urllib.parse

# 1. Test DDG HTML search for YouTube VOD
query = "Valorant T1 vs ZETA DIVISION VOD"
q = urllib.parse.quote_plus('site:youtube.com ' + query)
req = urllib.request.Request(f"https://html.duckduckgo.com/html/?q={q}", headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0)'})
try:
    html = urllib.request.urlopen(req, timeout=10).read().decode('utf-8')
    m = re.search(r'href="//duckduckgo.com/l/\?ud.*?uddg=([^"]+)"', html)
    if m:
        print("DDG found Youtube:", urllib.parse.unquote(m.group(1)))
    else:
        print("DDG matched nothing.")
except Exception as e:
    print("DDG Exception:", e)

# 2. Test Map parsing
html_str = open('match_sample.html', 'r', encoding='utf-8').read()
game_blocks = re.split(r'<div class="vm-stats-game\s', html_str)
gb = game_blocks[1]

# Try parsing Map by finding the team nodes
teams = re.findall(r'<div class="team-name">(.*?)</div>', gb)
print("Teams found in Map:", teams)

# The map name is often heavily nested. Let's just strip all HTML from the very first 300 chars of `gb`.
snippet = gb[:300]
text = re.sub(r'<[^>]+>', ' ', snippet)
text = re.sub(r'\s+', ' ', text).strip()
print("Clean text of gb top:", text)

# Try matching against known map list
known_maps = ['Ascent', 'Bind', 'Haven', 'Split', 'Icebox', 'Breeze', 'Fracture', 'Lotus', 'Sunset', 'Pearl', 'Abyss']
for km in known_maps:
    if km.lower() in text.lower():
        print("MATCHED MAP:", km)
        break
