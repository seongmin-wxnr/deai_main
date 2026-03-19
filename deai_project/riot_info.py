import urllib.request
import urllib.error
import urllib.parse
import json

from django.http import JsonResponse
from django.shortcuts import render
from django.conf import settings
from django.core.cache import cache

DDRAGON_BASE = 'https://ddragon.leagueoflegends.com'
CACHE_TTL    = 60 * 60 * 6   # 6시간 캐시

def _get(url: str) -> dict:
    req = urllib.request.Request(url, headers={'User-Agent': 'DeaiWeb/1.0'})
    with urllib.request.urlopen(req, timeout=8) as res:
        return json.loads(res.read().decode('utf-8'))

def _dd_version() -> str:
    cached = cache.get('ddragon_version')
    if cached:
        return cached
    versions = _get(f'{DDRAGON_BASE}/api/versions.json')
    ver = versions[0]
    cache.set('ddragon_version', ver, 60 * 60 * 24)
    return ver

TAG_TO_CLASS = {
    'Fighter'  : '브루저',
    'Tank'     : '탱커',
    'Mage'     : '마법사',
    'Assassin' : '암살자',
    'Marksman' : '원거리딜러',
    'Support'  : '서포터',
}

ARENA_ITEMS = {
    663039 : "아트마의 심판",
    663056 : "불사대마왕의 왕관",
    663058 : "용암의 방패",
    663060 : "신성의 검",
    663172 : "서풍",
    664011 : '꽃피는 새벽의 검',
    664644 : '부서진 여왕의 왕관',
    667101 : '도박꾼의 칼날',
    667109 : '잔혹 행위',
    667112 : '살점포식자',
    663059 : '별빛밤 망토',
    4636   : '밤의 수확자',
    663146 : '마법공학 총검',
}

# sync
ARENA_LEGENDARY_ITEMS = {
    3193 : '가고일 돌갑옷',
}

# force parsing
FORCE_LEGENDARY_ITEMS = {
    3031 : '무한의 대검',
    3089 : '라바돈의 죽음모자',
    3193 : '가고일 돌갑옷', 
}

# 칼바람 전용 아이템
ARAM_ITEMS = {
    2051 : '수호자의 뿔피리',
    3112 : '수호자의 보주',
    3177 : '수호자의 검',
    3184 : '수호자의 망치',
}

EXCLUDE_ITEM_IDS_HARD = {
    663074,  # 베이가의 승천의 부적 :: bot mode
    3011,    # 화학공학 부패기 :: del
}

EXCLUDE_ITEM_IDS = set(ARENA_ITEMS.keys()) | set(ARAM_ITEMS.keys()) | EXCLUDE_ITEM_IDS_HARD

def _item_type(item: dict, item_id: int = 0) -> str:
    tags  = item.get('tags', [])
    depth = item.get('depth', 1)
    maps  = item.get('maps', {})

    # exclude -> deleted or tft 
    if item_id in EXCLUDE_ITEM_IDS_HARD:
        return None
    # arena - legendary cate -> l
    if item_id in ARENA_LEGENDARY_ITEMS:
        return 'arena_legendary'
    # depth effect : NOT
    if item_id in FORCE_LEGENDARY_ITEMS:
        return 'legendary'
    # ARENA
    if item_id in ARENA_ITEMS:
        return 'arena'
    # ARAM
    if item_id in ARAM_ITEMS:
        return 'aram'
    if item_id in EXCLUDE_ITEM_IDS:
        return None
    if not maps.get('11', True):
        return None
    if item.get('requiredChampion') or item.get('requiredAlly'):
        return None
    if 'Consumable' in tags or 'Trinket' in tags or 'Boots' in tags:
        return None
    if 'Mythic' in tags or (depth and depth >= 3):
        return 'legendary'
    if depth and depth == 2:
        return 'entry'
    if depth and depth == 1 and item.get('gold', {}).get('purchasable', False):
        return 'entry'
    return None

def infoPageRender(request):
    if request.method != 'GET':
        return JsonResponse({'success': False, 'message': '잘못된 메서드입니다.'}, status=405)
    try:
        return render(request, 'riot_infoPage.html')
    except Exception as e:
        print(f'[INFO PAGE] -> {e}')
        return JsonResponse({'success': False, 'message': f'오류: {e}'}, status=400)

## version return

def info_dd_version(request):
    try:
        ver = _dd_version()
        return JsonResponse({'success': True, 'version': ver})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)

