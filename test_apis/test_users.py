"""用户模块接口测试"""

import time

import allure
import pytest
from client import APIClient, anon
from schemas import (
    WrappedAddressListResponse,
    WrappedAddressResponse,
    WrappedRegisterResponse,
    WrappedUserInfoResponse,
    assert_valid,
)


@allure.feature("用户模块")
@allure.story("用户注册")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.p2
class TestRegister:
    """用户注册接口测试（无需登录）"""

    def test_register(self):
        timestamp = int(time.time() * 1000)
        register_data = {
            "username": f"test_{timestamp}",
            "password": "1234567811",
            "password_confirm": "1234567811",
        }
        response = anon.post("/users/register/", json=register_data)
        assert response.status_code == 201
        assert_valid(WrappedRegisterResponse, response.json(), context="用户注册")
        assert "tokens" in response.json()["data"]

    def test_register_password_not_match(self):
        timestamp = int(time.time() * 1000)
        register_data = {
            "username": f"test_{timestamp}",
            "password": "12345678",
            "password_confirm": "1234567789",
        }
        response = anon.post("/users/register/", json=register_data)
        assert response.status_code == 400
        json_data = response.json()
        assert json_data["code"] == 400
        assert "errors" in json_data
        assert json_data["message"] == "password_confirm: 两次密码不一致"


@allure.feature("用户模块")
@allure.story("用户登录")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.p2
class TestLogin:
    """用户登录接口测试（无需登录）"""

    @pytest.mark.smoke
    def test_login(self):
        login_data = {"username": "test111", "password": "1234567811"}
        response = anon.post("/users/login/", json=login_data)
        assert response.status_code == 200
        json_data = response.json()
        assert json_data["code"] == 200
        assert "tokens" in json_data["data"]

    def test_login_username_not_exist(self):
        login_data = {"username": "test111_not_exist", "password": "1234567811"}
        response = anon.post("/users/login/", json=login_data)
        assert response.status_code == 400
        json_data = response.json()
        assert json_data["code"] == 400
        assert json_data["message"] == "non_field_errors: 用户名或密码错误"

    def test_login_password_error(self):
        login_data = {"username": "test111", "password": "12345678"}
        response = anon.post("/users/login/", json=login_data)
        assert response.status_code == 400
        json_data = response.json()
        assert json_data["code"] == 400
        assert json_data["message"] == "non_field_errors: 用户名或密码错误"


@allure.feature("用户模块")
@allure.story("获取用户信息")
@allure.severity(allure.severity_level.NORMAL)
class TestGetUserInfo:
    """获取用户信息接口测试"""

    @pytest.fixture(autouse=True)
    def setup(self, auth):
        self.token = auth["token"]
        self.client = APIClient(self.token)

    def test_get_user_info(self):
        resp = self.client.get("/users/me/")
        assert resp.status_code == 200
        assert_valid(WrappedUserInfoResponse, resp.json(), context="用户信息")

    def test_get_user_info_no_token(self):
        resp = anon.get("/users/me/")
        assert resp.status_code == 401


@allure.feature("用户模块")
@allure.story("更新用户信息")
@allure.severity(allure.severity_level.NORMAL)
class TestUpdateUserInfo:
    """更新用户信息接口测试"""

    @pytest.fixture(autouse=True)
    def setup(self, auth):
        self.token = auth["token"]
        self.client = APIClient(self.token)

    def test_update_user_info(self):
        resp = self.client.put("/users/me/", json={"nickname": "新昵称"})
        assert resp.status_code == 200
        json_data = resp.json()
        assert json_data["code"] == 200
        assert json_data["data"]["nickname"] == "新昵称"

    def test_update_user_info_no_token(self):
        resp = anon.put("/users/me/", json={"nickname": "test"})
        assert resp.status_code == 401

    def test_update_user_info_wrong_token(self):
        client = APIClient("invalid_token_12345")
        resp = client.put("/users/me/", json={"nickname": "test"})
        assert resp.status_code == 401


