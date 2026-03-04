from django.db import models
from django.utils import timezone

class BaseUserInformation_data(models.Model):
    email      = models.EmailField(unique=True, verbose_name='이메일', max_length=254)
    username   = models.CharField(max_length=30, unique=True, verbose_name='닉네임')
    password   = models.CharField(max_length=256, verbose_name='비밀번호')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='가입일')  
    is_active  = models.BooleanField(default=True, verbose_name='활성 여부')

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
