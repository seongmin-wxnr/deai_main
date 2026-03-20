import urllib.request
import urllib.error
import urllib.parse
import json

from django.http import JsonResponse
from django.shortcuts import render
from django.conf import settings
from django.core.cache import cache

import requests
# external api define
CACHE_TTL    = 60 * 60 * 6 
DB_TTL_HOURS = 6   

def _db_get(key: str):
    try:
        from .models import RiotDataCache
        return RiotDataCache.get(key)
    except Exception:
        return None

def _db_set(key: str, data, version: str = '', ttl_hours: int = DB_TTL_HOURS):
    try:
        from .models import RiotDataCache
        RiotDataCache.set(key, data, version=version, ttl_hours=ttl_hours)
    except Exception:
        pass

def _db_delete(key: str):
    """DB 캐시 삭제"""
    try:
        from .models import RiotDataCache
        RiotDataCache.delete_key(key)
    except Exception:
        pass

def _cached_get(key: str):
    if key in _MEM_CACHE:
        return _MEM_CACHE[key]
    data = cache.get(key)
    if data is not None:
        _MEM_CACHE[key] = data
        return data
    data = _db_get(key)
    if data is not None:
        _MEM_CACHE[key] = data
        cache.set(key, data, CACHE_TTL)
        return data
    return None

def _cached_set(key: str, data, version: str = ''):
    _MEM_CACHE[key] = data
    cache.set(key, data, CACHE_TTL)
    _db_set(key, data, version=version)

def _cached_delete(key: str):
    _MEM_CACHE.pop(key, None)
    cache.delete(key)
    _db_delete(key)

_MEM_CACHE: dict = {}

def _get(url: str) -> dict:
    req = urllib.request.Request(url, headers={'User-Agent': 'DeaiWeb/1.0'})
    with urllib.request.urlopen(req, timeout=8) as res:
        return json.loads(res.read().decode('utf-8'))
        
## BASE URL OR MAPS
BASE = "https://kr.api.riotgames.com"

## ranking api 

def riot_api_rankingPage(request):
    if request.method != "POST":
        return JsonResponse({
            'success' : False,
            'message' : "잘못된 메서드 접근 입니다.",
        }, status=400)

class RiotAPIError(Exception):
    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        self.message     = message
        super().__init__(message)


def _riot_get(url: str) -> dict:
    req = urllib.request.Request(
        url,
        headers={
            'X-Riot-Token'   : settings.RIOT_API_KEY,
            'User-Agent'     : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Accept-Language': 'ko-KR,ko;q=0.9',
            'Accept-Charset' : 'application/x-www-form-urlencoded; charset=UTF-8',
            'Origin'         : 'https://developer.riotgames.com',
        }
    )
    print(f"[RIOT] 호출 URL: {url}", flush=True)
    print(f"[RIOT] 사용 키: {settings.RIOT_API_KEY[:20]}...", flush=True)
    try:
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            print(f"[RIOT] 성공 응답: {str(data)[:100]}", flush=True)
            return data
    except urllib.error.HTTPError as e:
        body = {}
        try:
            body = json.loads(e.read().decode('utf-8'))
        except Exception:
            pass
        print(f"[RIOT] HTTP 에러: {e.code} / body: {body}", flush=True)
        raise RiotAPIError(e.code, body.get('status', {}).get('message', str(e)))
    except urllib.error.URLError as e:
        print(f"[RIOT] URL 에러: {e.reason}", flush=True)
        raise RiotAPIError(503, f'네트워크 오류: {e.reason}')
    except Exception as e:
        print(f"[RIOT] 알 수 없는 에러: {e}", flush=True)
        raise
def _error_response(e: RiotAPIError) -> JsonResponse:
    messages = {
        400: '잘못된 요청입니다.',
        401: 'API 키 오류입니다.',
        403: 'API 키가 만료되었습니다.',
        404: '소환사를 찾을 수 없습니다.',
        429: '요청 횟수를 초과했습니다. 잠시 후 재시도해주세요.',
        500: 'Riot 서버 오류입니다.',
        503: '네트워크 연결 오류입니다.',
    }
    msg       = messages.get(e.status_code, e.message)
    http_code = e.status_code if e.status_code in [400, 401, 403, 404, 429, 500, 503] else 500
    return JsonResponse(
        {'success': False, 'message': msg, 'riot_status': e.status_code},
        status=http_code
    )

