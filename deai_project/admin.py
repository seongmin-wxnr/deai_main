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
