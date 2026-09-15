# 测试基础配置
import requests
import pytest

BASE_URL = 'http://localhost:8000/api/v1'


@pytest.fixture(scope="session")
def auth():
    """
    模块级别的登录 fixture：整个 test_users.py 只登录一次，所有类共享 token

    用法：
        class TestXxx:
            @pytest.fixture(autouse=True)
            def setup(self, auth):
                self.token = auth["token"]
                self.refresh = auth["refresh"]

    注意：
        如果某个测试类不需要登录（如 TestRegister、TestLogin），
        就不要引入这个 fixture，避免浪费一次请求。
    """
    resp = requests.post(f"{BASE_URL}/users/login/", json={
        "username": "test111",
        "password": "1234567811",
    })
    assert resp.status_code == 200, f"登录失败: {resp.text}"
    data = resp.json()["data"]
    return {
        "token": data["tokens"]["access"],
        "refresh": data["tokens"]["refresh"],
        "user": data["user"],
    }


@pytest.fixture(scope="session")
def seller_auth():
    """
    商家登录 fixture，用于 shop-settings / goods 写操作 / orders 发货等商家专属接口

    用法同 auth fixture
    """
    resp = requests.post(f"{BASE_URL}/users/login/", json={
        "username": "seller111",
        "password": "1234567811",
    })
    assert resp.status_code == 200, f"商家登录失败: {resp.text}"
    data = resp.json()["data"]
    return {
        "token": data["tokens"]["access"],
        "refresh": data["tokens"]["refresh"],
        "user": data["user"],
    }