RIOT_API_KEY  = getattr(settings, 'RIOT_API_KEY', '')
# 한국 서버 kr.api.riotgames.com / ASIA 라우팅: asia.api.riotgames.com
LOL_API_BASE  = 'https://kr.api.riotgames.com'
TFT_API_BASE  = 'https://kr.api.riotgames.com'
VAL_API_BASE  = 'https://kr.api.riotgames.com'
ASIA_API_BASE = 'https://asia.api.riotgames.com'
 
def _riot_get(url: str) -> dict:
    """Riot API GET — API 키 헤더 포함"""
    req = urllib.request.Request(
        url,
        headers={
            'User-Agent'    : 'DeaiWeb/1.0',
            'X-Riot-Token'  : RIOT_API_KEY,
            'Accept'        : 'application/json',
        }
    )
    with urllib.request.urlopen(req, timeout=10) as res:
        return json.loads(res.read().decode('utf-8'))
 
def _riot_get_requests(url: str) -> dict:
    try:
        import requests as _req
        resp = _req.get(url, headers={
            'X-Riot-Token': RIOT_API_KEY,
            'Accept'      : 'application/json',
        }, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except ImportError:
        return _riot_get(url)
 
def _format_rank(tier: str, division: str) -> str:
    TIER_KO = {
        'IRON':'아이언','BRONZE':'브론즈','SILVER':'실버','GOLD':'골드',
        'PLATINUM':'플래티넘','EMERALD':'에메랄드','DIAMOND':'다이아몬드',
        'MASTER':'마스터','GRANDMASTER':'그랜드마스터','CHALLENGER':'챌린저',
    }
    if not tier:
        return '챌린저'   # tier )
    label = TIER_KO.get(tier.upper(), tier)
    if tier.upper() in ('MASTER', 'GRANDMASTER', 'CHALLENGER'):
        return label
    return f'{label} {division}'
 
 
def _entries_to_list(entries: list, tier_from_parent: str = '', limit: int = 200) -> list:
    entries.sort(key=lambda e: (-e.get('leaguePoints', 0)))
    result = []
    tier = tier_from_parent.upper()
    for rank, e in enumerate(entries[:limit], 1):
        div     = e.get('rank', '')
        wins    = e.get('wins', 0)
        losses  = e.get('losses', 0)
        total   = wins + losses
        winrate = round(wins / total * 100) if total else 0
        name    = (e.get('riotIdGameName') or e.get('summonerName') or '').strip()
        tag     = (e.get('riotIdTagline')  or '').strip()
        puuid   = e.get('puuid', '')

        result.append({
            'rank'      : rank,
            'summonerId': e.get('summonerId', ''),
            'puuid'     : puuid,
            'name'      : name if name else '?',
            'tagLine'   : tag,
            'iconId'    : 1, 
            'tier'      : tier,
            'division'  : div,
            'rankLabel' : _format_rank(tier, div),
            'lp'        : e.get('leaguePoints', 0),
            'wins'      : wins,
            'losses'    : losses,
            'winrate'   : winrate,
            'hotStreak' : e.get('hotStreak', False),
            'veteran'   : e.get('veteran', False),
            'freshBlood': e.get('freshBlood', False),
        })
    return result


def _resolve_names_by_puuid(entries: list, max_resolve: int = 500) -> list:
    ASIA_BASE = 'https://asia.api.riotgames.com'

    if not hasattr(_resolve_names_by_puuid, '_cache'):
        _resolve_names_by_puuid._cache = {}
    name_cache = _resolve_names_by_puuid._cache

    to_resolve = [
        e for e in entries[:max_resolve]
        if (e['name'] == '?' or e.get('iconId', 1) == 1)
        and e.get('puuid')
        and e['puuid'] not in name_cache
    ]

    # 캐시에서 이미 아는 것 먼저 채우기
    for e in entries[:max_resolve]:
        puuid = e.get('puuid', '')
        if puuid and puuid in name_cache:
            cached = name_cache[puuid]
            if cached.get('name'):
                e['name']      = cached['name']
                e['tagLine']   = cached['tagLine']
                e['iconId']    = cached.get('iconId', 1)
                e['rankLabel'] = _format_rank(e['tier'], e['division'])

    if not to_resolve:
        return entries

    from concurrent.futures import ThreadPoolExecutor, as_completed

    def fetch_info(e):
        puuid = e['puuid']
        try:
            # 1) ASIA: 이름/태그 조회
            url       = f'{ASIA_BASE}/riot/account/v1/accounts/by-puuid/{puuid}'
            acc       = _riot_get_requests(url)
            game_name = acc.get('gameName', '')
            tag_line  = acc.get('tagLine', '')
            icon_id = 1
            try:
                s_url   = f'{LOL_API_BASE}/lol/summoner/v4/summoners/by-puuid/{puuid}'
                s_data  = _riot_get_requests(s_url)
                icon_id = s_data.get('profileIconId', 1)
            except Exception:
                pass

            return puuid, game_name, tag_line, icon_id
        except Exception:
            return puuid, '', '', 1

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(fetch_info, e): e for e in to_resolve}
        for future in as_completed(futures):
            e = futures[future]
            puuid, game_name, tag_line, icon_id = future.result()
            if game_name:
                e['name']      = game_name
                e['tagLine']   = tag_line
                e['iconId']    = icon_id
                e['rankLabel'] = _format_rank(e['tier'], e['division'])
                name_cache[puuid] = {
                    'name'   : game_name,
                    'tagLine': tag_line,
                    'iconId' : icon_id,
                }

    return entries 


