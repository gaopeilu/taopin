"""
订单异步任务
- cancel_expired_orders: 取消超时未支付订单（30分钟）
"""
import logging
from celery import shared_task
from django.utils import timezone
from datetime import timedelta

logger = logging.getLogger(__name__)


@shared_task(name='apps.orders.tasks.cancel_expired_orders')
def cancel_expired_orders():
    """
    取消超时未支付的订单
    规则：pending状态超过30分钟的订单自动取消，恢复库存
    """
    from .models import Order
    from apps.goods.models import GoodsSKU

    deadline = timezone.now() - timedelta(minutes=30)
    expired_orders = Order.objects.filter(
        status='pending',
        created_at__lt=deadline
    )

    count = 0
    for order in expired_orders:
        # 恢复库存
        for item in order.items.all():
            try:
                sku = GoodsSKU.objects.get(id=item.sku_id)
                sku.stock += item.quantity
                sku.sales = max(0, sku.sales - item.quantity)
                sku.save()
                try:
                    spu = sku.spu
                    spu.sales = max(0, spu.sales - item.quantity)
                    spu.save()
                except Exception:
                    pass
            except GoodsSKU.DoesNotExist:
                pass

        order.status = 'cancelled'
        order.save()
        count += 1

    if count > 0:
        logger.info(f'自动取消 {count} 个超时订单')
    return f'cancelled {count} expired orders'
