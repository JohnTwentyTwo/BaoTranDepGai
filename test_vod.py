import re
import server

print("Fetching matches...")
matches = server.scrape_match_results(num_pages=3)
for m in matches:
    html_str = server.cached_fetch(f"https://www.vlr.gg{m['url']}")
    # match-vods links
    vods = re.findall(r'<a.*?href="(https?://(?:www\.)?(?:youtube\.com|youtu\.be|twitch\.tv)[^"]+)".*?>', html_str)
    if vods:
        print(f"Found VODs for {m['url']}: {[v[0] for v in vods]}")
        with open('match_sample.html', 'w', encoding='utf-8') as f:
            f.write(html_str)
        break
