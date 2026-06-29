"""
订单模块测试
覆盖：创建订单、订单列表、订单详情、取消订单、库存扣减/恢复
"""
import pytest
from apps.orders.models import Order, OrderItem
from apps.goods.models import GoodsSKU


@pytest.mark.django_db
class TestCreateOrder:
    """创建订单测试"""

    def test_create_order_success(self, auth_client, user, sku):
        """创建订单成功"""
        resp = auth_client.post('/api/v1/orders/', {
            'receiver_name': '张三',
            'receiver_phone': '13800000001',
            'receiver_address': '北京市朝阳区xxx',
            'items': [{'sku_id': sku.id, 'quantity': 2}]
        }, format='json')
        assert resp.status_code == 201
        assert resp.data['code'] == 200
        # 验证订单创建
        order = Order.objects.latest('created_at')
        assert order.user == user
        assert order.status == 'pending'
        # 验证订单项
        assert order.items.count() == 1
        # 验证库存扣减
        sku.refresh_from_db()
        assert sku.stock == 98
        assert sku.sales == 12

    def test_create_order_empty_items(self, auth_client):
        """空商品列表"""
        resp = auth_client.post('/api/v1/orders/', {
            'receiver_name': '张三',
            'receiver_phone': '13800000001',
            'receiver_address': '北京市朝阳区xxx',
            'items': []
        }, format='json')
        assert resp.status_code == 400

    def test_create_order_insufficient_stock(self, auth_client, sku):
        """库存不足"""
        resp = auth_client.post('/api/v1/orders/', {
            'receiver_name': '张三',
            'receiver_phone': '13800000001',
            'receiver_address': '北京市朝阳区xxx',
            'items': [{'sku_id': sku.id, 'quantity': 999}]
        }, format='json')
        assert resp.status_code == 400

    def test_create_order_nonexistent_sku(self, auth_client):
        """SKU不存在"""
        resp = auth_client.post('/api/v1/orders/', {
            'receiver_name': '张三',
            'receiver_phone': '13800000001',
            'receiver_address': '北京市朝阳区xxx',
            'items': [{'sku_id': 99999, 'quantity': 1}]
        }, format='json')
        assert resp.status_code == 400

    def test_create_order_unauthenticated(self, api_client, sku):
        """未登录创建订单"""
        resp = api_client.post('/api/v1/orders/', {
            'receiver_name': '张三',
            'receiver_phone': '13800000001',
            'receiver_address': '北京市朝阳区xxx',
            'items': [{'sku_id': sku.id, 'quantity': 1}]
        }, format='json')
        assert resp.status_code == 401


@pytest.mark.django_db
class TestOrderList:
    """订单列表测试"""

    def test_order_list_empty(self, auth_client):
        """无订单时返回空列表"""
        resp = auth_client.get('/api/v1/orders/')
        assert resp.status_code == 200

    def test_order_list_with_orders(self, auth_client, user, sku):
        """有订单时返回列表"""
        # 先创建一个订单
        auth_client.post('/api/v1/orders/', {
            'receiver_name': '张三',
            'receiver_phone': '13800000001',
            'receiver_address': '北京市朝阳区xxx',
            'items': [{'sku_id': sku.id, 'quantity': 1}]
        }, format='json')
        resp = auth_client.get('/api/v1/orders/')
        assert resp.status_code == 200

    def test_order_list_filter_by_status(self, auth_client, user, sku):
        """按状态筛选"""
        auth_client.post('/api/v1/orders/', {
            'receiver_name': '张三',
            'receiver_phone': '13800000001',
            'receiver_address': '北京市朝阳区xxx',
            'items': [{'sku_id': sku.id, 'quantity': 1}]
        }, format='json')
        resp = auth_client.get('/api/v1/orders/?status=pending')
        assert resp.status_code == 200


@pytest.mark.django_db
class TestOrderCancel:
    """取消订单测试"""

    def _create_order(self, auth_client, sku):
        """辅助：创建订单"""
        auth_client.post('/api/v1/orders/', {
            'receiver_name': '张三',
            'receiver_phone': '13800000001',
            'receiver_address': '北京市朝阳区xxx',
            'items': [{'sku_id': sku.id, 'quantity': 2}]
        }, format='json')
        return Order.objects.latest('created_at')

    def test_cancel_order_success(self, auth_client, user, sku):
        """取消订单成功"""
        order = self._create_order(auth_client, sku)
        sku.refresh_from_db()
        old_stock = sku.stock  # 98 (100 - 2)
        resp = auth_client.post(f'/api/v1/orders/{order.order_no}/cancel/')
        assert resp.status_code == 200
        # 验证库存恢复
        sku.refresh_from_db()
        assert sku.stock == old_stock + 2

    def test_cancel_non_pending_order(self, auth_client, user, sku):
        """取消非pending状态的订单"""
        order = self._create_order(auth_client, sku)
        order.status = 'paid'
        order.save()
        resp = auth_client.post(f'/api/v1/orders/{order.order_no}/cancel/')
        assert resp.status_code == 400


@pytest.mark.django_db
class TestOrderPay:
    """支付订单测试"""

    def test_pay_order_success(self, auth_client, user, sku):
        """支付订单成功"""
        auth_client.post('/api/v1/orders/', {
            'receiver_name': '张三',
            'receiver_phone': '13800000001',
            'receiver_address': '北京市朝阳区xxx',
            'items': [{'sku_id': sku.id, 'quantity': 1}]
        }, format='json')
        order = Order.objects.latest('created_at')
        resp = auth_client.post(f'/api/v1/orders/{order.order_no}/pay/', {
            'pay_method': 'wechat'
        })
        assert resp.status_code == 200
        order.refresh_from_db()
        assert order.status == 'paid'

    def test_pay_non_pending_order(self, auth_client, user, sku):
        """支付非pending状态的订单"""
        auth_client.post('/api/v1/orders/', {
            'receiver_name': '张三',
            'receiver_phone': '13800000001',
            'receiver_address': '北京市朝阳区xxx',
            'items': [{'sku_id': sku.id, 'quantity': 1}]
        }, format='json')
        order = Order.objects.latest('created_at')
        # 先支付一次
        auth_client.post(f'/api/v1/orders/{order.order_no}/pay/', {'pay_method': 'wechat'})
        # 再次支付
        resp = auth_client.post(f'/api/v1/orders/{order.order_no}/pay/', {'pay_method': 'wechat'})
        assert resp.status_code == 400
