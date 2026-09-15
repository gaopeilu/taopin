# 用户模块接口测试
import requests
import time
import pytest
from conftest import BASE_URL


class TestRegister:
    """用户注册接口测试（无需登录）"""
    def test_register(self):
        timestamp = int(time.time() * 1000)
        register_data = {
            "username": f"test_{timestamp}",
            "password": "1234567811",
            "password_confirm": "1234567811",
        }
        response = requests.post(f"{BASE_URL}/users/register/", json=register_data)
        assert response.status_code == 201
        json_data = response.json()
        assert json_data["code"] == 200
        assert "tokens" in json_data["data"]

    def test_register_password_not_match(self):
        timestamp = int(time.time() * 1000)
        register_data = {
            "username": f"test_{timestamp}",
            "password": "12345678",
            "password_confirm": "1234567789",
        }
        response = requests.post(f"{BASE_URL}/users/register/", json=register_data)
        assert response.status_code == 400
        json_data = response.json()
        assert json_data["code"] == 400
        assert "errors" in json_data
        assert json_data["message"] == "password_confirm: 两次密码不一致"


class TestLogin:
    """用户登录接口测试（无需登录）"""
    def test_login(self):
        login_data = {"username": "test111", "password": "1234567811"}
        response = requests.post(f"{BASE_URL}/users/login/", json=login_data)
        assert response.status_code == 200
        json_data = response.json()
        assert json_data["code"] == 200
        assert "tokens" in json_data["data"]

    def test_login_username_not_exist(self):
        login_data = {"username": "test111_not_exist", "password": "1234567811"}
        response = requests.post(f"{BASE_URL}/users/login/", json=login_data)
        assert response.status_code == 400
        json_data = response.json()
        assert json_data["code"] == 400
        assert json_data["message"] == "non_field_errors: 用户名或密码错误"

    def test_login_password_error(self):
        login_data = {"username": "test111", "password": "12345678"}
        response = requests.post(f"{BASE_URL}/users/login/", json=login_data)
        assert response.status_code == 400
        json_data = response.json()
        assert json_data["code"] == 400
        assert json_data["message"] == "non_field_errors: 用户名或密码错误"


class TestGetUserInfo:
    """获取用户信息接口测试"""

    @pytest.fixture(autouse=True)
    def setup(self, auth):
        self.token = auth["token"]

    def test_get_user_info(self):
        resp = requests.get(f"{BASE_URL}/users/me/", headers={
            "Authorization": f"Bearer {self.token}"
        })
        assert resp.status_code == 200
        json_data = resp.json()
        assert json_data["code"] == 200
        assert json_data["data"]["username"] == "test111"
        assert "tokens" not in json_data["data"]

    def test_get_user_info_no_token(self):
        resp = requests.get(f"{BASE_URL}/users/me/")
        assert resp.status_code == 401


class TestUpdateUserInfo:
    """更新用户信息接口测试"""

    @pytest.fixture(autouse=True)
    def setup(self, auth):
        self.token = auth["token"]

    def test_update_user_info(self):
        resp = requests.put(f"{BASE_URL}/users/me/", json={"nickname": "新昵称"}, headers={
            "Authorization": f"Bearer {self.token}"
        })
        assert resp.status_code == 200
        json_data = resp.json()
        assert json_data["code"] == 200
        assert json_data["data"]["nickname"] == "新昵称"

    def test_update_user_info_no_token(self):
        resp = requests.put(f"{BASE_URL}/users/me/", json={"nickname": "test"})
        assert resp.status_code == 401

    def test_update_user_info_wrong_token(self):
        headers = {"Authorization": "Bearer invalid_token_12345"}
        resp = requests.put(f"{BASE_URL}/users/me/", json={"nickname": "test"}, headers=headers)
        assert resp.status_code == 401


