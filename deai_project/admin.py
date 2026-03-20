from django.contrib import admin
from .models import BaseUserInformation_data, UserPreferGame, Post_Community, PostParticipant, Friendship, ChatMessage, JoinRequest, Notification, DirectMessage, UserReport

@admin.register(BaseUserInformation_data)
class UserAdmin(admin.ModelAdmin):
    list_display  = ('id', 'username', 'email', 'created_at', 'is_active')
    search_fields = ('username', 'email')
    list_filter   = ('is_active',)
    ordering      = ('-created_at',)

@admin.register(UserPreferGame)
class UserPreferGameAdmin(admin.ModelAdmin):
    list_display  = ('id', 'user', 'game_id', 'name_tag', 'tier', 'score_current', 'sub_info')
    search_fields = ('user__username', 'name_tag')
    list_filter   = ('game_id',)
    ordering      = ('-created_at',)
    
@admin.register(Post_Community)
class PostAdmin(admin.ModelAdmin):
    list_display  = ('id', 'user', 'game_id', 'post_title', 'current_member', 'total_member', 'tier_condition', 'is_open', 'post_upload_at')
    search_fields = ('user__username', 'post_title')
    list_filter   = ('game_id', 'is_open')
    ordering      = ('-post_upload_at',)

@admin.register(PostParticipant)
class PostParticipantAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'post', 'joined_at')

@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display  = ('id', 'post', 'user', 'message', 'sent_at')
    list_filter   = ('post',)
    search_fields = ('user__username', 'message')
    ordering      = ('-sent_at',)
    readonly_fields = ('sent_at',)

@admin.register(JoinRequest)
class JoinRequestAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'post', 'status', 'created_at')
    list_filter  = ('status',)

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'type', 'message', 'is_read', 'created_at')
    list_filter  = ('type', 'is_read')

@admin.register(Friendship)
class FriendshipAdmin(admin.ModelAdmin):
    list_display  = ('id', 'from_user', 'to_user', 'status', 'created_at')
    list_filter   = ('status',)
    search_fields = ('from_user__username', 'to_user__username')
    ordering      = ('-created_at',)

@admin.register(DirectMessage)
class DirectMessageAdmin(admin.ModelAdmin):
    list_display  = ('id', 'sender', 'receiver', 'message', 'sent_at')
    search_fields = ('sender__username', 'receiver__username', 'message')
    ordering      = ('-sent_at',)

@admin.register(UserReport)
class UserReportAdmin(admin.ModelAdmin):
    list_display  = ('id', 'reporter', 'reported', 'category', 'status', 'created_at')
    list_filter   = ('status', 'category')
    search_fields = ('reporter__username', 'reported__username', 'detail')
    ordering      = ('-created_at',)

from django.contrib import admin
from django.utils import timezone
from django.utils.html import format_html
from .models import RiotDataCache


@admin.register(RiotDataCache)
class RiotDataCacheAdmin(admin.ModelAdmin):
    list_display  = ('cache_key', 'version', 'data_size', 'status_badge',
                     'updated_at', 'expires_at')
    list_filter   = ('version',)
    search_fields = ('cache_key',)
    readonly_fields = ('cache_key', 'version', 'created_at', 'updated_at',
                       'expires_at', 'data_preview')
    ordering      = ('cache_key',)

    # 상세 페이지 필드 순서
    fields = ('cache_key', 'version', 'status_badge_detail',
              'created_at', 'updated_at', 'expires_at', 'data_preview')

    @admin.display(description='데이터 크기')
    def data_size(self, obj):
        import json as _json
        try:
            size = len(_json.dumps(obj.data, ensure_ascii=False).encode('utf-8'))
            if size >= 1024 * 1024:
                return f'{size / 1024 / 1024:.1f} MB'
            elif size >= 1024:
                return f'{size / 1024:.1f} KB'
            return f'{size} B'
        except Exception:
            return '—'

    @admin.display(description='상태')
    def status_badge(self, obj):
        if obj.expires_at is None:
            return format_html('<span style="color:#2196f3;font-weight:700;">♾ 영구</span>')
        if obj.is_expired():
            return format_html('<span style="color:#f44336;font-weight:700;">✗ 만료됨</span>')
        remaining = obj.expires_at - timezone.now()
        hours = int(remaining.total_seconds() // 3600)
        minutes = int((remaining.total_seconds() % 3600) // 60)
        return format_html(
            '<span style="color:#4caf50;font-weight:700;">✓ 유효 ({}h {}m 남음)</span>',
            hours, minutes
        )

    @admin.display(description='상태')
    def status_badge_detail(self, obj):
        return self.status_badge(obj)

    @admin.display(description='데이터 미리보기')
    def data_preview(self, obj):
        import json as _json
        try:
            preview = _json.dumps(obj.data, ensure_ascii=False, indent=2)
            # 너무 길면 앞 2000자만
            if len(preview) > 2000:
                preview = preview[:2000] + '\n...(생략)...'
            return format_html(
                '<pre style="background:#1a1a2e;color:#e0e0e0;padding:12px;'
                'border-radius:4px;font-size:11px;max-height:400px;overflow:auto;">'
                '{}</pre>',
                preview
            )
        except Exception:
            return '미리보기 불가'

    actions = ['force_expire', 'delete_selected_cache']

    @admin.action(description='선택한 캐시 즉시 만료 처리')
    def force_expire(self, request, queryset):
        count = queryset.update(expires_at=timezone.now())
        self.message_user(request, f'{count}개 캐시를 만료 처리했습니다.')

    @admin.action(description='선택한 캐시 삭제 (Django cache + DB)')
    def delete_selected_cache(self, request, queryset):
        from django.core.cache import cache as djcache
        keys = list(queryset.values_list('cache_key', flat=True))
        for key in keys:
            djcache.delete(key)
        count = queryset.delete()[0]
        self.message_user(request, f'{count}개 캐시를 삭제했습니다. (키: {", ".join(keys)})')
