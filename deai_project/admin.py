from django.contrib import admin
from .models import BaseUserInformation_data, UserPreferGame, Post_Community  # ← Post_ 추가

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