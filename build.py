import json
import os
import server # import your existing server scraping logic

def main():
    print("Scraping vlr.gg for static data...")
    # Matches logic currently mirrors what /api/full-data?pages=2&max=30 did
    matches = server.scrape_match_results(num_pages=2)[:30]
    results = []
    
    for m in matches:
        try:
            detail = server.scrape_match_detail(m['id'], m['url'])
            results.append(detail)
            print(f"Scraped {m['id']} - {m['team1']} vs {m['team2']}")
        except Exception as e:
            print(f"  [ERROR] Match {m['id']}: {e}")
    
    data = {'status': 'success', 'count': len(results), 'matches': results}
    
    # Save the output to data.json
    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data.json')
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Successfully saved {len(results)} matches to {out_path}")

if __name__ == "__main__":
    main()
