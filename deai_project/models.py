from django.db import models
from django.utils import timezone

class BaseUserInformation_data(models.Model):
    email      = models.EmailField(unique=True, verbose_name='이메일', max_length=254)
    username   = models.CharField(max_length=30, unique=True, verbose_name='닉네임')
    password   = models.CharField(max_length=256, verbose_name='비밀번호')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='가입일')  
    is_active  = models.BooleanField(default=True, verbose_name='활성 여부')
    blocked_until = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'user_info'

    def __str__(self):
        return f'{self.username} ({self.email})'
    
class UserPreferGame(models.Model):

    user = models.ForeignKey(
        BaseUserInformation_data,
        on_delete=models.CASCADE,
        related_name='prefer_games',
        verbose_name='유저'
    )

    GAME_CHOICES = [
        ('lol',     '리그 오브 레전드'),
        ('val',     '발로란트'),
        ('ow',      '오버워치 2'),
        ('fifa',    '피파 온라인 4'),
        ('genshin', '원신'),
    ]
    game_id = models.CharField(max_length=10, choices=GAME_CHOICES, verbose_name='게임')

    name_tag      = models.CharField(max_length=50, verbose_name='Name#Tag')
    tier          = models.CharField(max_length=20, blank=True, verbose_name='티어')
    score_best    = models.IntegerField(default=0, verbose_name='최고 점수')
    score_current = models.IntegerField(default=0, verbose_name='현재 점수')
    sub_info      = models.CharField(max_length=30, blank=True, verbose_name='포지션/역할')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table     = 'user_prefer_game'
        unique_together = ('user', 'game_id')

    def __str__(self):
        return f'{self.user.username} - {self.game_id}'

class Post_Community(models.Model):
    user = models.ForeignKey(
        BaseUserInformation_data,
        on_delete=models.CASCADE,
        related_name='posts',          #  'prefer_games' 에서 변경 (중복 방지)
        verbose_name='작성자'
    )

    GAME_CHOICES = [
        ('lol',     '리그 오브 레전드'),
        ('val',     '발로란트'),
        ('ow',      '오버워치 2'),
        ('fifa',    '피파 온라인 4'),
        ('genshin', '원신'),
    ]
    game_id   = models.CharField(max_length=10, choices=GAME_CHOICES, verbose_name='게임')

    post_title     = models.CharField(max_length=100, verbose_name='제목')
    post_body      = models.TextField(blank=True, verbose_name='한마디')

    current_member = models.IntegerField(default=1, verbose_name='현재 인원')
    total_member   = models.IntegerField(default=5, verbose_name='모집 인원')
    tier_condition = models.CharField(max_length=20, default='무관', verbose_name='티어 조건')

    is_open        = models.BooleanField(default=True, verbose_name='모집 중')  # True=모집중, False=마감
    post_upload_at = models.DateTimeField(auto_now_add=True, verbose_name='작성일')

    class Meta:
        db_table = 'user_post_circuit'
        ordering = ['-post_upload_at'] 

    def __str__(self):
        return f'[{self.game_id}] {self.post_title} - {self.user.username}'
    
class PostParticipant(models.Model):
    post = models.ForeignKey(
        Post_Community,
        on_delete=models.CASCADE,
        related_name='participants',
        verbose_name='게시글'
    )
    user = models.ForeignKey(
        BaseUserInformation_data,
        on_delete=models.CASCADE,
        related_name='joined_posts',
        verbose_name='참여자'
    )
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'post_participant'
        unique_together = ('post', 'user')  # 중복 참여 DB 레벨에서 방지

    def __str__(self):
        return f'{self.user.username} → {self.post.post_title}'

class Friendship(models.Model):
    STATUS_CHOICES = [
        ('pending',  '대기 중'),
        ('accepted', '수락됨'),
        ('rejected', '거절됨'),
    ]

    from_user = models.ForeignKey(
        BaseUserInformation_data,
        on_delete=models.CASCADE,
        related_name='sent_requests',
        verbose_name='요청자'
    )
    to_user = models.ForeignKey(
        BaseUserInformation_data,
        on_delete=models.CASCADE,
        related_name='received_requests',
        verbose_name='수신자'
    )
    status    = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table     = 'friendship'
        unique_together = ('from_user', 'to_user')  # 중복 요청 방지

    def __str__(self):
        return f'{self.from_user.username} → {self.to_user.username} ({self.status})'
    
