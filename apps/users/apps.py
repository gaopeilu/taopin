from django.apps import AppConfig


class UsersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.users'  # 完整路径
    label = 'users'      # app_label（用于AUTH_USER_MODEL）
    verbose_name = '用户管理'
