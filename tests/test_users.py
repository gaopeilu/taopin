"""
用户模块测试
覆盖：注册、登录、获取用户信息、修改密码
"""
import pytest
from django.urls import reverse
from apps.users.models import User


@pytest.mark.django_db
class TestRegister:
    """注册测试"""

    def test_register_success(self, api_client):
        """注册成功"""
        resp = api_client.post('/api/v1/users/register/', {
            'username': 'newuser',
            'password': 'NewPass123',
            'password_confirm': 'NewPass123',
            'phone': '13900000001',
            'role': 'user'
        })
        assert resp.status_code == 201
        assert resp.data['code'] == 200
        assert 'tokens' in resp.data['data']
        assert User.objects.filter(username='newuser').exists()

    def test_register_duplicate_username(self, api_client, user):
        """用户名已存在"""
        resp = api_client.post('/api/v1/users/register/', {
            'username': 'testuser',
            'password': 'Test123456',
            'password_confirm': 'Test123456',
        })
        assert resp.status_code == 400

    def test_register_password_mismatch(self, api_client):
        """两次密码不一致"""
        resp = api_client.post('/api/v1/users/register/', {
            'username': 'newuser2',
            'password': 'Test123456',
            'password_confirm': 'Different123',
        })
        assert resp.status_code == 400

    def test_register_seller_without_shop_name(self, api_client):
        """商家注册缺少店铺名称"""
        resp = api_client.post('/api/v1/users/register/', {
            'username': 'selleruser',
            'password': 'Test123456',
            'password_confirm': 'Test123456',
            'role': 'seller'
        })
        assert resp.status_code == 400


@pytest.mark.django_db
class TestLogin:
    """登录测试"""

    def test_login_by_username(self, api_client, user):
        """用户名登录"""
        resp = api_client.post('/api/v1/users/login/', {
            'username': 'testuser',
            'password': 'Test123456'
        })
        assert resp.status_code == 200
        assert resp.data['code'] == 200
        assert 'tokens' in resp.data['data']

    def test_login_by_phone(self, api_client, user):
        """手机号登录"""
        resp = api_client.post('/api/v1/users/login/', {
            'username': '13800000001',
            'password': 'Test123456'
        })
        assert resp.status_code == 200

    def test_login_wrong_password(self, api_client, user):
        """密码错误"""
        resp = api_client.post('/api/v1/users/login/', {
            'username': 'testuser',
            'password': 'WrongPass123'
        })
        assert resp.status_code == 400


@pytest.mark.django_db
class TestUserInfo:
    """用户信息测试"""

    def test_get_user_info(self, auth_client):
        """获取当前用户信息"""
        resp = auth_client.get('/api/v1/users/me/')
        assert resp.status_code == 200
        assert resp.data['data']['username'] == 'testuser'

    def test_update_user_info(self, auth_client):
        """更新用户信息"""
        resp = auth_client.patch('/api/v1/users/me/', {
            'nickname': '新昵称'
        })
        assert resp.status_code == 200
        assert resp.data['data']['nickname'] == '新昵称'

    def test_get_user_info_unauthenticated(self, api_client):
        """未登录获取用户信息"""
        resp = api_client.get('/api/v1/users/me/')
        assert resp.status_code == 401


@pytest.mark.django_db
class TestChangePassword:
    """修改密码测试"""

    def test_change_password_success(self, auth_client):
        """修改密码成功"""
        resp = auth_client.put('/api/v1/users/me/password/', {
            'old_password': 'Test123456',
            'new_password': 'NewPass123',
            'new_password_confirm': 'NewPass123'
        })
        assert resp.status_code == 200

    def test_change_password_wrong_old(self, auth_client):
        """旧密码错误"""
        resp = auth_client.put('/api/v1/users/me/password/', {
            'old_password': 'WrongOld123',
            'new_password': 'NewPass123',
            'new_password_confirm': 'NewPass123'
        })
        assert resp.status_code == 400