class ChatMessage(models.Model):
    post    = models.ForeignKey(
        Post_Community,
        on_delete=models.CASCADE, # 게시글 삭제 시 채팅 내역도 삭제
        related_name='messages'
    )
    user     = models.ForeignKey(
        BaseUserInformation_data,
        on_delete=models.CASCADE,
        related_name='chat_messages'
    )
    message  = models.TextField()
    sent_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table  = 'chat_message'
        ordering  = ['sent_at']

    def __str__(self):
        return f'[{self.post_id}] {self.user.username}: {self.message[:20]}'

class JoinRequest(models.Model):
    STATUS_CHOICES = [
        ('pending',  '대기 중'),
        ('accepted', '수락됨'),
        ('rejected', '거절됨'),
    ]
    post       = models.ForeignKey(Post_Community, on_delete=models.CASCADE, related_name='join_requests')
    user       = models.ForeignKey(BaseUserInformation_data, on_delete=models.CASCADE, related_name='join_requests')
    status     = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table       = 'join_request'
        unique_together = ('post', 'user')

    def __str__(self):
        return f'{self.user.username} → {self.post.post_title} ({self.status})'
    
class Notification(models.Model):
    TYPE_CHOICES = [
        ('join_request', '가입 요청'),
        ('join_accept',  '가입 수락'),
        ('join_reject',  '가입 거절'),
    ]
    user       = models.ForeignKey(BaseUserInformation_data, on_delete=models.CASCADE, related_name='notifications')
    type       = models.CharField(max_length=20, choices=TYPE_CHOICES)
    message    = models.CharField(max_length=200)
    is_read    = models.BooleanField(default=False)
    related_join_request = models.ForeignKey(
        JoinRequest, on_delete=models.CASCADE, null=True, blank=True, related_name='notifications'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'notification'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user.username} - {self.type}'

class DirectMessage(models.Model):
    sender   = models.ForeignKey(BaseUserInformation_data, on_delete=models.CASCADE, related_name='sent_dms')
    receiver = models.ForeignKey(BaseUserInformation_data, on_delete=models.CASCADE, related_name='received_dms')
    message  = models.TextField()
    sent_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'direct_message'
        ordering = ['sent_at']

    def __str__(self):
        return f'{self.sender.username} → {self.receiver.username}: {self.message[:20]}'

class UserReport(models.Model):
    reporter = models.ForeignKey(BaseUserInformation_data, on_delete=models.CASCADE, related_name='reports_sent')
    reported = models.ForeignKey(BaseUserInformation_data, on_delete=models.CASCADE, related_name='reports_received')
    category = models.CharField(max_length=50)
    status    = models.CharField(max_length=20, default='pending')
    detail   = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'user_report'

from django.db import models
from django.utils import timezone


class RiotDataCache(models.Model):
    # cache_key 예시:
    #   info_lol_champs_ko_KR
    #   info_lol_items_ko_KR_<hash>
    #   info_tft_champs_ko_KR
    #   info_tft_items_ko_KR
    #   cdragon_tft_ko_kr         
    #   ddragon_version

    ## 중복 로드 방지 db 캐시 테이블
    cache_key   = models.CharField(max_length=120, unique=True, db_index=True,
                                   verbose_name='캐시 키')
    data        = models.JSONField(verbose_name='JSON 데이터')
    version     = models.CharField(max_length=20, blank=True, default='',
                                   verbose_name='데이터 버전(패치)')
    created_at  = models.DateTimeField(auto_now_add=True, verbose_name='최초 저장')
    updated_at  = models.DateTimeField(auto_now=True,     verbose_name='최근 갱신')
    expires_at  = models.DateTimeField(null=True, blank=True,
                                       verbose_name='만료 시각 (null=영구)')

    class Meta:
        db_table     = 'riot_data_cache'
        verbose_name = 'Riot 데이터 캐시'

    def __str__(self):
        return f'{self.cache_key} (v{self.version}, {self.updated_at:%Y-%m-%d %H:%M})'

    def is_expired(self) -> bool:
        if self.expires_at is None:
            return False
        return timezone.now() > self.expires_at

    @classmethod
    def get(cls, key: str):
        """캐시 조회. 없거나 만료됐으면 None 반환."""
        try:
            obj = cls.objects.get(cache_key=key)
            if obj.is_expired():
                return None
            return obj.data
        except cls.DoesNotExist:
            return None

    @classmethod
    def set(cls, key: str, data, version: str = '', ttl_hours: int = 6):
        """캐시 저장/갱신."""
        from datetime import timedelta
        expires = timezone.now() + timedelta(hours=ttl_hours) if ttl_hours else None
        cls.objects.update_or_create(
            cache_key=key,
            defaults={
                'data'      : data,
                'version'   : version,
                'expires_at': expires,
            }
        )
    @classmethod
    def delete_key(cls, key: str):
        cls.objects.filter(cache_key=key).delete()