def info_cache_clear(request):
    try:
        cleared = []
        import hashlib
        mapping_sig = str(sorted(EXCLUDE_ITEM_IDS_HARD) + sorted(ARENA_LEGENDARY_ITEMS) + sorted(FORCE_LEGENDARY_ITEMS) + sorted(ARENA_ITEMS) + sorted(ARAM_ITEMS))
        mapping_hash = hashlib.md5(mapping_sig.encode()).hexdigest()[:8]
        keys_to_delete = []
        for lang in ['ko_KR', 'en_US']:
            keys_to_delete += [
                f'info_lol_items_{lang}',           # 구버전 키
                f'info_lol_items_{lang}_{mapping_hash}',  # 신버전 키
                f'info_lol_champs_{lang}',
                f'info_tft_champs_{lang}',
                f'info_tft_items_{lang}',
            ]
            for h in ['00000000','aaaaaaaa','ffffffff']:
                keys_to_delete.append(f'info_lol_items_{lang}_{h}')
        keys_to_delete.append('ddragon_version')
        for key in keys_to_delete:
            cache.delete(key)
            cleared.append(key)
        return JsonResponse({'success': True, 'cleared': cleared, 'count': len(cleared)})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)


## import lol champs .. 

def info_lol_champions(request):
    lang = request.GET.get('lang', 'ko_KR')
    cache_key = f'info_lol_champs_{lang}'
    cached = cache.get(cache_key)
    if cached:
        return JsonResponse(cached)

    try:
        ver   = _dd_version()
        data  = _get(f'{DDRAGON_BASE}/cdn/{ver}/data/{lang}/champion.json')
        champs = []
        for key, c in data.get('data', {}).items():
            tags = c.get('tags', [])
            primary_class = TAG_TO_CLASS.get(tags[0], 'fighter') if tags else 'fighter'
            champs.append({
                'id': key,
                'name': c.get('name', key),
                'title': c.get('title', ''),
                'class': primary_class,
                'tags': [TAG_TO_CLASS.get(t, t.lower()) for t in tags],
                'blurb': c.get('blurb', ''),
                'img': f'{DDRAGON_BASE}/cdn/{ver}/img/champion/{key}.png',
                'splash': f'{DDRAGON_BASE}/cdn/img/champion/splash/{key}_0.jpg',
            })
        champs.sort(key=lambda x: x['name'])
        result = {'success': True, 'version': ver, 'champions': champs}
        cache.set(cache_key, result, CACHE_TTL)
        return JsonResponse(result)

    except Exception as e:
        print(f'[INFO LOL CHAMPS] {e}')
        return JsonResponse({'success': False, 'message': str(e)}, status=500)

## lol item list

def info_lol_items(request):
    lang = request.GET.get('lang', 'ko_KR')
    # 매핑 딕셔너리가 바뀌면 캐시 자동 무효화
    mapping_sig = str(sorted(EXCLUDE_ITEM_IDS_HARD) + sorted(ARENA_LEGENDARY_ITEMS) + sorted(FORCE_LEGENDARY_ITEMS) + sorted(ARENA_ITEMS) + sorted(ARAM_ITEMS))
    import hashlib
    mapping_hash = hashlib.md5(mapping_sig.encode()).hexdigest()[:8]
    cache_key = f'info_lol_items_{lang}_{mapping_hash}'
    cached = cache.get(cache_key)
    if cached:
        return JsonResponse(cached)

    try:
        ver  = _dd_version()
        data = _get(f'{DDRAGON_BASE}/cdn/{ver}/data/{lang}/item.json')
        items = []
        for item_id, item in data.get('data', {}).items():
            itype = _item_type(item, int(item_id))
            if not itype:
                continue
            # 스탯 텍스트 생성
            stats = item.get('stats', {})
            stat_parts = []
            stat_map = {
                'FlatPhysicalDamageMod': '공격력',
                'FlatMagicDamageMod': '주문력',
                'FlatHPPoolMod': '체력',
                'FlatArmorMod': '방어력',
                'FlatSpellBlockMod': '마법 저항력',
                'PercentAttackSpeedMod': '공격속도',
                'FlatCritChanceMod': '치명타',
                'FlatMovementSpeedMod': '이동속도',
                'PercentLifeStealMod': '생명력 흡수',
            }
            for stat_key, stat_name in stat_map.items():
                val = stats.get(stat_key, 0)
                if val:
                    if 'Percent' in stat_key:
                        stat_parts.append(f'+{round(val*100)}% {stat_name}')
                    else:
                        stat_parts.append(f'+{int(val)} {stat_name}')
            desc = item.get('plaintext', '') or item.get('description', '')
            # HTML 태그 간단 제거
            import re
            desc = re.sub(r'<[^>]+>', '', desc)[:120]
            full_desc = item.get('description', '')
            full_desc = re.sub(r'<[^>]+>', '', full_desc)

            from_ids = [int(x) for x in item.get('from', [])]
            into_ids = [int(x) for x in item.get('into', [])]

            iid  = int(item_id)
            name = (ARENA_ITEMS.get(iid) or ARAM_ITEMS.get(iid)
                    or ARENA_LEGENDARY_ITEMS.get(iid)
                    or FORCE_LEGENDARY_ITEMS.get(iid)
                    or item.get('name', ''))

            stats_detail = {}
            for stat_key, stat_name in stat_map.items():
                val = stats.get(stat_key, 0)
                if val:
                    if 'Percent' in stat_key:
                        stats_detail[stat_name] = f'+{round(val*100)}%'
                    else:
                        stats_detail[stat_name] = f'+{int(val)}'

            items.append({
                'id': iid,
                'name': name,
                'type': itype,
                'stats': ', '.join(stat_parts) if stat_parts else '—',
                'stats_detail': stats_detail,
                'desc' : desc,
                'full_desc': full_desc,
                'gold': item.get('gold', {}).get('total', 0),
                'gold_sell': item.get('gold', {}).get('sell', 0),
                'img' : f'{DDRAGON_BASE}/cdn/{ver}/img/item/{item_id}.png',
                'from_ids' : from_ids,
                'into_ids': into_ids,
            })

        ## 내림차순 정렬
        type_order = {'legendary':0, 'arena_legendary':1, 'arena':2, 'aram':3, 'entry':4}
        items.sort(key=lambda x: (type_order.get(x['type'], 9), -x['gold']))
        result = {'success': True, 'version': ver, 'items': items}
        cache.set(cache_key, result, CACHE_TTL)

        #print(f"[ITEM NAME DEBUG] -> {items}")
        return JsonResponse(result)

    except Exception as e:
        print(f'[INFO LOL ITEMS] {e}')
        return JsonResponse({'success': False, 'message': str(e)}, status=500)

