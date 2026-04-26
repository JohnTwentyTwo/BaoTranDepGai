import server
import re

# Pick a known match with good data
matches = server.scrape_match_results(num_pages=1)[:3]
for m in matches:
    url = f"https://www.vlr.gg{m['url']}"
    print(f"\nChecking {url}")
    html = server.fetch_url(url)
    
    # Look for economy/weapon-related sections
    if 'econ' in html.lower():
        print("  Found 'econ' mention")
    if 'weapon' in html.lower():
        print("  Found 'weapon' mention")
    if 'loadout' in html.lower():
        print("  Found 'loadout' mention")
    if 'kill' in html.lower():
        print("  Found 'kill' mention")
    
    # Check for economy round data
    econ_blocks = re.findall(r'class="[^"]*econ[^"]*"', html)
    print(f"  Econ blocks found: {len(econ_blocks)}")
    for eb in econ_blocks[:5]:
        print(f"    {eb}")
    
    # Look for weapon names in the page
    weapons = ['Vandal', 'Phantom', 'Operator', 'Sheriff', 'Spectre', 'Ghost', 'Classic', 'Marshal']
    for w in weapons:
        count = html.lower().count(w.lower())
        if count > 0:
            print(f"  {w}: {count} mentions")
    break
