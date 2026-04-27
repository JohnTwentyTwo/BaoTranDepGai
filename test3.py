import server
import re
import pprint

url = '/645489/'
html_str = server.fetch_url(f"https://www.vlr.gg{url}")
print(f"Scraping match detail for {url}...")
# Just manually run the map logic
game_blocks = re.split(r'<div class="vm-stats-game\s', html_str)
print(f"Found {len(game_blocks)} game blocks")
if len(game_blocks) > 1:
    for i, gb in enumerate(game_blocks[1:]):
        print(f"--- Map {i+1} ---")
        map_m = re.search(r'<div class="map">\s*<div[^>]*>\s*(?:<span[^>]*>)?\s*(\w+)', gb)
        print("Regex 1 map name matched:", map_m.group(1) if map_m else None)
        
        # Test alternative regexes for map
        alt_m1 = re.search(r'<span style="font-weight: 700;">([^<]+)<\/span>', gb)
        alt_m2 = re.search(r'<div class="map">.*?<span[^>]*>([^<]+)</span>', gb, re.DOTALL)
        print("Alt map match 1 (font-weight):", alt_m1.group(1) if alt_m1 else None)
        print("Alt map match 2 (div map span):", alt_m2.group(1).strip() if alt_m2 else None)
        
        # Agent parsing
        player_rows = re.findall(
            r'<tr>\s*<td class="mod-player"[^>]*>(.*?)</td>\s*<td class="mod-agents">(.*?)</td>',
            gb, re.DOTALL
        )
        if player_rows:
            agent_html = player_rows[0][1]
            print("First player agent HTML snippet:", agent_html.strip().replace('\n', ''))
            print("Regex /agents/ match:", re.findall(r'/agents/([^.]+)\.png', agent_html))
