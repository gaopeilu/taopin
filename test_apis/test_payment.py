"""支付模块的接口测试"""

import time

import allure
import pytest
from client import APIClient, anon
from conftest import get_any_sku_id
from schemas import WrappedPaymentResponse, assert_valid

SKU_ID = 18  # 稳定的测试 SKU（优先使用，若库存不足则动态查找）


def _get_sku_id():
    """获取一个有库存的 SKU ID"""
    sku_id = get_any_sku_id()
    return sku_id if sku_id is not None else SKU_ID


def _create_order(token):
    """创建订单并返回 order_no"""
    sku_id = _get_sku_id()
    resp = APIClient(token).post(
        "/orders/",
        json={
            "items": [{"sku_id": sku_id, "quantity": 1}],
            "receiver_name": "测试",
            "receiver_phone": "13800138000",
            "receiver_address": "北京",
        },
    )
    assert resp.status_code == 201
    return resp.json()["data"]["order_no"]


def _create_payment(token, order_no):
    """发起支付并返回 pay_no"""
    resp = APIClient(token).post(
        "/payment/create/",
        json={"order_no": order_no, "pay_method": "wechat"},
    )
    return resp


# ==================== 发起支付 ====================
@allure.feature("支付模块")
@allure.story("创建支付")
@allure.severity(allure.severity_level.CRITICAL)
class TestPaymentCreate:
    @pytest.fixture(autouse=True)
    def setup(self, auth):
        self.token = auth["token"]
        self.client = APIClient(self.token)

    @pytest.mark.smoke
    def test_create_success(self):
        """正常发起支付"""
        order_no = _create_order(self.token)
        resp = self.client.post(
            "/payment/create/",
            json={"order_no": order_no, "pay_method": "wechat"},
        )
        assert resp.status_code == 200
        assert_valid(WrappedPaymentResponse, resp.json(), context="创建支付")
        data = resp.json()["data"]
        assert "pay_no" in data
        assert data["order_no"] == order_no
        assert data["status"] == "pending"

    def test_create_order_not_found(self):
        """订单不存在"""
        resp = self.client.post(
            "/payment/create/",
            json={"order_no": "ORDNOTEXISTS12345", "pay_method": "wechat"},
        )
        assert resp.status_code == 404
        assert "订单不存在" in resp.json()["message"]

    def test_create_order_not_pending(self):
        """已支付订单不能再次发起支付"""
        order_no = _create_order(self.token)
        resp = _create_payment(self.token, order_no)
        pay_no = resp.json()["data"]["pay_no"]
        self.client.post(
            "/payment/mock-pay/",
            json={"pay_no": pay_no},
        )
        resp = self.client.post(
            "/payment/create/",
            json={"order_no": order_no, "pay_method": "wechat"},
        )
        assert resp.status_code == 400

    def test_create_no_auth(self):
        """未登录"""
        resp = anon.post(
            "/payment/create/",
            json={"order_no": "ORDNOTEXISTS", "pay_method": "wechat"},
        )
        assert resp.status_code == 401


# ==================== 模拟支付 ====================
@allure.feature("支付模块")
@allure.story("模拟支付")
@allure.severity(allure.severity_level.CRITICAL)
class TestMockPay:
    @pytest.fixture(autouse=True)
    def setup(self, auth):
        self.token = auth["token"]
        self.client = APIClient(self.token)

    def test_mock_pay_success(self):
        """模拟支付成功"""
        order_no = _create_order(self.token)
        resp = _create_payment(self.token, order_no)
        pay_no = resp.json()["data"]["pay_no"]

        resp = self.client.post(
            "/payment/mock-pay/",
            json={"pay_no": pay_no},
        )
        assert resp.status_code == 200
        assert resp.json()["message"] == "支付成功"
        assert resp.json()["data"]["status"] == "success"

    def test_mock_pay_not_found(self):
        """支付记录不存在"""
        resp = self.client.post(
            "/payment/mock-pay/",
            json={"pay_no": "PAYNOTEXISTS12345"},
        )
        assert resp.status_code == 404

    def test_mock_pay_already_paid(self):
        """不能重复支付"""
        order_no = _create_order(self.token)
        resp = _create_payment(self.token, order_no)
        pay_no = resp.json()["data"]["pay_no"]

        self.client.post(
            "/payment/mock-pay/",
            json={"pay_no": pay_no},
        )

        resp = self.client.post(
            "/payment/mock-pay/",
            json={"pay_no": pay_no},
        )
        assert resp.status_code == 400

    def test_mock_pay_no_auth(self):
        """未登录"""
        resp = anon.post("/payment/mock-pay/", json={"pay_no": "PAYNOTEXISTS"})
        assert resp.status_code == 401


