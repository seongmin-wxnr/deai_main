import urllib.request
import urllib.error
import urllib.parse
import json
import re

from django.http      import JsonResponse
from django.shortcuts import render
from django.conf      import settings

_COMPANION_CACHE: dict = {} 
_COMPANION_LOADED: bool = False

_CDRAGON_COMPANIONS_URL = (
    'https://raw.communitydragon.org/latest/plugins/'
    'rcp-be-lol-game-data/global/default/v1/companions.json'
)
_CDRAGON_PLUGIN_BASE = (
    'https://raw.communitydragon.org/latest/plugins/'
    'rcp-be-lol-game-data/global/default'
)


def _load_companion_cache() -> None:
    """CDragon companions.json 로드 → content_id 기준 캐시 구축."""
    global _COMPANION_CACHE, _COMPANION_LOADED
    if _COMPANION_LOADED:
        return
    try:
        req = urllib.request.Request(
            _CDRAGON_COMPANIONS_URL,
            headers={'User-Agent': 'Mozilla/5.0'}
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            companions = json.loads(resp.read().decode('utf-8'))
        for c in companions:
            cid  = c.get('contentId', '')
            icon = c.get('loadoutsIcon', '')
            if not cid or not icon:
                continue
            path = icon.replace('/lol-game-data/assets', '').lower()
            _COMPANION_CACHE[cid] = _CDRAGON_PLUGIN_BASE + path
        _COMPANION_LOADED = True
        print(f'[TFT] companion cache loaded: {len(_COMPANION_CACHE)} items', flush=True)
    except Exception as ex:
        print(f'[TFT] companion cache load failed: {ex}', flush=True)


def _companion_img_url(content_id: str) -> str:
    """content_ID(UUID) → CDragon 전술가 이미지 URL. 캐시 미스 시 빈 문자열."""
    _load_companion_cache()
    return _COMPANION_CACHE.get(content_id, '')

TFT_QUEUE_KO = {
    'RANKED_TFT': '랭크',
    'RANKED_TFT_TURBO': '하이퍼롤',
    'NORMAL_TFT'  : '일반',
    'RANKED_TFT_PAIRS' : '듀오전',
    'RANKED_TFT_DOUBLE_UP' : '더블업',
}

TFT_TIER_KO = {
    'IRON': '아이언', 'BRONZE': '브론즈', 'SILVER': '실버',
    'GOLD': '골드', 'PLATINUM': '플래티넘', 'EMERALD': '에메랄드',
    'DIAMOND': '다이아몬드', 'MASTER': '마스터',
    'GRANDMASTER': '그랜드마스터', 'CHALLENGER': '챌린저',
}


def _clean_augment(aug_id: str) -> str:
    name = re.sub(r'^TFT\d*_Augment_', '', aug_id)
    name = re.sub(r'^TFT\d*_Item_',    '', name)
    name = re.sub(r'(?<=[a-z])(?=[A-Z])', ' ', name)
    name = re.sub(r'(?<=[A-Z])(?=[A-Z][a-z])', ' ', name)
    return name.strip()


def _trait_style_name(style: int) -> str:
    return ['', 'bronze', 'silver', 'gold', 'chromatic'][min(style, 4)]


def _placement_str(p: int) -> str:
    return {1:'1위',2:'2위',3:'3위',4:'4위',5:'5위',6:'6위',7:'7위',8:'8위'}.get(p, f'{p}위')


def _tier_emblem_url(tier: str) -> str:
    return (
        f'https://raw.communitydragon.org/latest/plugins/rcp-fe-lol-static-assets/'
        f'global/default/images/ranked-emblem/emblem-{tier.lower()}.png'
    )
class RiotAPIError(Exception):
    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        self.message     = message
        super().__init__(message)


def _handle_error(e: RiotAPIError) -> JsonResponse:
    MESSAGES = {
        400: '잘못된 요청입니다.',
        401: 'API 키 오류입니다.',
        403: 'API 키가 만료되었거나 권한이 없습니다.',
        404: '플레이어를 찾을 수 없습니다.',
        429: '요청 횟수를 초과했습니다. 잠시 후 재시도해주세요.',
        500: 'Riot 서버 오류입니다.',
        503: '네트워크 연결 오류입니다.',
    }
    msg = MESSAGES.get(e.status_code, e.message)
    return JsonResponse(
        {'success': False, 'message': msg, 'riot_status': e.status_code},
        status=200
    )


def _riot_get(url: str) -> dict:
    req = urllib.request.Request(
        url,
        headers={
            'X-Riot-Token': settings.RIOT_API_KEY,
            'User-Agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
            'Accept-Language': 'ko-KR,ko;q=0.9',
            'Accept-Charse' : 'application/x-www-form-urlencoded; charset=UTF-8',
            'Origin' : 'https://developer.riotgames.com',
        }
    )
    print(f"[TFT DEBUG] -> {url}", flush=True)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            print(f"[TFT DEBUG] -> s {str(data)[:120]}", flush=True)
            return data
    except urllib.error.HTTPError as e:
        body = {}
        try:
            body = json.loads(e.read().decode('utf-8'))
        except Exception:
            pass
        print(f"[TFT DEBUG] -> f HTTP {e.code}: {body}", flush=True)
        raise RiotAPIError(e.code, body.get('status', {}).get('message', str(e)))
    except urllib.error.URLError as e:
        print(f"[[TFT DEBUG] -> f: {e.reason}", flush=True)
        raise RiotAPIError(503, f'네트워크 오류: {e.reason}')


def _get_region_urls(region: str) -> tuple:
    info = settings.RIOT_REGION_MAP.get(region.lower())
    if not info:
        raise RiotAPIError(400, f'지원하지 않는 지역: {region}')
    return info['platform'], info['regional']


def tft_page_rendering(request):
    if not request.session.get('user_id'):
        return render(request, 'login.html')
    return render(request, 'riot_tftUserpage.html', {
        'DD_VERSION': settings.RIOT_DD_VERSION,
    })

# GET /api/tft/account/?name=...&tag=...&region=...
def tft_api_search_account(request):
    if request.method != 'GET':
        return JsonResponse({'success': False, 'message': '잘못된 메서드입니다.'}, status=405)

    name= request.GET.get('name','').strip()
    tag = request.GET.get('tag',  '').strip()
    region = request.GET.get('region','kr').strip().lower()

    if not name or not tag:
        return JsonResponse({'success': False, 'message': '이름과 태그를 입력해주세요.'}, status=400)

    try:
        platform, regional = _get_region_urls(region)

        # Riot Account 조회
        account = _riot_get(
            f'https://{regional}/riot/account/v1/accounts/by-riot-id'
            f'/{urllib.parse.quote(name)}/{urllib.parse.quote(tag)}'
        )
        puuid = account['puuid']

        # TFT 소환사 조회
        summoner = _riot_get(
            f'https://{platform}/tft/summoner/v1/summoners/by-puuid/{puuid}'
        )

        return JsonResponse({
            'success' : True,
            'gameName' : account.get('gameName', name),
            'tagLine' : account.get('tagLine',  tag),
            'puuid' : puuid,
            'summonerId' : summoner.get('id', ''),
            'profileIconId': summoner.get('profileIconId', 1),
            'summonerLevel': summoner.get('summonerLevel', 0),
        })

    except RiotAPIError as e:
        return _handle_error(e)
    except Exception as e:
        print(f"[TFT] account 예외: {e}", flush=True)
        return JsonResponse({'success': False, 'message': str(e)}, status=200)


# GET /api/tft/rank/?summonerId=...&region=...
def tft_api_getRank(request):
    if request.method != 'GET':
        return JsonResponse({'success': False, 'message': '잘못된 메서드입니다.'}, status=405)
    print("[TFT DEBUG] -> RANK 조회 메서드 접속됌.")
    summoner_id = request.GET.get('summonerId', '').strip()
    puuid = request.GET.get('puuid', '').strip()
    region = request.GET.get('region','kr').strip().lower()

    if not summoner_id and not puuid:
        return JsonResponse({'success': False, 'message': 'summonerId 또는 puuid가 필요합니다.'}, status=400)
    print(f"[TFT DEBUG] -> {summoner_id} : {puuid} : {region}")
    try:
        platform, _ = _get_region_urls(region)
        if not summoner_id and puuid:
            print(f"[TFT] summonerId 없음 -> puuid로 소환사 재조회", flush=True)
            summoner = _riot_get(
                f'https://{platform}/tft/summoner/v1/summoners/by-puuid/{puuid}'
            )
            summoner_id = summoner.get('id', '')

        if not summoner_id:
            return JsonResponse({'success': True, 'ranks': []})

        entries = _riot_get(
            f'https://{platform}/tft/league/v1/entries/by-summoner/{summoner_id}'
        )

        ranks = []
        print(f"[TFT DEBUG] -> 발견된 유저")
        for e in entries:
            tier   = e.get('tier','UNRANKED')
            wins   = e.get('wins',0)
            losses = e.get('losses',0)
            total  = wins + losses
            wr     = round(wins / total * 100, 1) if total else 0

            ranks.append({
                'queueType': e.get('queueType', ''),
                'queueName': TFT_QUEUE_KO.get(e.get('queueType', ''), e.get('queueType', '')),
                'tier' : tier,
                'tierKo': TFT_TIER_KO.get(tier, tier),
                'rank': e.get('rank', ''),
                'lp' : e.get('leaguePoints', 0),
                'wins' : wins,
                'losses' : losses,
                'winRate' : wr,
                'hotStreak': e.get('hotStreak',  False),
                'veteran' : e.get('veteran',    False),
                'freshBlood': e.get('freshBlood', False),
                'emblemUrl': _tier_emblem_url(tier),
            })
        print(f"[TFT DEBUG] -> {ranks} returned")
        return JsonResponse({'success': True, 'ranks': ranks})

    except RiotAPIError as e:
        return _handle_error(e)
    except Exception as e:
        print(f"[TFT] rank 예외: {e}", flush=True)
        return JsonResponse({'success': False, 'message': str(e)}, status=200)


# GET /api/tft/matches/?puuid=...&region=...&count=20
def tft_api_getMatchIDs(request):
    if request.method != 'GET':
        return JsonResponse({'success': False, 'message': '잘못된 메서드입니다.'}, status=405)

    puuid  = request.GET.get('puuid',  '').strip()
    region = request.GET.get('region', 'kr').strip().lower()
    count  = min(int(request.GET.get('count', 20)), 100)

    if not puuid:
        return JsonResponse({'success': False, 'message': 'puuid가 필요합니다.'}, status=400)

    try:
        _, regional = _get_region_urls(region)

        data = _riot_get(
            f'https://{regional}/tft/match/v1/matches/by-puuid/{puuid}/ids?count={count}'
        )
        return JsonResponse({
            'success'  : True,
            'matchIds' : data if isinstance(data, list) else [],
        })

    except RiotAPIError as e:
        return _handle_error(e)
    except Exception as e:
        print(f"[TFT] matchlist 예외: {e}", flush=True)
        return JsonResponse({'success': False, 'message': str(e)}, status=200)


# GET /api/tft/match/<match_id>/?region=...
# {
#   success,
#   match: {
#     matchInfo: { matchId, gameLength, tftSetNumber, tftSetCoreName,
#                  queueType, queueName, gameDate },
#     participants: [{
#       puuid, riotIdGameName, riotIdTagline,
#       placement, placementStr, isTop4,
#       level, lastRound,
#       augments: [{id, name}],
#       traits:   [{name, numUnits, style, styleName}],   ← 활성화된 것만
#       units:    [{characterId, name, tier, rarity, itemNames}],
#       stats:    { totalDamage, playersEliminated, goldLeft }
#     }]
#   }
# }
def tft_api_matchDetail(request, match_id):
    if request.method != 'GET':
        return JsonResponse({'success': False, 'message': '잘못된 메서드입니다.'}, status=405)

    region = request.GET.get('region', 'kr').strip().lower()

    try:
        _, regional = _get_region_urls(region)
        raw = _riot_get(f'https://{regional}/tft/match/v1/matches/{match_id}')
        info = raw.get('info', {})
        raw_parts = info.get('participants', [])
        queue_type = info.get('tft_game_type', '')
        match_info = {
            'matchId': raw.get('metadata', {}).get('match_id', match_id),
            'gameLength': round(info.get('game_length', 0)),
            'tftSetNumber': info.get('tft_set_number',    0),
            'tftSetCoreName': info.get('tft_set_core_name', ''),
            'queueType': queue_type,
            'queueName': TFT_QUEUE_KO.get(queue_type, queue_type or '일반'),
            'gameDate': info.get('game_datetime', 0),
        }
        participants = []
        for p in raw_parts:

            # 증강
            augments = [
                {'id': a, 'name': _clean_augment(a)}
                for a in p.get('augments', [])
            ]

            UNIQUE_IDS = {
                'TFT16_SylasTrait', 'TFT16_ShyvanaUnique', 'TFT16_KaisaUnique',
                'TFT16_XerathUnique', 'TFT16_KindredUnique', 'TFT16_ZaahenTrait',
                'TFT16_Heroic', 'TFT16_Blacksmith', 'TFT16_DarkChild',
                'TFT16_Emperor', 'TFT16_Caretaker', 'TFT16_Glutton',
                'TFT16_Huntress', 'TFT16_HexMech', 'TFT16_Harvester',
                'TFT16_Chronokeeper', 'TFT16_DarkinWeapon',
            }
            traits = []
            for t in p.get('traits', []):
                style    = t.get('style', 0)
                tier_tot = t.get('tier_total', 0)
                raw_name = t.get('name','')
                # unique 트레이트 제외
                if raw_name in UNIQUE_IDS:
                    continue
                # 비활성화 or tier 없음 제외
                if style <= 0 or tier_tot <= 0:
                    continue
                traits.append({
                    'name': raw_name,
                    'numUnits' : t.get('num_units', 0),
                    'style': style,
                    'styleName' : _trait_style_name(style),
                    'tierCurrent': t.get('tier_current', 0),
                    'tierTotal': tier_tot,
                })
            traits.sort(key=lambda x: x['style'], reverse=True)
            units = []
            for u in p.get('units', []):
                units.append({
                    'characterId': u.get('character_id', ''),
                    'name' : u.get('name', u.get('character_id', '').split('_')[-1]),
                    'tier': u.get('tier',   1),
                    'rarity' : u.get('rarity', 0),
                    'itemNames': u.get('itemNames', []),
                })
            units.sort(key=lambda x: (x['rarity'], x['tier']), reverse=True)

            companion= p.get('companion', {})
            content_id = companion.get('content_ID', '')
            companion_url = _companion_img_url(content_id) if content_id else ''

            placement = p.get('placement', 0)
            participants.append({
                'puuid' : p.get('puuid', ''),
                'riotIdGameName': p.get('riotIdGameName', ''),
                'riotIdTagline' : p.get('riotIdTagline',  ''),
                'placement' : placement,
                'placementStr' : _placement_str(placement),
                'isTop4': placement <= 4,
                'level' : p.get('level', 0),
                'lastRound' : p.get('last_round', 0),
                'augments': augments,
                'traits' : traits[:6],
                'units' : units,
                'companionImgUrl': companion_url,
                'stats': {
                    'totalDamage': p.get('total_damage_to_players', 0),
                    'playersEliminated': p.get('players_eliminated', 0),
                    'goldLeft' : p.get('gold_left', 0),
                },
            })

        participants.sort(key=lambda x: x['placement'])

        return JsonResponse({
            'success': True,
            'match': {
                'matchInfo': match_info,
                'participants': participants,
            }
        })

    except RiotAPIError as e:
        return _handle_error(e)
    except Exception as e:
        print(f"[TFT] match detail 예외: {e}", flush=True)

        return JsonResponse({'success': False, 'message': str(e)}, status=200)