class TestRefreshToken:
    """刷新 token 接口测试"""

    @pytest.fixture(autouse=True)
    def setup(self, auth):
        self.token = auth["token"]
        self.refresh = auth["refresh"]

    def test_refresh_token(self):
        resp = requests.post(f"{BASE_URL}/users/token/refresh/", json={
            "refresh": self.refresh
        })
        assert resp.status_code == 200
        json_data = resp.json()
        assert "access" in json_data
        assert "refresh" in json_data

    def test_refresh_token_wrong(self):
        resp = requests.post(f"{BASE_URL}/users/token/refresh/", json={
            "refresh": "invalid_token_12345"
        })
        assert resp.status_code == 401
        assert "Token is invalid" in resp.json()["message"]

    def test_refresh_token_missing(self):
        resp = requests.post(f"{BASE_URL}/users/token/refresh/", json={})
        assert resp.status_code == 400
        assert "refresh" in resp.json()["message"]

    def test_refresh_token_reuse(self):
        """重复刷新：第二次失败（已拉黑）"""
        # 需要独立的登录，因为刷新会消耗 refresh token
        login_resp = requests.post(f"{BASE_URL}/users/login/", json={
            "username": "test111", "password": "1234567811"
        })
        refresh_token = login_resp.json()["data"]["tokens"]["refresh"]

        resp1 = requests.post(f"{BASE_URL}/users/token/refresh/", json={
            "refresh": refresh_token
        })
        assert resp1.status_code == 200

        resp2 = requests.post(f"{BASE_URL}/users/token/refresh/", json={
            "refresh": refresh_token
        })
        assert resp2.status_code == 401


class TestUpdateUserPassword:
    """更新用户密码接口测试"""

    @pytest.fixture(autouse=True)
    def setup(self, auth):
        self.token = auth["token"]

    def test_update_user_password(self):
        """正常修改密码（用临时账号，不影响 test111）"""
        timestamp = int(time.time() * 1000)
        username = f"temp_{timestamp}"
        requests.post(f"{BASE_URL}/users/register/", json={
            "username": username,
            "password": "12345678",
            "password_confirm": "12345678"
        })
        login_resp = requests.post(f"{BASE_URL}/users/login/", json={
            "username": username, "password": "12345678"
        })
        access_token = login_resp.json()["data"]["tokens"]["access"]

        resp = requests.put(f"{BASE_URL}/users/me/password/", json={
            "old_password": "12345678",
            "new_password": "87654321",
            "new_password_confirm": "87654321"
        }, headers={"Authorization": f"Bearer {access_token}"})
        assert resp.status_code == 200
        assert resp.json()["code"] == 200

        # 验证新密码可登录
        login_resp2 = requests.post(f"{BASE_URL}/users/login/", json={
            "username": username, "password": "87654321"
        })
        assert login_resp2.status_code == 200

    def test_update_user_password_wrong_old(self):
        resp = requests.put(f"{BASE_URL}/users/me/password/", json={
            "old_password": "wrong_password",
            "new_password": "87654321",
            "new_password_confirm": "87654321"
        }, headers={"Authorization": f"Bearer {self.token}"})
        assert resp.status_code == 400
        assert resp.json()["message"] == "old_password: 旧密码错误"

    def test_update_user_password_not_match(self):
        resp = requests.put(f"{BASE_URL}/users/me/password/", json={
            "old_password": "1234567811",
            "new_password": "87654321",
            "new_password_confirm": "12345678"
        }, headers={"Authorization": f"Bearer {self.token}"})
        assert resp.status_code == 400
        assert resp.json()["message"] == "new_password_confirm: 两次密码不一致"

    def test_update_user_password_no_token(self):
        resp = requests.put(f"{BASE_URL}/users/me/password/", json={
            "old_password": "1234567811",
            "new_password": "87654321",
            "new_password_confirm": "87654321"
        })
        assert resp.status_code == 401


class TestUploadAvatar:
    """上传头像接口测试（multipart/form-data）"""

    @pytest.fixture(autouse=True)
    def setup(self, auth):
        self.token = auth["token"]

    def test_upload_avatar(self):
        from PIL import Image
        import io
        img = Image.new('RGB', (1, 1), color='red')
        buf = io.BytesIO()
        img.save(buf, format='PNG')
        buf.name = 'test.png'

        resp = requests.post(f"{BASE_URL}/users/me/avatar/", files={
            "avatar": buf
        }, headers={"Authorization": f"Bearer {self.token}"})
        assert resp.status_code == 200
        json_data = resp.json()
        assert json_data["code"] == 200
        assert "avatar" in json_data["data"]

    def test_upload_avatar_no_file(self):
        resp = requests.post(f"{BASE_URL}/users/me/avatar/", headers={
            "Authorization": f"Bearer {self.token}"
        })
        assert resp.status_code == 400

    def test_upload_avatar_no_token(self):
        resp = requests.post(f"{BASE_URL}/users/me/avatar/")
        assert resp.status_code == 401


