"""
营销异步任务
- expire_coupons: 标记过期优惠券
"""
import logging
from celery import shared_task
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task(name='apps.marketing.tasks.expire_coupons')
def expire_coupons():
    """
    标记过期的优惠券记录
    规则：unused状态且关联优惠券已过期的记录，标记为expired
    """
    from .models import CouponRecord

    now = timezone.now()
    expired_records = CouponRecord.objects.filter(
        status='unused',
        coupon__end_time__lt=now
    )
    count = expired_records.update(status='expired')

    if count > 0:
        logger.info(f'标记 {count} 张优惠券为已过期')
    return f'expired {count} coupons'