@allure.feature("用户模块")
@allure.story("刷新Token")
@allure.severity(allure.severity_level.CRITICAL)
class TestRefreshToken:
    """刷新 token 接口测试"""

    @pytest.fixture(autouse=True)
    def setup(self, auth):
        self.token = auth["token"]
        self.refresh = auth["refresh"]

    def test_refresh_token(self):
        resp = anon.post("/users/token/refresh/", json={"refresh": self.refresh})
        assert resp.status_code == 200
        json_data = resp.json()
        assert "access" in json_data
        assert "refresh" in json_data

    def test_refresh_token_wrong(self):
        resp = anon.post(
            "/users/token/refresh/", json={"refresh": "invalid_token_12345"}
        )
        assert resp.status_code == 401
        assert "Token is invalid" in resp.json()["message"]

    def test_refresh_token_missing(self):
        resp = anon.post("/users/token/refresh/", json={})
        assert resp.status_code == 400
        assert "refresh" in resp.json()["message"]

    def test_refresh_token_reuse(self):
        """重复刷新：第二次失败（已拉黑）"""
        login_resp = anon.post(
            "/users/login/",
            json={"username": "test111", "password": "1234567811"},
        )
        refresh_token = login_resp.json()["data"]["tokens"]["refresh"]

        resp1 = anon.post("/users/token/refresh/", json={"refresh": refresh_token})
        assert resp1.status_code == 200

        resp2 = anon.post("/users/token/refresh/", json={"refresh": refresh_token})
        assert resp2.status_code == 401


@allure.feature("用户模块")
@allure.story("修改密码")
@allure.severity(allure.severity_level.CRITICAL)
class TestUpdateUserPassword:
    """更新用户密码接口测试"""

    @pytest.fixture(autouse=True)
    def setup(self, auth):
        self.token = auth["token"]
        self.client = APIClient(self.token)

    def test_update_user_password(self):
        """正常修改密码（用临时账号，不影响 test111）"""
        timestamp = int(time.time() * 1000)
        username = f"temp_{timestamp}"
        anon.post(
            "/users/register/",
            json={
                "username": username,
                "password": "12345678",
                "password_confirm": "12345678",
            },
        )
        login_resp = anon.post(
            "/users/login/",
            json={"username": username, "password": "12345678"},
        )
        access_token = login_resp.json()["data"]["tokens"]["access"]
        temp_client = APIClient(access_token)

        resp = temp_client.put(
            "/users/me/password/",
            json={
                "old_password": "12345678",
                "new_password": "87654321",
                "new_password_confirm": "87654321",
            },
        )
        assert resp.status_code == 200
        assert resp.json()["code"] == 200

        login_resp2 = anon.post(
            "/users/login/",
            json={"username": username, "password": "87654321"},
        )
        assert login_resp2.status_code == 200

    def test_update_user_password_wrong_old(self):
        resp = self.client.put(
            "/users/me/password/",
            json={
                "old_password": "wrong_password",
                "new_password": "87654321",
                "new_password_confirm": "87654321",
            },
        )
        assert resp.status_code == 400
        assert resp.json()["message"] == "old_password: 旧密码错误"

    def test_update_user_password_not_match(self):
        resp = self.client.put(
            "/users/me/password/",
            json={
                "old_password": "1234567811",
                "new_password": "87654321",
                "new_password_confirm": "12345678",
            },
        )
        assert resp.status_code == 400
        assert resp.json()["message"] == "new_password_confirm: 两次密码不一致"

    def test_update_user_password_no_token(self):
        resp = anon.put(
            "/users/me/password/",
            json={
                "old_password": "1234567811",
                "new_password": "87654321",
                "new_password_confirm": "87654321",
            },
        )
        assert resp.status_code == 401