# ==================== 支付状态查询 ====================
@allure.feature("支付模块")
@allure.story("支付状态")
@allure.severity(allure.severity_level.NORMAL)
class TestPaymentStatus:
    @pytest.fixture(autouse=True)
    def setup(self, auth):
        self.token = auth["token"]
        self.client = APIClient(self.token)

    def test_status_success(self):
        """查询支付状态"""
        order_no = _create_order(self.token)
        resp = _create_payment(self.token, order_no)
        pay_no = resp.json()["data"]["pay_no"]

        self.client.post(
            "/payment/mock-pay/",
            json={"pay_no": pay_no},
        )

        resp = self.client.get(f"/payment/{pay_no}/status/")
        assert resp.status_code == 200
        assert resp.json()["code"] == 200
        assert resp.json()["data"]["status"] == "success"

    def test_status_not_found(self):
        """不存在的支付记录"""
        resp = self.client.get("/payment/PAYNOTEXISTS/status/")
        assert resp.status_code == 404

    def test_status_no_auth(self):
        """未登录"""
        resp = anon.get("/payment/PAYNOTEXISTS/status/")
        assert resp.status_code == 401


# ==================== 支付回调 ====================
@allure.feature("支付模块")
@allure.story("支付回调")
@allure.severity(allure.severity_level.CRITICAL)
class TestPaymentCallback:
    @pytest.fixture(autouse=True)
    def setup(self, auth):
        self.token = auth["token"]
        self.client = APIClient(self.token)

    def test_callback_no_signature(self):
        """无签名 → 403"""
        resp = anon.post(
            "/payment/callback/",
            json={"pay_no": "PAYNOTEXISTS", "trade_no": "TN123", "status": "success"},
        )
        assert resp.status_code == 403
        assert "签名" in resp.json()["message"]

    def test_callback_success(self):
        """带正确签名，不存在的 pay_no → 404"""
        resp = anon.post(
            "/payment/callback/",
            json={"pay_no": "PAYNOTEXISTS", "trade_no": "TN123", "status": "success"},
            extra_headers={"X-Callback-Secret": "dianshang_callback_secret_2026"},
        )
        assert resp.status_code == 404

    def test_callback_invalid_status(self):
        """无效状态值"""
        resp = anon.post(
            "/payment/callback/",
            json={
                "pay_no": "PAYNOTEXISTS",
                "trade_no": "TN123",
                "status": "invalid_status",
            },
            extra_headers={"X-Callback-Secret": "dianshang_callback_secret_2026"},
        )
        assert resp.status_code == 400

    def test_callback_idempotent(self):
        """回调幂等: 重复发送相同回调不改变状态"""
        order_no = _create_order(self.token)
        pay_resp = _create_payment(self.token, order_no)
        pay_no = pay_resp.json()["data"]["pay_no"]

        callback_payload = {
            "pay_no": pay_no,
            "trade_no": f"TN{int(time.time())}",
            "status": "success",
        }
        cb_headers = {"X-Callback-Secret": "dianshang_callback_secret_2026"}

        resp1 = anon.post(
            "/payment/callback/", json=callback_payload, extra_headers=cb_headers
        )
        assert resp1.status_code == 200

        resp2 = anon.post(
            "/payment/callback/", json=callback_payload, extra_headers=cb_headers
        )
        assert resp2.status_code == 200, (
            f"幂等回调不应报错: {resp2.status_code} {resp2.text}"
        )

        order_resp = self.client.get(f"/orders/{order_no}/")
        assert order_resp.status_code == 200
        assert order_resp.json()["status"] in ("paid", "shipped", "completed")

    def test_callback_order_status_changed(self):
        """回调成功后订单状态变为已支付"""
        order_no = _create_order(self.token)
        pay_resp = _create_payment(self.token, order_no)
        pay_no = pay_resp.json()["data"]["pay_no"]

        resp = anon.post(
            "/payment/callback/",
            json={
                "pay_no": pay_no,
                "trade_no": f"TN{int(time.time())}",
                "status": "success",
            },
            extra_headers={"X-Callback-Secret": "dianshang_callback_secret_2026"},
        )
        assert resp.status_code == 200

        order_resp = self.client.get(f"/orders/{order_no}/")
        assert order_resp.status_code == 200
        assert order_resp.json()["status"] in ("paid", "shipped", "completed"), (
            f"订单应已支付: {order_resp.json()['status']}"
        )

    def test_callback_pay_no_not_found(self):
        """回调不存在的 pay_no → 404"""
        resp = anon.post(
            "/payment/callback/",
            json={
                "pay_no": "PAYNOTEXISTS99999",
                "trade_no": "TN123",
                "status": "success",
            },
            extra_headers={"X-Callback-Secret": "dianshang_callback_secret_2026"},
        )
        assert resp.status_code == 404

    def test_callback_missing_fields(self):
        """回调缺少必填字段 → 400"""
        resp = anon.post(
            "/payment/callback/",
            json={
                "pay_no": "PAYNOTEXISTS",
            },
            extra_headers={"X-Callback-Secret": "dianshang_callback_secret_2026"},
        )
        # 后端可能返回 400(缺少字段) 或 404(pay_no 不存在)
        assert resp.status_code in (400, 404), (
            f"缺少字段应返回 400 或 404: {resp.status_code} {resp.text}"
        )
