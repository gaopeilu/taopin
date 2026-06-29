from django.apps import AppConfig


# 这个类的意思是：这个app的名字是goods，这个app的label是goods
class GoodsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.goods'
    label = 'goods'
    verbose_name = '商品管理'