@allure.feature("用户模块")
@allure.story("上传头像")
@allure.severity(allure.severity_level.MINOR)
class TestUploadAvatar:
    """上传头像接口测试（multipart/form-data）"""

    @pytest.fixture(autouse=True)
    def setup(self, auth):
        self.token = auth["token"]
        self.client = APIClient(self.token)

    def test_upload_avatar(self):
        import io

        from PIL import Image

        img = Image.new("RGB", (1, 1), color="red")
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.name = "test.png"

        resp = self.client.post("/users/me/avatar/", files={"avatar": buf})
        assert resp.status_code == 200
        json_data = resp.json()
        assert json_data["code"] == 200
        assert "avatar" in json_data["data"]

    def test_upload_avatar_no_file(self):
        resp = self.client.post("/users/me/avatar/")
        assert resp.status_code == 400

    def test_upload_avatar_no_token(self):
        resp = anon.post("/users/me/avatar/")
        assert resp.status_code == 401


@allure.feature("用户模块")
@allure.story("用户偏好")
@allure.severity(allure.severity_level.MINOR)
class TestPreferences:
    """用户偏好设置接口测试"""

    @pytest.fixture(autouse=True)
    def setup(self, auth):
        self.token = auth["token"]
        self.client = APIClient(self.token)

    def test_get_preferences(self):
        resp = self.client.get("/users/preferences/")
        assert resp.status_code == 200
        assert resp.json()["code"] == 200

    def test_update_preferences(self):
        resp = self.client.put(
            "/users/preferences/",
            json={"language": "zh", "currency": "CNY"},
        )
        assert resp.status_code == 200
        assert resp.json()["code"] == 200

    def test_get_preferences_no_token(self):
        resp = anon.get("/users/preferences/")
        assert resp.status_code == 401

    def test_update_preferences_no_token(self):
        resp = anon.put("/users/preferences/", json={"language": "zh"})
        assert resp.status_code == 401


@allure.feature("用户模块")
@allure.story("绑定手机号")
@allure.severity(allure.severity_level.NORMAL)
class TestBindPhone:
    """绑定手机号接口测试"""

    @pytest.fixture(autouse=True)
    def setup(self, auth):
        self.token = auth["token"]
        self.client = APIClient(self.token)

    def test_bind_phone(self):
        resp = self.client.post("/users/me/phone/bind/", json={"phone": "13800138000"})
        assert resp.status_code == 200
        json_data = resp.json()
        assert json_data["code"] == 200
        assert json_data["data"]["phone"] == "13800138000"

    def test_bind_phone_invalid(self):
        resp = self.client.post("/users/me/phone/bind/", json={"phone": "123"})
        assert resp.status_code == 400

    def test_bind_phone_no_token(self):
        resp = anon.post("/users/me/phone/bind/", json={"phone": "13800138000"})
        assert resp.status_code == 401


