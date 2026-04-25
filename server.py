import http.server
import urllib.request
import urllib.parse
import json
import os
import re
import ssl
import time
import html
import threading

PORT = int(os.environ.get('PORT', 8080))
VLR_BASE = 'https://www.vlr.gg'
STATIC_DIR = os.path.dirname(os.path.abspath(__file__))

MIME_TYPES = {
    '.html': 'text/html',
    '.css': 'text/css',
    '.js': 'application/javascript',
    '.json': 'application/json',
    '.png': 'image/png',
    '.jpg': 'image/jpeg',
    '.svg': 'image/svg+xml',
    '.ico': 'image/x-icon',
}

ssl_ctx = ssl.create_default_context()
ssl_ctx.check_hostname = False
ssl_ctx.verify_mode = ssl.CERT_NONE

# ========== CACHE ==========
_cache = {}
CACHE_TTL = 600  # 10 minutes

def cached_fetch(url, ttl=CACHE_TTL):
    now = time.time()
    if url in _cache and now - _cache[url]['time'] < ttl:
        return _cache[url]['data']
    data = fetch_url(url)
    _cache[url] = {'data': data, 'time': now}
    return data

# ========== HTTP FETCH ==========
def fetch_url(url):
    req = urllib.request.Request(url, headers={
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
    })
    with urllib.request.urlopen(req, context=ssl_ctx, timeout=20) as resp:
        return resp.read().decode('utf-8', errors='ignore')

# ========== SCRAPER: MATCH LIST ==========
def scrape_match_results(num_pages=1):
    all_matches = []
    for page in range(1, num_pages + 1):
        url = f'{VLR_BASE}/matches/results/?page={page}'
        html_str = cached_fetch(url, ttl=300)
        
        # Find all match-item links
        # Pattern: <a href="/645487/team1-vs-team2-..." class="... match-item ...">
        match_blocks = re.findall(
            r'<a\s+href="(/\d+/[^"]+)"\s+class="[^"]*match-item[^"]*"[^>]*>(.*?)</a>',
            html_str, re.DOTALL
        )
        
        for href, block in match_blocks:
            match_id = re.match(r'/(\d+)/', href)
            if not match_id:
                continue
            
            # Extract team names
            teams = re.findall(r'<div class="text-of">\s*(?:<span[^>]*></span>)?\s*([^<]+)', block)
            teams = [t.strip() for t in teams if t.strip()]
            
            # Extract scores
            scores = re.findall(r'match-item-vs-team-score[^>]*>\s*(\d+)\s*<', block)
            
            # Extract event
            event_m = re.search(r'match-item-event text-of[^>]*>.*?</div>\s*([^<]+)', block, re.DOTALL)
            event = ''
            if event_m:
                event = event_m.group(1).strip()
            else:
                event_m2 = re.search(r'match-item-event text-of[^>]*>\s*(?:<div[^>]*>[^<]*</div>)?\s*([^<]+)', block, re.DOTALL)
                if event_m2:
                    event = event_m2.group(1).strip()
            
            all_matches.append({
                'id': match_id.group(1),
                'url': href,
                'team1': teams[0] if len(teams) > 0 else '?',
                'team2': teams[1] if len(teams) > 1 else '?',
                'score1': scores[0] if len(scores) > 0 else '?',
                'score2': scores[1] if len(scores) > 1 else '?',
                'event': html.unescape(event),
            })
    
    return all_matches

