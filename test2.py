import server
import re
import pprint

print("Fetching old matches to guarantee VODs...")
matches = server.scrape_match_results(num_pages=5)[40:50]
for m in matches:
    html = server.cached_fetch(f"https://www.vlr.gg{m['url']}")
    
    # Try finding VOD blocks specifically first (vlr uses class="match-vods" or "wf-card mod-vod")
    streams = re.findall(r'<a[^>]*href=["\']([^"\']+tube[^"\']+|[^"\']+twitch[^"\']+)["\'][^>]*>', html)
    
    # Filter to actual VOD urls
    vods = [s for s in streams if (('youtu' in s) or ('twitch' in s)) and ('clip' not in s)]
    if vods:
        print(f"\nMatch: {m['url']}")
        pprint.pprint(vods)
