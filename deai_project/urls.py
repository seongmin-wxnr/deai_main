from django.urls import path
from . import views

urlpatterns = [
    path("",views.index, name='index'),
    path("login/",views.login_,name='Login'),
    path("register/",views.register_, name='register'),
    path("selectGame/", views.selection_page,name='selectGames'),
    path("Deai_main/",views.Main_rq,name='Deai_main'),
    path("eventPage/", views.eventPage, name='eventPage'),
    path("aboutDeai/", views.aboutDeai, name='aboutDeai'),

    ## API space
    path("logout/",views.logout_, name='logout'),
    path("api/auth/register/",views.api_register,name='api_register'),
    path("api/auth/login/", views.api_login, name='api_login'),
    path("api/game/save/", views.save_prefer_game,name='save_prefer_game'),
    path("api/game/my/", views.get_my_games,name='get_my_games'),
    path("api/post/create/", views.api_post_create, name='api_post_create'),
    path("api/post/list/",views.api_post_list,name='api_post_list'),
    path("api/post/delete/<int:post_id>/", views.api_post_delete, name='api_post_delete'), 
    path("api/post/join/<int:post_id>/", views.api_post_join, name='api_post_join'), 
    path("api/post/leave/<int:post_id>/", views.api_post_leave, name='api_post_leave'),
    path("api/user/search/", views.api_user_search, name='api_user_search'),
    path("api/friend/request/", views.api_friend_request,name='api_friend_request'),
    path("api/friend/requests/received/", views.api_friend_requests_received, name='api_friend_requests_received'),
    path("api/friend/respond/", views.api_friend_respond, name='api_friend_respond'),
    path("api/friend/list/", views.api_friend_list, name='api_friend_list'),
    path("api/friend/delete/<int:friendship_id>/", views.api_friend_delete,  name='api_friend_delete'),
]
