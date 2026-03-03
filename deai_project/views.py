from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.hashers import make_password, check_password

## 데이터베이스 관ㄹ리
from .models import BaseUserInformation_data , UserPreferGame, Post_Community
from datetime import datetime
import json

def selection_page(request):
    if not request.session.get('username'):
        try:

            return render(request , 'login.html')
        
        except Exception as e:
            print(f"Except {e}")
    else:

        username = request.session.get('username')
        username = request.session.get('username', '게스트')
        return render(request, "selectGame.html", {
            'username': username 
        })
     
    
def index(request):
    return render(request, "index.html")

# fix -> 2026.03.02
def Main_rq(request):
    if not request.session.get('user_id'):
        return render(request, 'login.html')
    
    import json
    games = UserPreferGame.objects.filter(
        user_id=request.session['user_id']
    ).values('game_id', 'name_tag', 'tier', 'score_best', 'score_current', 'sub_info')

    return render(request, "Main.html", {
        'username'  : request.session.get('username', ''),
        'email'     : request.session.get('email', ''),
        'games_json': json.dumps(list(games)),
    })

def get_my_games(request):
    if not request.session.get('user_id'):
        return JsonResponse({'success': False}, status=401)
    games = UserPreferGame.objects.filter(
        user_id=request.session['user_id']
    ).values('game_id','name_tag','tier','score_best','score_current','sub_info')
    return JsonResponse({'success': True, 'games': list(games)})

def login_(request):
    if request.method == "GET":
        return render(request, "login.html")

    if request.method == "POST":
        try:
            data     = json.loads(request.body)
            username = data.get('username', '').strip()
            password = data.get('password', '').strip()

            if not username or not password:
                return JsonResponse({
                    'success': False,
                    'message': '유저 이름, 비밀번호를 확인해주세요.'
                }, status=400)

            user = BaseUserInformation_data.objects.filter(username=username).first()

            if not user:
                return JsonResponse({
                    'success': False,
                    'message': '존재하지 않는 닉네임입니다.'
                }, status=404)

            if not check_password(password, user.password):
                return JsonResponse({
                    'success': False,
                    'message': '비밀번호가 틀렸습니다.'
                }, status=401)

            request.session['user_id']  = user.id
            request.session['username'] = user.username
            request.session['email']    = user.email

            has_game = UserPreferGame.objects.filter(user=user).exists()
            redirect_url = '/Deai_main/' if has_game else '/selectGame/'

            return JsonResponse({
                'success'     : True,
                'message'     : '로그인 성공!',
                'username'    : user.username,
                'redirect_url': redirect_url, 
            })

        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'서버 오류: {str(e)}'
            }, status=500)

def register_(request):
    if request.method == "GET":
        return render(request, "register.html")

    if request.method == "POST":
        try:
            data     = json.loads(request.body)
            username = data.get('username', '').strip()
            password = data.get('password', '').strip()
            email    = data.get('email',    '').strip()

            if not email or not username or not password:
                return JsonResponse({
                    'success': False,
                    'message': '모든 항목을 입력해주세요.'
                }, status=400)

            if BaseUserInformation_data.objects.filter(email=email).exists():  # ← 버그 수정
                return JsonResponse({
                    'success': False,
                    'message': '이미 사용중인 이메일입니다.'
                }, status=409)

            if BaseUserInformation_data.objects.filter(username=username).exists():
                return JsonResponse({
                    'success': False,
                    'message': '이미 사용중인 닉네임입니다.'
                }, status=409)

            BaseUserInformation_data.objects.create(
                email    = email,
                username = username,
                password = make_password(password),
            )
            print("registerd -> " + str(username))
            return JsonResponse({
                'success': True,
                'message': f'회원가입 성공! {username}님 환영합니다.'
            }, status=201)  # ← 버그 수정 (400 → 201)

        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'회원가입에 실패했습니다. {e}'
            }, status=500)
