import os
from celery import Celery

# 设置Django默认设置模块
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dianshang.settings')

app = Celery('dianshang')

# 从Django settings中加载配置，CELERY_前缀的配置
app.config_from_object('django.conf:settings', namespace='CELERY')

# 自动发现所有app中的tasks.py
app.autodiscover_tasks()


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
