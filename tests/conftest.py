"""
测试公共fixtures
"""
import pytest
from rest_framework.test import APIClient
from apps.users.models import User
from apps.goods.models import Category, Brand, GoodsSPU, GoodsSKU


@pytest.fixture(autouse=True)
def disable_throttling(settings):
    """测试环境禁用限流"""
    settings.REST_FRAMEWORK['DEFAULT_THROTTLE_CLASSES'] = []
    settings.REST_FRAMEWORK['DEFAULT_THROTTLE_RATES'] = {
        'anon': '99999/minute',
        'login': '99999/minute',
        'register': '99999/minute',
        'send_code': '99999/minute',
    }


@pytest.fixture
def api_client():
    """DRF测试客户端"""
    return APIClient()


@pytest.fixture
def user(db):
    """普通用户"""
    u = User.objects.create_user(
        username='testuser',
        password='Test123456',
        email='testuser@test.com',
        phone='13800000001',
        role='user'
    )
    return u


@pytest.fixture
def seller(db):
    """商家用户"""
    u = User.objects.create_user(
        username='testseller',
        password='Test123456',
        email='testseller@test.com',
        phone='13800000002',
        role='seller',
        shop_name='测试店铺'
    )
    return u


@pytest.fixture
def category(db):
    """商品分类"""
    return Category.objects.create(name='数码产品', level=1, is_active=True)


@pytest.fixture
def brand(db):
    """品牌"""
    return Brand.objects.create(name='测试品牌', is_active=True)


@pytest.fixture
def spu(db, seller, category, brand):
    """商品SPU"""
    return GoodsSPU.objects.create(
        seller=seller,
        name='测试手机 Pro',
        subtitle='高性能测试手机',
        category=category,
        brand=brand,
        is_on_sale=True,
        is_deleted=False
    )


@pytest.fixture
def sku(db, spu):
    """商品SKU"""
    return GoodsSKU.objects.create(
        spu=spu,
        name='黑色 256GB',
        price=4999.00,
        original_price=5999.00,
        stock=100,
        sales=10,
        is_active=True,
        is_default=True
    )


@pytest.fixture
def auth_client(api_client, user):
    """已认证的普通用户客户端"""
    api_client.force_authenticate(user=user)
    return api_client


@pytest.fixture
def seller_client(api_client, seller):
    """已认证的商家客户端"""
    api_client.force_authenticate(user=seller)
    return api_client
