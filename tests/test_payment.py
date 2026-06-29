"""
支付模块测试
覆盖：创建支付、模拟支付、支付状态查询、支付回调
"""
import pytest
from apps.orders.models import Order
from apps.payment.models import Payment


@pytest.mark.django_db
class TestCreatePayment:
    """创建支付测试"""

    def _create_and_pay_order(self, auth_client, sku):
        """辅助：创建订单"""
        auth_client.post('/api/v1/orders/', {
            'receiver_name': '张三',
            'receiver_phone': '13800000001',
            'receiver_address': '北京市朝阳区xxx',
            'items': [{'sku_id': sku.id, 'quantity': 1}]
        }, format='json')
        return Order.objects.latest('created_at')

    def test_create_payment(self, auth_client, sku):
        """创建支付记录"""
        order = self._create_and_pay_order(auth_client, sku)
        resp = auth_client.post('/api/v1/payment/create/', {
            'order_no': order.order_no,
            'pay_method': 'wechat'
        })
        assert resp.status_code == 200
        assert resp.data['code'] == 200
        assert Payment.objects.filter(order_no=order.order_no).exists()

    def test_create_payment_nonexistent_order(self, auth_client):
        """订单不存在"""
        resp = auth_client.post('/api/v1/payment/create/', {
            'order_no': 'ORD_NOT_EXIST',
            'pay_method': 'wechat'
        })
        assert resp.status_code == 404


@pytest.mark.django_db
class TestMockPay:
    """模拟支付测试"""

    def _create_payment(self, auth_client, sku):
        """辅助：创建支付记录"""
        auth_client.post('/api/v1/orders/', {
            'receiver_name': '张三',
            'receiver_phone': '13800000001',
            'receiver_address': '北京市朝阳区xxx',
            'items': [{'sku_id': sku.id, 'quantity': 1}]
        }, format='json')
        order = Order.objects.latest('created_at')
        auth_client.post('/api/v1/payment/create/', {
            'order_no': order.order_no,
            'pay_method': 'wechat'
        })
        return Payment.objects.latest('created_at'), order

    def test_mock_pay_success(self, auth_client, sku):
        """模拟支付成功"""
        payment, order = self._create_payment(auth_client, sku)
        resp = auth_client.post('/api/v1/payment/mock-pay/', {
            'pay_no': payment.pay_no
        })
        assert resp.status_code == 200
        payment.refresh_from_db()
        assert payment.status == 'success'
        # 验证订单状态更新
        order.refresh_from_db()
        assert order.status == 'paid'

    def test_mock_pay_nonexistent(self, auth_client):
        """支付记录不存在"""
        resp = auth_client.post('/api/v1/payment/mock-pay/', {
            'pay_no': 'PAY_NOT_EXIST'
        })
        assert resp.status_code == 404


@pytest.mark.django_db
class TestPaymentStatus:
    """支付状态查询测试"""

    def test_payment_status(self, auth_client, sku):
        """查询支付状态"""
        # 创建订单和支付
        auth_client.post('/api/v1/orders/', {
            'receiver_name': '张三',
            'receiver_phone': '13800000001',
            'receiver_address': '北京市朝阳区xxx',
            'items': [{'sku_id': sku.id, 'quantity': 1}]
        }, format='json')
        order = Order.objects.latest('created_at')
        auth_client.post('/api/v1/payment/create/', {
            'order_no': order.order_no,
            'pay_method': 'wechat'
        })
        payment = Payment.objects.latest('created_at')
        resp = auth_client.get(f'/api/v1/payment/{payment.pay_no}/status/')
        assert resp.status_code == 200
