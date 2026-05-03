import json
import os
from collections import Counter
import server  # import your existing server scraping logic


def count_map_instances(matches):
    """Count how many map instances exist per map name across all matches."""
    counts = Counter()
    for match in matches:
        for m in (match.get('maps') or []):
            name = m.get('map_name', 'Unknown')
            if name and name != 'Unknown':
                counts[name] += 1
    return counts


def detect_map_pool(matches, min_pct=3.0):
    """
    Auto-detect the current competitive map pool from scraped pro match data.
    Maps that account for at least `min_pct`% of total maps played are
    considered part of the active rotation. Pro matches only use the current
    comp pool, so frequent maps = current rotation.
    """
    map_counts = count_map_instances(matches)
    total = sum(map_counts.values())
    if total == 0:
        return sorted(map_counts.keys())

    pool = [
        name for name, count in map_counts.items()
        if (count / total * 100) >= min_pct
    ]
    pool.sort()
    return pool


def backfill_sparse_maps(results, map_pool, min_maps=20, max_extra_pages=10):
    """
    If any map in the pool has fewer than `min_maps` instances, scrape older
    match pages to backfill data for those maps. This handles the case where
    a map is newly added to the comp rotation and doesn't have enough data yet.
    """
    map_counts = count_map_instances(results)
    sparse_maps = {m for m in map_pool if map_counts.get(m, 0) < min_maps}

    if not sparse_maps:
        print("✅ All maps have sufficient data, no backfill needed.")
        return results

    needed = {m: min_maps - map_counts.get(m, 0) for m in sparse_maps}
    print(f"⚠️  Maps needing backfill:")
    for m, n in sorted(needed.items()):
        print(f"    {m}: {map_counts.get(m, 0)} instances (need {n} more)")

    existing_ids = {m['id'] for m in results}
    # We already scraped pages 1-3, start from page 4
    start_page = 4

    for page in range(start_page, start_page + max_extra_pages):
        if not sparse_maps:
            break

        print(f"   📄 Scraping page {page} for backfill...")
        try:
            page_matches = server.scrape_match_results(
                num_pages=1, start_page=page
            )
        except Exception as e:
            print(f"   [ERROR] Failed to scrape page {page}: {e}")
            continue

        if not page_matches:
            print(f"   No more matches found, stopping backfill.")
            break

        for m in page_matches:
            if m['id'] in existing_ids:
                continue
            if not sparse_maps:
                break

            try:
                detail = server.scrape_match_detail(m['id'], m['url'])
                # Check if this match has any of the sparse maps
                match_maps = {
                    mp.get('map_name', 'Unknown')
                    for mp in (detail.get('maps') or [])
                }
                has_sparse = match_maps & sparse_maps

                if has_sparse:
                    results.append(detail)
                    existing_ids.add(m['id'])
                    print(f"   ✓ Backfilled {m['id']} — "
                          f"{m['team1']} vs {m['team2']} "
                          f"(maps: {', '.join(has_sparse)})")

                    # Update counts
                    for mp in (detail.get('maps') or []):
                        name = mp.get('map_name', 'Unknown')
                        if name in sparse_maps:
                            needed[name] -= 1
                            if needed[name] <= 0:
                                sparse_maps.discard(name)
                                print(f"   ✅ {name} now has enough data!")
            except Exception as e:
                print(f"   [ERROR] Match {m['id']}: {e}")

    # Final report
    final_counts = count_map_instances(results)
    for m in map_pool:
        count = final_counts.get(m, 0)
        status = "✅" if count >= min_maps else "⚠️"
        print(f"   {status} {m}: {count} map instances")

    return results


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
    print(f"\n🗺️  Detected comp map pool: {', '.join(map_pool)}")

    # Backfill maps that are new to rotation and don't have enough data
    print(f"\n📊 Checking map data coverage (min 20 per map)...")
    results = backfill_sparse_maps(results, map_pool, min_maps=20)

    # Re-detect pool after backfill (in case new maps emerged)
    map_pool = detect_map_pool(results)

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

    print(f"\n✅ Successfully saved {len(results)} matches to {out_path}")


if __name__ == "__main__":
    main()