# ========== SCRAPER: MATCH DETAIL ==========
def scrape_match_detail(match_id, match_url):
    url = f'{VLR_BASE}{match_url}'
    html_str = cached_fetch(url, ttl=600)
    
    result = {
        'id': match_id,
        'teams': [],
        'event': '',
        'vod': '',
        'maps': []
    }
    
    # Extract VOD link (Youtube/Twitch)
    streams = re.findall(r'<a\s+[^>]*href=["\'](https?://(?:www\.)?(?:youtube\.com|youtu\.be|twitch\.tv)[^"\']+)["\']', html_str)
    for s in streams:
        if 'clip' not in s:  # prioritize full video over clips
            result['vod'] = s
            break
    
    # Extract event name
    event_m = re.search(r'<a\s+href="/event/[^"]*"[^>]*class="[^"]*"[^>]*>\s*<div[^>]*>\s*<div[^>]*>\s*([^<]+)', html_str)
    if event_m:
        result['event'] = event_m.group(1).strip()
    
    # Extract overall team names from match header
    header_teams = re.findall(r'<div class="wf-title-med">\s*([^<]+)', html_str)
    if len(header_teams) >= 2:
        result['teams'] = [t.strip() for t in header_teams[:2]]
    
    # Split by vm-stats-game blocks (each is a map)
    game_blocks = re.split(r'<div class="vm-stats-game\s', html_str)
    
    for gb in game_blocks[1:]:  # skip first (before any game block)
        map_data = {'map_name': 'Unknown', 'team1': '', 'team2': '', 'score': '', 'players': []}
        
        # Get map name from the header
        map_m = re.search(r'<div class="map">\s*<div[^>]*>\s*(?:<span[^>]*>)?\s*(\w+)', gb)
        if map_m:
            map_data['map_name'] = map_m.group(1).strip()
        
        # Get team names & scores from the game header
        team_names = re.findall(r'<div class="team-name">\s*([^<]+)', gb)
        scores = re.findall(r'<div class="score[^"]*"[^>]*>\s*(\d+)', gb)
        
        if len(team_names) >= 2:
            map_data['team1'] = team_names[0].strip()
            map_data['team2'] = team_names[1].strip()
        elif len(result['teams']) >= 2:
            map_data['team1'] = result['teams'][0]
            map_data['team2'] = result['teams'][1]
        
        if len(scores) >= 2:
            map_data['score'] = f"{scores[0]}-{scores[1]}"
        
        # Extract player rows with agent info
        # Each player row has: player name (in mod-player), team tag (in ge-text-light), agent (in mod-agent img title)
        player_rows = re.findall(
            r'<tr>\s*<td class="mod-player"[^>]*>(.*?)</td>\s*<td class="mod-agents">(.*?)</td>',
            gb, re.DOTALL
        )
        
        for player_html, agent_html in player_rows:
            # Player name
            name_m = re.search(r'font-weight:\s*700[^>]*>\s*([^<]+)', player_html)
            player_name = name_m.group(1).strip() if name_m else '?'
            
            # Team tag
            team_m = re.search(r'ge-text-light[^>]*>\s*([^<]+)', player_html)
            team_tag = team_m.group(1).strip() if team_m else ''
            
            # Agent(s)
            agents = re.findall(r'title="([^"]+)"', agent_html)
            
            for agent in agents:
                map_data['players'].append({
                    'player': player_name,
                    'team_tag': team_tag,
                    'agent': agent.title()  # Capitalize first letter
                })
            
            # If no agent found in title, try alt text
            if not agents:
                agents_alt = re.findall(r'alt="([^"]+)"', agent_html)
                for agent in agents_alt:
                    map_data['players'].append({
                        'player': player_name,
                        'team_tag': team_tag,
                        'agent': agent.title()
                    })
        
        # Only add if we have player data
        if map_data['players']:
            result['maps'].append(map_data)
    
    return result

# ========== API ENDPOINTS ==========
def handle_api(path, query):
    if path == '/api/matches':
        pages = int(query.get('pages', ['2'])[0])
        matches = scrape_match_results(num_pages=pages)
        return {'status': 'success', 'count': len(matches), 'matches': matches}
    
    elif path == '/api/match-detail':
        match_id = query.get('id', [''])[0]
        match_url = query.get('url', [''])[0]
        if not match_id or not match_url:
            return {'status': 'error', 'message': 'id and url required'}
        detail = scrape_match_detail(match_id, match_url)
        return {'status': 'success', 'data': detail}
    
    elif path == '/api/full-data':
        # All-in-one: fetch results + details for each match
        pages = int(query.get('pages', ['1'])[0])
        max_matches = int(query.get('max', ['10'])[0])
        
        matches = scrape_match_results(num_pages=pages)[:max_matches]
        results = []
        
        for m in matches:
            try:
                detail = scrape_match_detail(m['id'], m['url'])
                results.append(detail)
            except Exception as e:
                print(f'  [ERROR] Match {m["id"]}: {e}')
        
        return {'status': 'success', 'count': len(results), 'matches': results}
    
    return {'status': 'error', 'message': 'Unknown endpoint'}

# ========== HTTP SERVER ==========
class Handler(http.server.BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', '*')
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        query = urllib.parse.parse_qs(parsed.query)

        # API routes
        if parsed.path.startswith('/api/'):
            try:
                data = handle_api(parsed.path, query)
                body = json.dumps(data, ensure_ascii=False).encode('utf-8')
                self.send_response(200)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(body)
            except Exception as e:
                print(f'  [API ERROR] {e}')
                body = json.dumps({'status': 'error', 'message': str(e)}).encode()
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(body)
            return

        # Static files
        file_path = parsed.path
        if file_path == '/':
            file_path = '/index.html'

        full_path = os.path.normpath(os.path.join(STATIC_DIR, file_path.lstrip('/')))
        if not full_path.startswith(STATIC_DIR):
            self.send_response(403)
            self.end_headers()
            return

        if not os.path.isfile(full_path):
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b'Not Found')
            return

        ext = os.path.splitext(full_path)[1]
        content_type = MIME_TYPES.get(ext, 'application/octet-stream')

        with open(full_path, 'rb') as f:
            data = f.read()

        self.send_response(200)
        self.send_header('Content-Type', content_type)
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, fmt, *args):
        print(f'  {args[0]}')


if __name__ == '__main__':
    server = http.server.HTTPServer(('', PORT), Handler)
    print(f'\n  🎯 Valorant Meta server running at http://localhost:{PORT}')
    print(f'  Static: {STATIC_DIR}')
    print(f'  API:')
    print(f'    GET /api/matches?pages=2       — recent match results')
    print(f'    GET /api/match-detail?id=X&url=Y — single match detail')
    print(f'    GET /api/full-data?pages=1&max=10 — all-in-one\n')
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('\n  Server stopped.')
