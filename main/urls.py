from django.urls import path
from .views import *


urlpatterns = [
    path('', start_login, name='login_page'),
    #path('', site_stop),
    path('user_home/', user_home, name='user_home'),
    path('logout/', userlogout, name='user_logout'),
    path('staff_home/', staff_home, name='staff_home'),
    path('load_data/<str:mod_name>/', admin_load_data, name='admin_load_data_page'),
    path('logs_list/', LogsList.as_view(), name='logs_page'),
    path('help/', HelpPage.as_view(), name='help_page'),
]