def info_tft_champions(request):
    lang = request.GET.get('lang', 'ko_KR')
    cache_key = f'info_tft_champs_{lang}'
    cached = cache.get(cache_key)
    if cached:
        return JsonResponse(cached)

    try:
        ver  = _dd_version()
        data = _get(f'{DDRAGON_BASE}/cdn/{ver}/data/{lang}/tft-champion.json')
        champs = []
        for key, c in data.get('data', {}).items():
            if not key.startswith('TFT16_'):
                continue
            traits = c.get('traits', [])
            champs.append({
                'id'    : key,
                'name'  : c.get('name', key),
                'cost'  : c.get('tier', 1),
                'traits': traits,
                'img'   : f'{DDRAGON_BASE}/cdn/{ver}/img/tft-champion/{key}.png',
            })
        champs.sort(key=lambda x: (x['cost'], x['name']))
        result = {'success': True, 'version': ver, 'champions': champs}
        cache.set(cache_key, result, CACHE_TTL)
        return JsonResponse(result)

    except Exception as e:
        print(f'[INFO TFT CHAMPS] {e}')
        return JsonResponse({'success': False, 'message': str(e)}, status=500)

## TFT ITEM LIST ** << image error
def info_tft_items(request):
    lang = request.GET.get('lang', 'ko_KR')
    cache_key = f'info_tft_items_{lang}'
    cached = cache.get(cache_key)
    if cached:
        return JsonResponse(cached)

    try:
        ver  = _dd_version()
        data = _get(f'{DDRAGON_BASE}/cdn/{ver}/data/{lang}/tft-item.json')
        items = []
        import re
        for key, item in data.get('data', {}).items():
            name = item.get('name', '')
            if not name or name.startswith('tft_item'):
                continue

            # 타입 분류
            name_lower = name.lower()
            if '찬란한' in name or 'radiant' in name_lower:
                itype = 'radiant'
            elif item.get('composition'):    
                itype = 'combined'
            else:
                itype = 'component'

            desc = item.get('description', '')
            desc = re.sub(r'<[^>]+>', '', desc)[:120]

            # 스탯 텍스트
            effects = item.get('effects', {})
            stat_parts = []
            stat_label = {
                'AD':'공격력', 'AP':'주문력', 'Armor':'방호',
                'MagicResist':'마법 저항력', 'HP':'체력',
                'AS':'공격속도', 'Crit':'치명타',
                'Mana':'마나', 'OmnivampPct':'모든 피해 흡혈',
            }
            for ek, ev in list(effects.items())[:3]:
                label = stat_label.get(ek, ek)
                try:
                    val = float(ev)
                    fmt = f'+{int(val)}%' if val < 2 and val > 0 else f'+{int(val)}'
                    stat_parts.append(f'{fmt} {label}')
                except (ValueError, TypeError):
                    pass

            items.append({
                'id'   : key,
                'name' : name,
                'type' : itype,
                'stats': ', '.join(stat_parts) if stat_parts else '—',
                'desc' : desc,
                'img'  : f'{DDRAGON_BASE}/cdn/{ver}/img/tft-item/{key}.png',
            })

        type_order = {'component':0, 'combined':1, 'radiant':2}
        items.sort(key=lambda x: (type_order.get(x['type'], 9), x['name']))
        result = {'success': True, 'version': ver, 'items': items}
        cache.set(cache_key, result, CACHE_TTL)
        return JsonResponse(result)

    except Exception as e:
        print(f'[INFO TFT ITEMS] {e}')
        return JsonResponse({'success': False, 'message': str(e)}, status=500)