class TestPreferences:
    """用户偏好设置接口测试"""

    @pytest.fixture(autouse=True)
    def setup(self, auth):
        self.token = auth["token"]

    def test_get_preferences(self):
        resp = requests.get(f"{BASE_URL}/users/preferences/", headers={
            "Authorization": f"Bearer {self.token}"
        })
        assert resp.status_code == 200
        assert resp.json()["code"] == 200

    def test_update_preferences(self):
        resp = requests.put(f"{BASE_URL}/users/preferences/", json={
            "language": "zh", "currency": "CNY"
        }, headers={"Authorization": f"Bearer {self.token}"})
        assert resp.status_code == 200
        assert resp.json()["code"] == 200

    def test_get_preferences_no_token(self):
        resp = requests.get(f"{BASE_URL}/users/preferences/")
        assert resp.status_code == 401

    def test_update_preferences_no_token(self):
        resp = requests.put(f"{BASE_URL}/users/preferences/", json={
            "language": "zh"
        })
        assert resp.status_code == 401


class TestBindPhone:
    """绑定手机号接口测试"""

    @pytest.fixture(autouse=True)
    def setup(self, auth):
        self.token = auth["token"]

    def test_bind_phone(self):
        resp = requests.post(f"{BASE_URL}/users/me/phone/bind/", json={
            "phone": "13800138000"
        }, headers={"Authorization": f"Bearer {self.token}"})
        assert resp.status_code == 200
        json_data = resp.json()
        assert json_data["code"] == 200
        assert json_data["data"]["phone"] == "13800138000"

    def test_bind_phone_invalid(self):
        resp = requests.post(f"{BASE_URL}/users/me/phone/bind/", json={
            "phone": "123"
        }, headers={"Authorization": f"Bearer {self.token}"})
        assert resp.status_code == 400

    def test_bind_phone_no_token(self):
        resp = requests.post(f"{BASE_URL}/users/me/phone/bind/", json={
            "phone": "13800138000"
        })
        assert resp.status_code == 401


class TestAddress:
    """收货地址接口测试

    覆盖: 创建 → 列表 → 详情 → 修改 → 设默认 → 删除 → 验证已删
    """

    @pytest.fixture(autouse=True)
    def setup(self, auth):
        self.token = auth["token"]

    def test_address_lifecycle(self):
        """完整生命周期"""
        # 1. 创建
        resp = requests.post(f"{BASE_URL}/users/address/", json={
            "receiver_name": "张三",
            "receiver_phone": "13800138000",
            "province": "广东省",
            "city": "深圳市",
            "district": "南山区",
            "detail_address": "科技园路1号",
        }, headers={"Authorization": f"Bearer {self.token}"})
        assert resp.status_code == 201
        assert resp.json()["message"] == "添加成功"
        addr_id = resp.json()["data"]["id"]

        # 2. 查列表
        resp = requests.get(f"{BASE_URL}/users/address/", headers={
            "Authorization": f"Bearer {self.token}"
        })
        assert resp.status_code == 200
        assert any(a["id"] == addr_id for a in resp.json()["data"])

        # 3. 查详情
        resp = requests.get(f"{BASE_URL}/users/address/{addr_id}/", headers={
            "Authorization": f"Bearer {self.token}"
        })
        assert resp.status_code == 200
        assert resp.json()["data"]["receiver_name"] == "张三"

        # 4. 修改
        resp = requests.put(f"{BASE_URL}/users/address/{addr_id}/", json={
            "receiver_name": "李四",
            "receiver_phone": "13900139000",
        }, headers={"Authorization": f"Bearer {self.token}"})
        assert resp.status_code == 200
        assert resp.json()["data"]["receiver_name"] == "李四"

        # 5. 设默认
        resp = requests.put(f"{BASE_URL}/users/address/{addr_id}/default/", headers={
            "Authorization": f"Bearer {self.token}"
        })
        assert resp.status_code == 200
        assert resp.json()["message"] == "设置成功"

        # 6. 删除
        resp = requests.delete(f"{BASE_URL}/users/address/{addr_id}/", headers={
            "Authorization": f"Bearer {self.token}"
        })
        assert resp.status_code == 200
        assert resp.json()["message"] == "删除成功"

        # 7. 验证已删
        resp = requests.get(f"{BASE_URL}/users/address/{addr_id}/", headers={
            "Authorization": f"Bearer {self.token}"
        })
        assert resp.status_code == 404

    def test_address_list(self):
        """获取地址列表"""
        resp = requests.get(f"{BASE_URL}/users/address/", headers={
            "Authorization": f"Bearer {self.token}"
        })
        assert resp.status_code == 200
        assert resp.json()["code"] == 200

    def test_address_no_token(self):
        """无 token 访问"""
        resp = requests.get(f"{BASE_URL}/users/address/")
        assert resp.status_code == 401

    def test_address_detail_not_exist(self):
        """访问不存在的地址 → 404"""
        resp = requests.get(f"{BASE_URL}/users/address/99999/", headers={
            "Authorization": f"Bearer {self.token}"
        })
        assert resp.status_code == 404

    def test_address_default_not_exist(self):
        """设置不存在的地址为默认 → 404"""
        resp = requests.put(f"{BASE_URL}/users/address/99999/default/", headers={
            "Authorization": f"Bearer {self.token}"
        })
        assert resp.status_code == 404