@allure.feature("用户模块")
@allure.story("收货地址")
@allure.severity(allure.severity_level.NORMAL)
class TestAddress:
    """收货地址接口测试

    覆盖: 创建 → 列表 → 详情 → 修改 → 设默认 → 删除 → 验证已删
    """

    @pytest.fixture(autouse=True)
    def setup(self, auth):
        self.token = auth["token"]
        self.client = APIClient(self.token)

    def test_address_lifecycle(self):
        """完整生命周期"""
        resp = self.client.post(
            "/users/address/",
            json={
                "receiver_name": "张三",
                "receiver_phone": "13800138000",
                "province": "广东省",
                "city": "深圳市",
                "district": "南山区",
                "detail_address": "科技园路1号",
            },
        )
        assert resp.status_code == 201
        assert_valid(WrappedAddressResponse, resp.json(), context="创建地址")
        addr_id = resp.json()["data"]["id"]

        resp = self.client.get("/users/address/")
        assert resp.status_code == 200
        assert any(a["id"] == addr_id for a in resp.json()["data"])

        resp = self.client.get(f"/users/address/{addr_id}/")
        assert resp.status_code == 200
        assert resp.json()["data"]["receiver_name"] == "张三"

        resp = self.client.put(
            f"/users/address/{addr_id}/",
            json={"receiver_name": "李四", "receiver_phone": "13900139000"},
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["receiver_name"] == "李四"

        resp = self.client.put(f"/users/address/{addr_id}/default/")
        assert resp.status_code == 200
        assert resp.json()["message"] == "设置成功"

        resp = self.client.delete(f"/users/address/{addr_id}/")
        assert resp.status_code == 200
        assert resp.json()["message"] == "删除成功"

        resp = self.client.get(f"/users/address/{addr_id}/")
        assert resp.status_code == 404

    def test_address_list(self):
        """获取地址列表"""
        resp = self.client.get("/users/address/")
        assert resp.status_code == 200
        assert_valid(WrappedAddressListResponse, resp.json(), context="地址列表")

    def test_address_no_token(self):
        """无 token 访问"""
        resp = anon.get("/users/address/")
        assert resp.status_code == 401

    def test_address_detail_not_exist(self):
        """访问不存在的地址 → 404"""
        resp = self.client.get("/users/address/99999/")
        assert resp.status_code == 404

    def test_address_default_not_exist(self):
        """设置不存在的地址为默认 → 404"""
        resp = self.client.put("/users/address/99999/default/")
        assert resp.status_code == 404


@allure.feature("用户模块")
@allure.story("升级为商家")
@allure.severity(allure.severity_level.NORMAL)
class TestUpgradeToSeller:
    """升级为商家接口测试"""

    def test_upgrade(self):
        """普通用户升级为商家"""
        timestamp = int(time.time() * 1000)
        username = f"upgrade_{timestamp}"
        reg = anon.post(
            "/users/register/",
            json={
                "username": username,
                "password": "12345678",
                "password_confirm": "12345678",
            },
        )
        assert reg.status_code == 201
        token = reg.json()["data"]["tokens"]["access"]
        client = APIClient(token)

        resp = client.post("/users/upgrade/", json={"shop_name": "我的小店"})
        assert resp.status_code == 200
        assert resp.json()["data"]["role"] == "seller"

    def test_upgrade_already_seller(self, seller_auth):
        """已是商家再升级 → 400"""
        client = APIClient(seller_auth["token"])
        resp = client.post("/users/upgrade/", json={"shop_name": "再升级"})
        assert resp.status_code == 400
        assert resp.json()["message"] == "您已经是商家，无需重复升级"

    def test_upgrade_no_shop_name(self):
        """缺店铺名 → 400"""
        timestamp = int(time.time() * 1000)
        reg = anon.post(
            "/users/register/",
            json={
                "username": f"up2_{timestamp}",
                "password": "12345678",
                "password_confirm": "12345678",
            },
        )
        token = reg.json()["data"]["tokens"]["access"]
        client = APIClient(token)
        resp = client.post("/users/upgrade/", json={})
        assert resp.status_code == 400

    def test_upgrade_no_token(self):
        """无 token → 401"""
        resp = anon.post("/users/upgrade/", json={"shop_name": "test"})
        assert resp.status_code == 401


@allure.feature("用户模块")
@allure.story("店铺设置")
@allure.severity(allure.severity_level.NORMAL)
class TestShopSettings:
    """店铺设置接口测试"""

    @pytest.fixture(autouse=True)
    def setup(self, seller_auth):
        self.seller_token = seller_auth["token"]
        self.client = APIClient(self.seller_token)

    def test_get_shop_settings(self):
        """获取店铺设置"""
        resp = self.client.get("/users/shop-settings/")
        assert resp.status_code == 200
        assert resp.json()["data"]["shop_name"] == "测试店铺"

    def test_update_shop_settings(self):
        """更新店铺设置"""
        resp = self.client.put(
            "/users/shop-settings/",
            json={"shop_name": "新店铺名", "shop_description": "新描述"},
        )
        assert resp.status_code == 200
        assert resp.json()["message"] == "更新成功"
        self.client.put(
            "/users/shop-settings/",
            json={"shop_name": "测试店铺"},
        )

    def test_shop_settings_not_seller(self, auth):
        """普通用户访问 → 403"""
        client = APIClient(auth["token"])
        resp = client.get("/users/shop-settings/")
        assert resp.status_code == 403

    def test_shop_settings_no_token(self):
        """无 token → 401"""
        resp = anon.get("/users/shop-settings/")
        assert resp.status_code == 401