def api_register(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': '허용되지 않는 메서드'}, status=405)
    try:
        data     = json.loads(request.body)
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()
        email    = data.get('email',    '').strip()

        if not email or not username or not password:
            return JsonResponse({'success': False, 'message': '모든 항목을 입력해주세요.'}, status=400)

        if BaseUserInformation_data.objects.filter(email=email).exists():
            return JsonResponse({'success': False, 'message': '이미 사용중인 이메일입니다.'}, status=409)

        if BaseUserInformation_data.objects.filter(username=username).exists():
            return JsonResponse({'success': False, 'message': '이미 사용중인 닉네임입니다.'}, status=409)

        BaseUserInformation_data.objects.create(
            email    = email,
            username = username,
            password = make_password(password),
        )
        print("login -> " + str(username))
        return JsonResponse({'success': True, 'message': f'{username}님 환영합니다!'}, status=201)

    except Exception as e:
        return JsonResponse({'success': False, 'message': f'서버 오류: {str(e)}'}, status=500)


def api_login(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': '허용되지 않는 메서드'}, status=405)
    try:
        data     = json.loads(request.body)
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()

        if not username or not password:
            return JsonResponse({'success': False, 'message': '닉네임과 비밀번호를 입력해주세요.'}, status=400)

        user = BaseUserInformation_data.objects.filter(username=username).first()

        if not user:
            return JsonResponse({'success': False, 'message': '존재하지 않는 닉네임입니다.'}, status=404)

        if not check_password(password, user.password):
            return JsonResponse({'success': False, 'message': '비밀번호가 틀렸습니다.'}, status=401)

        request.session['user_id']  = user.id
        request.session['username'] = user.username
        request.session['email']    = user.email

        # 게임 정보 1 -> pass 아니면 ->
        has_game = UserPreferGame.objects.filter(user=user).exists()
        redirect_url = '/Deai_main/' if has_game else '/selectGame/'

        return JsonResponse({
            'success'     : True,
            'message'     : '로그인 성공!',
            'username'    : user.username,
            'redirect_url': redirect_url,   # ← 프론트에 URL 전달
        })

    except Exception as e:
        return JsonResponse({'success': False, 'message': f'서버 오류: {str(e)}'}, status=500)
    
def logout_(request):
    request.session.flush()  # 세션 전체 삭제
    return JsonResponse({'success': True})

def Add_usergamedata(request):
    if request.method == 'POST':
        data  = json.loads(request.body)
        games = data.get('games', [])  # selectGame.html 에서 넘어온 배열

        user = BaseUserInformation_data.objects.get(
            id=request.session['user_id']
        )

        for g in games:
            UserPreferGame.objects.update_or_create(
                user    = user,
                game_id = g['gameId'],   # 'lol', 'val' 등
                defaults = {
                    'name_tag'      : f"{g['name']}#{g['tag']}",
                    'tier'          : g.get('lol_tier') or g.get('val_tier') or g.get('ow_tier') or '',
                    'score_best'    : g.get('lol_lp_best') or g.get('val_rr_best') or 0,
                    'score_current' : g.get('lol_lp_current') or g.get('val_rr_current') or 0,
                    'sub_info'      : g.get('lol_pos') or g.get('val_role') or g.get('ow_role') or '',
                }
            )
        print("update user game data at -> ")
        return JsonResponse({'success': True})

def save_prefer_game(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': '허용되지 않는 메서드'}, status=405)

    if not request.session.get('user_id'):
        return JsonResponse({'success': False, 'message': '로그인이 필요합니다.'}, status=401)

    try:
        data = json.loads(request.body)
        user = BaseUserInformation_data.objects.get(id=request.session['user_id'])

        UserPreferGame.objects.update_or_create(
            user    = user,
            game_id = data['game_id'],
            defaults = {
                'name_tag'      : data.get('name_tag', ''),
                'tier'          : data.get('tier', ''),
                'score_best'    : data.get('score_best', 0),
                'score_current' : data.get('score_current', 0),
                'sub_info'      : data.get('sub_info', ''),
            }
        )
        return JsonResponse({'success': True})

    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)

def api_posts(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': '허용되지 않는 메서드'}, status=405)

    if not request.session.get('user_id'):
        return JsonResponse({'success': False, 'message': '로그인이 필요합니다.'}, status=401)
    try:
        mainRQ_data = json.load(request.body)
        ingameDataSets = UserPreferGame.objects.get(id=request.session['user_id'])
        print("reading -> " + str(mainRQ_data) + " " + str(ingameDataSets))

    except Exception as e:
        return JsonResponse({'success' : False ,'message' : str(e)}, status=500)

def api_post_create(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': '허용되지 않는 메서드'}, status=405)

    if not request.session.get('user_id'):
        return JsonResponse({'success': False, 'message': '로그인이 필요합니다.'}, status=401)

    try:
        data = json.loads(request.body)
        user = BaseUserInformation_data.objects.get(id=request.session['user_id'])

        # 필수값 검사
        if not data.get('post_title'):
            return JsonResponse({'success': False, 'message': '제목을 입력해주세요.'}, status=400)
        if not data.get('game_id'):
            return JsonResponse({'success': False, 'message': '게임을 선택해주세요.'}, status=400)

        post = Post_Community.objects.create(
            user           = user,
            game_id        = data['game_id'],
            post_title     = data['post_title'],
            post_body      = data.get('post_body', ''),
            current_member = int(data.get('current_member', 1)),
            total_member   = int(data.get('total_member', 5)),
            tier_condition = data.get('tier_condition', '무관'),
            is_open        = True,
        )
        print("Data save at -> post_")
        return JsonResponse({
            'success': True,
            'post': {
                'id'            : post.id,
                'game_id'       : post.game_id,
                'post_title'    : post.post_title,
                'post_body'     : post.post_body,
                'current_member': post.current_member,
                'total_member'  : post.total_member,
                'tier_condition': post.tier_condition,
                'is_open'       : post.is_open,
                'author'        : user.username,
                'uploaded_at'   : '방금 전',
            }
        }, status=201)
    
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)


def api_post_list(request):
    if request.method != 'GET':
        return JsonResponse({'success': False, 'message': '허용되지 않는 메서드'}, status=405)
    try:
        game_id = request.GET.get('game_id', '')
        posts = Post_Community.objects.select_related('user')
        if game_id:
            posts = posts.filter(game_id=game_id)

        def time_ago(dt):
            from django.utils import timezone
            diff = timezone.now() - dt
            s = int(diff.total_seconds())
            if s < 60:    return '방금 전'
            if s < 3600:  return f'{s//60}분 전'
            if s < 86400: return f'{s//3600}시간 전'
            return f'{s//86400}일 전'

        result = []
        for p in posts:
            # 작성자의 해당 게임 정보 조회
            game_info = UserPreferGame.objects.filter(
                user=p.user, game_id=p.game_id
            ).first()

            result.append({
                'id'             : p.id,
                'game_id'        : p.game_id,
                'post_title'     : p.post_title,
                'post_body'      : p.post_body,
                'current_member' : p.current_member,
                'total_member'   : p.total_member,
                'tier_condition' : p.tier_condition,
                'is_open'        : p.is_open,
                'author'         : p.user.username,
                'uploaded_at'    : time_ago(p.post_upload_at),
                # 작성자 게임 정보 
                'author_name_tag': game_info.name_tag  if game_info else '',
                'author_tier'    : game_info.tier      if game_info else '',
                'author_sub_info': game_info.sub_info  if game_info else '',
            })
        print("Data read at -> post_")
        return JsonResponse({'success': True, 'posts': result})

    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)