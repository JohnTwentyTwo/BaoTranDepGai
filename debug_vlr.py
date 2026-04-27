import server
import re
import pprint

html_str = server.fetch_url("https://www.vlr.gg/645489/")
game_blocks = re.split(r'<div class="vm-stats-game\s', html_str)
print("Found game blocks:", len(game_blocks)-1)

gb = game_blocks[1]

map_div = re.search(r'<div class="map">(.*?)</div>', gb, re.DOTALL)
print("MAP DIV HTML:\n", map_div.group(1) if map_div else 'None')

player_rows = re.findall(r'<tr>\s*<td class="mod-player"[^>]*>(.*?)</td>\s*<td class="mod-agents">(.*?)</td>', gb, re.DOTALL)
if player_rows:
    print("\nAGENT HTML 1:\n", player_rows[0][1])
    # check fallback
    print("Fallback matches:", re.findall(r'/agents/([a-zA-Z0-9-]+)\.png', player_rows[0][1], re.IGNORECASE))
    print("Title matches:", re.findall(r'title="([^"]+)"', player_rows[0][1]))
    print("Alt matches:", re.findall(r'alt="([^"]+)"', player_rows[0][1]))
