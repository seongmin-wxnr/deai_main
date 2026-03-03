from django.urls import path
from . import views

urlpatterns = [
    path("",                    views.index,           name='index'),
    path("login/",              views.login_,          name='Login'),
    path("register/",           views.register_,       name='register'),
    path("selectGame/",         views.selection_page,  name='selectGames'),
   path("Deai_main/",           views.Main_rq,         name='Deai_main'),
    path("logout/",             views.logout_,         name='logout'),

    ## API space
    path("api/auth/register/",  views.api_register,    name='api_register'),
    path("api/auth/login/",     views.api_login,       name='api_login'),
    path("api/game/save/",      views.save_prefer_game,name='save_prefer_game'),
    path("api/game/my/",        views.get_my_games,    name='get_my_games'),
    path("api/post/create/", views.api_post_create, name='api_post_create'),
    path("api/post/list/",   views.api_post_list,   name='api_post_list'),
]