## + rank 
class RankingSnapshot(models.Model):
    GAME_CHOICES = [
        ('lol', 'League of Legends'),
        ('tft', 'Teamfight Tactics'),
    ]
    QUEUE_CHOICES = [
        ('RANKED_SOLO_5x5',        'LoL 솔로랭크'),
        ('RANKED_FLEX_SR',         'LoL 자유랭크'),
        ('RANKED_TFT',             'TFT 솔로'),
        ('RANKED_TFT_DOUBLE_UP',   'TFT 더블업'),
    ]

    game       = models.CharField(max_length=5,  choices=GAME_CHOICES)
    queue      = models.CharField(max_length=30, choices=QUEUE_CHOICES)
    collected_at = models.DateTimeField(default=timezone.now, verbose_name='수집 시각')
    is_active  = models.BooleanField(default=True, verbose_name='활성 스냅샷')

    class Meta:
        db_table = 'c_ranking_snapshot'
        indexes  = [models.Index(fields=['game', 'queue', 'is_active'])]

    def __str__(self):
        return f'[{self.game}/{self.queue}] {self.collected_at:%Y-%m-%d %H:%M} active={self.is_active}'


class RankingEntry(models.Model):
    snapshot    = models.ForeignKey(
        RankingSnapshot, on_delete=models.CASCADE, related_name='entries'
    )

    rank        = models.PositiveIntegerField(verbose_name='순위')
    summoner_id = models.CharField(max_length=100, blank=True)
    puuid       = models.CharField(max_length=100, blank=True, db_index=True)
    name        = models.CharField(max_length=80,  default='?')
    tag_line    = models.CharField(max_length=20,  blank=True)
    icon_id     = models.PositiveIntegerField(default=1)
    level       = models.PositiveIntegerField(default=1)
    tier        = models.CharField(max_length=20)
    division    = models.CharField(max_length=4, blank=True)
    rank_label  = models.CharField(max_length=30)
    lp          = models.IntegerField(default=0)
    wins        = models.IntegerField(default=0)
    losses      = models.IntegerField(default=0)
    winrate     = models.IntegerField(default=0)
    hot_streak  = models.BooleanField(default=False)
    veteran     = models.BooleanField(default=False)
    fresh_blood = models.BooleanField(default=False)

    class Meta:
        db_table = 'c_userTable'
        ordering = ['rank']
        indexes  = [
            models.Index(fields=['snapshot', 'rank']),
        ]

    def __str__(self):
        return f'#{self.rank} {self.name}#{self.tag_line} {self.tier} {self.lp}LP'

    def to_dict(self) -> dict:
        return {
            'rank'      : self.rank,
            'summonerId': self.summoner_id,
            'puuid'     : self.puuid,
            'name'      : self.name,
            'tagLine'   : self.tag_line,
            'iconId'    : self.icon_id,
            'level'     : self.level,
            'tier'      : self.tier,
            'division'  : self.division,
            'rankLabel' : self.rank_label,
            'lp'        : self.lp,
            'wins'      : self.wins,
            'losses'    : self.losses,
            'winrate'   : self.winrate,
            'hotStreak' : self.hot_streak,
            'veteran'   : self.veteran,
            'freshBlood': self.fresh_blood,
        }