def info_lol_ranking(request):
    queue = request.GET.get('queue', 'RANKED_SOLO_5x5')
    tier  = request.GET.get('tier', 'challenger').lower()
    cache_key = f'lol_ranking_{queue}_{tier}'
 
    cached = _cached_get(cache_key)
    if cached:
        return JsonResponse(cached)
 
    if not RIOT_API_KEY:
        return JsonResponse({'success': False, 'message': 'API 키 미설정'}, status=500)
 
    try:
        TIER_EP = {
            'challenger'  : 'challengerleagues',
            'grandmaster' : 'grandmasterleagues',
            'master'      : 'masterleagues',
        }
        ep = TIER_EP.get(tier, 'challengerleagues')
        url  = f'{LOL_API_BASE}/lol/league/v4/{ep}/by-queue/{queue}'
        data = _riot_get_requests(url)
 
        entries  = data.get('entries', [])
        tier_str = data.get('tier', tier.upper())
        ranked   = _entries_to_list(entries, tier_from_parent=tier_str, limit=500)
        ranked   = _resolve_names_by_puuid(ranked, max_resolve=500)
        result   = {
            'success' : True,
            'queue'   : queue,
            'tier'    : tier_str,
            'total'   : len(ranked),
            'entries' : ranked,
        }
        _MEM_CACHE[cache_key] = result
        cache.set(cache_key, result, 60 * 60)
        _db_set(cache_key, result, ttl_hours=1)
        return JsonResponse(result)

    except RiotAPIError as e:
        return _error_response(e)
    except Exception as e:
        print(f'[LOL RANKING] {e}')
        return JsonResponse({'success': False, 'message': str(e)}, status=500)

def info_tft_ranking(request):
    queue = request.GET.get('queue', 'RANKED_TFT')
    tier  = request.GET.get('tier', 'challenger').lower()
    cache_key = f'tft_ranking_{queue}_{tier}'
 
    cached = _cached_get(cache_key)
    if cached:
        return JsonResponse(cached)
 
    if not RIOT_API_KEY:
        return JsonResponse({'success': False, 'message': 'API 키 미설정'}, status=500)
 
    try:
        TIER_EP = {
            'challenger'  : 'challenger',
            'grandmaster' : 'grandmaster',
            'master'      : 'master',
        }
        ep   = TIER_EP.get(tier, 'challenger')
        url  = f'{TFT_API_BASE}/tft/league/v1/{ep}?queue={queue}'
        data = _riot_get_requests(url)
 
        entries = data.get('entries', [])
        tier_str = data.get('tier', tier.upper())
        ranked  = _entries_to_list(entries, tier_from_parent=tier_str, limit=500)
        ranked  = _resolve_names_by_puuid(ranked, max_resolve=500)
        result  = {
            'success' : True,
            'queue'   : queue,
            'tier'    : tier_str,
            'total'   : len(ranked),
            'entries' : ranked,
        }
        _MEM_CACHE[cache_key] = result
        cache.set(cache_key, result, 60 * 60)
        _db_set(cache_key, result, ttl_hours=1)
        return JsonResponse(result)
 
    except Exception as e:
        print(f'[TFT RANKING] {e}')
        return JsonResponse({'success': False, 'message': str(e)}, status=500)