class TestUpgradeToSeller:
    """升级为商家接口测试"""

    def test_upgrade(self):
        """普通用户升级为商家"""
        timestamp = int(time.time() * 1000)
        username = f"upgrade_{timestamp}"
        reg = requests.post(f"{BASE_URL}/users/register/", json={
            "username": username,
            "password": "12345678",
            "password_confirm": "12345678",
        })
        assert reg.status_code == 201
        token = reg.json()["data"]["tokens"]["access"]

        resp = requests.post(f"{BASE_URL}/users/upgrade/", json={
            "shop_name": "我的小店"
        }, headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        assert resp.json()["data"]["role"] == "seller"

    def test_upgrade_already_seller(self, seller_auth):
        """已是商家再升级 → 400"""
        resp = requests.post(f"{BASE_URL}/users/upgrade/", json={
            "shop_name": "再升级"
        }, headers={"Authorization": f"Bearer {seller_auth['token']}"})
        assert resp.status_code == 400
        assert resp.json()["message"] == "您已经是商家，无需重复升级"

    def test_upgrade_no_shop_name(self):
        """缺店铺名 → 400"""
        timestamp = int(time.time() * 1000)
        reg = requests.post(f"{BASE_URL}/users/register/", json={
            "username": f"up2_{timestamp}",
            "password": "12345678",
            "password_confirm": "12345678",
        })
        token = reg.json()["data"]["tokens"]["access"]
        resp = requests.post(f"{BASE_URL}/users/upgrade/", json={}, headers={
            "Authorization": f"Bearer {token}"
        })
        assert resp.status_code == 400

    def test_upgrade_no_token(self):
        """无 token → 401"""
        resp = requests.post(f"{BASE_URL}/users/upgrade/", json={
            "shop_name": "test"
        })
        assert resp.status_code == 401


class TestShopSettings:
    """店铺设置接口测试"""

    @pytest.fixture(autouse=True)
    def setup(self, seller_auth):
        self.seller_token = seller_auth["token"]

    def test_get_shop_settings(self):
        """获取店铺设置"""
        resp = requests.get(f"{BASE_URL}/users/shop-settings/", headers={
            "Authorization": f"Bearer {self.seller_token}"
        })
        assert resp.status_code == 200
        assert resp.json()["data"]["shop_name"] == "测试店铺"

    def test_update_shop_settings(self):
        """更新店铺设置"""
        resp = requests.put(f"{BASE_URL}/users/shop-settings/", json={
            "shop_name": "新店铺名",
            "shop_description": "新描述"
        }, headers={"Authorization": f"Bearer {self.seller_token}"})
        assert resp.status_code == 200
        assert resp.json()["message"] == "更新成功"
        # 恢复原名
        requests.put(f"{BASE_URL}/users/shop-settings/", json={
            "shop_name": "测试店铺"
        }, headers={"Authorization": f"Bearer {self.seller_token}"})

    def test_shop_settings_not_seller(self, auth):
        """普通用户访问 → 403"""
        resp = requests.get(f"{BASE_URL}/users/shop-settings/", headers={
            "Authorization": f"Bearer {auth['token']}"
        })
        assert resp.status_code == 403

    def test_shop_settings_no_token(self):
        """无 token → 401"""
        resp = requests.get(f"{BASE_URL}/users/shop-settings/")
        assert resp.status_code == 401


class TestSendCode:
    """发送验证码接口测试"""

    def test_send_code_phone(self):
        """手机号发送验证码"""
        resp = requests.post(f"{BASE_URL}/users/send_code/", json={
            "target": "13800138000",
            "code_type": "register"
        })
        assert resp.status_code == 200
        assert resp.json()["code"] == 200
        assert len(resp.json()["data"]["code"]) == 6

    def test_send_code_email(self):
        """邮箱发送验证码"""
        resp = requests.post(f"{BASE_URL}/users/send_code/", json={
            "target": "test@example.com",
            "code_type": "login"
        })
        assert resp.status_code == 200
        assert resp.json()["code"] == 200

    def test_send_code_missing_target(self):
        """缺 target → 400"""
        resp = requests.post(f"{BASE_URL}/users/send_code/", json={
            "code_type": "register"
        })
        assert resp.status_code == 400