import json
import os
from collections import Counter
import server # import your existing server scraping logic


def detect_map_pool(matches, min_pct=3.0):
    """
    Auto-detect the current competitive map pool from scraped pro match data.
    Maps that account for at least `min_pct`% of total maps played are
    considered part of the active rotation. Pro matches only use the current
    comp pool, so frequent maps = current rotation.
    """
    map_counts = Counter()
    for match in matches:
        for m in (match.get('maps') or []):
            name = m.get('map_name', 'Unknown')
            if name and name != 'Unknown':
                map_counts[name] += 1

    total = sum(map_counts.values())
    if total == 0:
        return sorted(map_counts.keys())

    pool = [
        name for name, count in map_counts.items()
        if (count / total * 100) >= min_pct
    ]
    pool.sort()
    return pool


def main():
    print("Scraping vlr.gg for static data...")
    # Matches logic currently mirrors what /api/full-data?pages=2&max=30 did
    matches = server.scrape_match_results(num_pages=3)[:100]
    results = []
    
    for m in matches:
        try:
            detail = server.scrape_match_detail(m['id'], m['url'])
            results.append(detail)
            print(f"Scraped {m['id']} - {m['team1']} vs {m['team2']}")
        except Exception as e:
            print(f"  [ERROR] Match {m['id']}: {e}")
    
    # Auto-detect current comp map pool from the scraped data
    map_pool = detect_map_pool(results)
    print(f"🗺️  Detected comp map pool: {', '.join(map_pool)}")

    data = {
        'status': 'success',
        'count': len(results),
        'map_pool': map_pool,
        'matches': results,
    }
    
    # Save the output to data.json
    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data.json')
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Successfully saved {len(results)} matches to {out_path}")

if __name__ == "__main__":
    main()