def info_val_ranking(request):
    cache_key = 'val_ranking_kr'
    cached = _cached_get(cache_key)
    if cached:
        return JsonResponse(cached)
 
    if not RIOT_API_KEY:
        return JsonResponse({'success': False, 'message': 'API 키 미설정'}, status=500)
 
    try:
        import re as _re
        content_url  = f'{VAL_API_BASE}/val/content/v1/contents?locale=ko-KR'
        content_data = _riot_get_requests(content_url)
        acts = content_data.get('acts', [])
        current_act = next((a for a in acts if a.get('isActive')), None)
        if not current_act:
            current_act = acts[-1] if acts else {}
        act_id = current_act.get('id', '')
 
        if not act_id:
            return JsonResponse({'success': False, 'message': 'Act ID 조회 실패'}, status=500)

        lb_url = f'{VAL_API_BASE}/val/ranked/v1/leaderboards/by-act/{act_id}?size=200&startIndex=0'
        lb_data = _riot_get_requests(lb_url)
 
        players = lb_data.get('players', [])
        RANK_LABELS = {
            27: '레디언트', 26: '이모탈 3', 25: '이모탈 2', 24: '이모탈 1',
            23: '다이아 3',  22: '다이아 2',  21: '다이아 1',
        }
        entries = []
        for p in players:
            rank_num  = p.get('competitiveTier', 0)
            rank_name = RANK_LABELS.get(rank_num, f'Tier {rank_num}')
            entries.append({
                'rank'       : p.get('leaderboardRank', 0),
                'name'       : p.get('gameName', '?'),
                'tagLine'    : p.get('tagLine', ''),
                'rankLabel'  : rank_name,
                'lp'         : p.get('rankedRating', 0),
                'wins'       : p.get('numberOfWins', 0),
                'losses'     : 0,
                'winrate'    : 0,
                'tier'       : 'RADIANT' if rank_num == 27 else 'IMMORTAL',
            })
 
        result = {
            'success'  : True,
            'actId'    : act_id,
            'actName'  : current_act.get('name', ''),
            'total'    : len(entries),
            'entries'  : entries,
        }
        _cached_set(cache_key, result)
        return JsonResponse(result)
 
    except Exception as e:
        print(f'[VAL RANKING] {e}')
        return JsonResponse({'success': False, 'message': str(e)}, status=500)


def riot_api_rankRendering(request):
    if request.method != 'GET':
        return JsonResponse({
            'success' : False,
            'message' : "올바르지 않은 요청입니다.",
        }, status=400)
    try:
        return render(request, 'riot_ranking.html')
    except Exception as e:
        return JsonResponse({
            'success' : False,
            'message' : f'{e}',
        })

def info_ranking_cache_clear(request):
    from django.core.cache import cache as djcache
    keys = [
        'lol_ranking_RANKED_SOLO_5x5_challenger',
        'lol_ranking_RANKED_SOLO_5x5_grandmaster',
        'lol_ranking_RANKED_SOLO_5x5_master',
        'lol_ranking_RANKED_FLEX_SR_challenger',
        'lol_ranking_RANKED_FLEX_SR_grandmaster',
        'lol_ranking_RANKED_FLEX_SR_master',
        'tft_ranking_RANKED_TFT_challenger',
        'tft_ranking_RANKED_TFT_grandmaster',
        'tft_ranking_RANKED_TFT_master',
        'tft_ranking_RANKED_TFT_DOUBLE_UP_challenger',
        'tft_ranking_RANKED_TFT_DOUBLE_UP_grandmaster',
        'tft_ranking_RANKED_TFT_DOUBLE_UP_master',
        'val_ranking_kr',
    ]
    cleared = []
    for key in keys:
        _MEM_CACHE.pop(key, None)
        djcache.delete(key)
        _db_delete(key)
        cleared.append(key)
    if hasattr(_resolve_names_by_puuid, '_cache'):
        _resolve_names_by_puuid._cache.clear()
    return JsonResponse({'success': True, 'cleared': cleared, 'count': len(cleared)})


