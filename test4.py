import urllib.request
import urllib.parse
import re

# Test YouTube
query = urllib.parse.quote_plus("Valorant T1 vs ZETA DIVISION VOD")
yt_url = f"https://www.youtube.com/results?search_query={query}"
try:
    req = urllib.request.Request(yt_url, headers={'User-Agent': 'Mozilla/5.0'})
    yt_html = urllib.request.urlopen(req, timeout=10).read().decode('utf-8')
    yt_m = re.search(r'"videoId":"([a-zA-Z0-9_-]{11})"', yt_html)
    print("YT Match:", yt_m.group(1) if yt_m else "NO MATCH")
except Exception as e:
    print("YT Exception:", e)

# Test Map
html_str = open('match_sample.html', 'r', encoding='utf-8').read()
game_blocks = re.split(r'<div class="vm-stats-game\s', html_str)
gb = game_blocks[1]
print("Map classes found:", re.findall(r'class="[^"]*map[^"]*"', gb))