def info_lol_ranking_debug(request):
    if not RIOT_API_KEY:
        return JsonResponse({'error': 'no api key'})
    try:
        url  = f'{LOL_API_BASE}/lol/league/v4/challengerleagues/by-queue/RANKED_SOLO_5x5'
        data = _riot_get_requests(url)
        entries = data.get('entries', [])
        first = entries[0] if entries else {}
        return JsonResponse({
            'tier_in_root': data.get('tier'),
            'name_in_root': data.get('name'),
            'entry_keys'  : list(first.keys()),
            'first_entry' : first,
            'total'       : len(entries),
        })
    except Exception as e:
        return JsonResponse({'error': str(e)})
def info_mastery_by_puuid(request):
    """
    puuid 로 숙련도 상위 3 챔피언 조회
    GET /api/ranking/mastery/?puuid=xxx&game=lol|tft
    """
    puuid = request.GET.get('puuid', '').strip()
    game  = request.GET.get('game', 'lol')
    if not puuid:
        return JsonResponse({'success': False, 'message': 'puuid 필요'}, status=400)

    cache_key = f'mastery_{game}_{puuid}'
    cached    = _cached_get(cache_key)
    if cached:
        return JsonResponse(cached)

    if not RIOT_API_KEY:
        return JsonResponse({'success': False, 'message': 'API 키 미설정'}, status=500)

    try:
        # LoL: puuid로 직접 숙련도 조회 가능
        # TFT: summoner 거쳐서 조회
        if game == 'tft':
            summoner_url = f'{TFT_API_BASE}/tft/summoner/v1/summoners/by-puuid/{puuid}'
            summoner     = _riot_get_requests(summoner_url)
            summoner_id  = summoner.get('id', '')
            mastery_url  = f'{TFT_API_BASE}/tft/champion-mastery/v1/by-summoner/{summoner_id}/top?count=3'
        else:
            # LoL v4 
            mastery_url = f'{LOL_API_BASE}/lol/champion-mastery/v4/by-puuid/{puuid}/top?count=3'

        masteries = _riot_get_requests(mastery_url)

        # ddragon 버전
        try:
            ver_data = _riot_get_requests('https://ddragon.leagueoflegends.com/api/versions.json')
            dd_ver   = ver_data[0] if ver_data else '15.1.1'
        except Exception:
            dd_ver = '15.1.1'

        # championId
        try:
            champ_data = _riot_get_requests(
                f'https://ddragon.leagueoflegends.com/cdn/{dd_ver}/data/ko_KR/champion.json'
            )
            id_to_key = {
                int(c['key']): c['id']
                for c in champ_data.get('data', {}).values()
                if c.get('key', '').isdigit()
            }
        except Exception:
            id_to_key = {}

        champs = []
        for m in masteries[:3]:
            cid  = m.get('championId', 0)
            pts  = m.get('championPoints', 0)
            ckey = id_to_key.get(cid, '')
            img  = (f'https://ddragon.leagueoflegends.com/cdn/{dd_ver}/img/champion/{ckey}.png'
                    if ckey else '')
            champs.append({
                'championId'  : cid,
                'championKey' : ckey,
                'points'      : pts,
                'img'         : img,
            })

        result = {'success': True, 'champions': champs}
        _cached_set(cache_key, result)
        return JsonResponse(result)

    except RiotAPIError as e:
        return _error_response(e)
    except Exception as e:
        print(f'[MASTERY] {e}')
        return JsonResponse({'success': False, 'message': str(e)}, status=500)
