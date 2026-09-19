"""订单模块的接口测试"""

import threading
import time

import allure
import pytest
import requests
from client import APIClient, anon
from conftest import _safe_delete, create_order, get_any_sku_id
from schemas import (
    OrderData,
    WrappedOrderResponse,
    assert_valid,
)

SKU_ID = 18  # fallback

# 共享数据缓存
_SHIP_SHARED = {}


def _get_seller_sku_id(seller_token, seller_id=None):
    """确保 seller111 有一个可用的 SKU（创建或复用），返回 sku_id"""
    if "sku_id" in _SHIP_SHARED:
        return _SHIP_SHARED["sku_id"]
    client = APIClient(seller_token)

    resp = anon.get("/goods/categories/")
    assert resp.status_code == 200
    cat_id = resp.json()["results"][0]["id"]

    spu_name = f"发货测试SPU_{int(time.time() * 1000)}"
    spu_data = {"name": spu_name, "category": cat_id}
    if seller_id:
        spu_data["seller"] = seller_id
    resp = client.post("/goods/spus/", json=spu_data)
    assert resp.status_code == 201, f"SPU 创建失败: {resp.status_code} {resp.text}"

    resp = client.get(f"/goods/spus/?search={spu_name}")
    spu_id = resp.json()["results"][0]["id"]

    client.patch(f"/goods/spus/{spu_id}/", json={"is_on_sale": True})

    sku_name = f"发货测试SKU_{int(time.time() * 1000)}"
    resp = client.post(
        "/goods/skus/",
        json={"spu": spu_id, "name": sku_name, "price": "88.00", "stock": 100},
    )
    assert resp.status_code == 201, f"SKU 创建失败: {resp.status_code} {resp.text}"
    sku_id = resp.json()["id"]

    _SHIP_SHARED["sku_id"] = sku_id
    return sku_id


def _create_order(token, sku_id=None, quantity=1, **kwargs):
    """创建订单的 helper；自动查找有库存且 SPU 未下架的 SKU"""
    if sku_id is None:
        sku_id = get_any_sku_id()
        assert sku_id is not None, "没有可用的 SKU，无法创建订单"

    data = {
        "items": [{"sku_id": sku_id, "quantity": quantity}],
        "receiver_name": kwargs.get("receiver_name", "测试用户"),
        "receiver_phone": kwargs.get("receiver_phone", "13800138000"),
        "receiver_address": kwargs.get("receiver_address", "北京测试路1号"),
    }
    return APIClient(token).post("/orders/", json=data)


# ==================== 订单列表 ====================
@allure.feature("订单模块")
@allure.story("订单列表")
@allure.severity(allure.severity_level.CRITICAL)
class TestOrderList:
    @pytest.fixture(autouse=True)
    def setup(self, auth):
        self.token = auth["token"]
        self.client = APIClient(self.token)

    def test_list_no_auth(self):
        """未登录"""
        resp = anon.get("/orders/")
        assert resp.status_code == 401

    def test_list_user(self):
        """普通用户查看自己的订单"""
        resp = self.client.get("/orders/")
        assert resp.status_code == 200
        assert "results" in resp.json()
        assert "count" in resp.json()

        if resp.json()["results"]:
            order = resp.json()["results"][0]
            for key in ("order_no", "status", "total_amount", "items", "receiver_name"):
                assert key in order, f"缺少字段: {key}"

    def test_list_seller(self, seller_auth):
        """商家视角查看"""
        resp = APIClient(seller_auth["token"]).get("/orders/?type=seller")
        assert resp.status_code == 200
        assert "results" in resp.json()

    def test_list_filter_status(self):
        """按状态筛选"""
        _create_order(self.token)

        resp = self.client.get("/orders/?status=pending")
        assert resp.status_code == 200
        for o in resp.json()["results"]:
            assert o["status"] == "pending"


# ==================== 订单详情 ====================
@allure.feature("订单模块")
@allure.story("订单详情")
@allure.severity(allure.severity_level.CRITICAL)
class TestOrderDetail:
    @pytest.fixture(autouse=True)
    def setup(self, auth):
        self.token = auth["token"]
        self.client = APIClient(self.token)

    def test_detail_own(self):
        """查看自己的订单"""
        resp = _create_order(self.token)
        order_no = resp.json()["data"]["order_no"]

        resp = self.client.get(f"/orders/{order_no}/")
        assert resp.status_code == 200
        assert_valid(OrderData, resp.json(), context="订单详情")
        assert resp.json()["status"] == "pending"
        assert len(resp.json()["items"]) == 1

    def test_detail_not_found(self):
        """不存在的订单"""
        resp = self.client.get("/orders/ORDNOTEXISTS12345/")
        assert resp.status_code == 404

    def test_detail_no_auth(self):
        """未登录"""
        resp = anon.get("/orders/ORDNOTEXISTS12345/")
        assert resp.status_code == 401


# ==================== 创建订单 ====================
@allure.feature("订单模块")
@allure.story("创建订单")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.p2
class TestOrderCreate:
    @pytest.fixture(autouse=True)
    def setup(self, auth):
        self.token = auth["token"]
        self.client = APIClient(self.token)

    @pytest.mark.smoke
    def test_create_success(self):
        """正常创建"""
        resp = _create_order(self.token)
        assert resp.status_code == 201
        assert_valid(WrappedOrderResponse, resp.json(), context="创建订单")
        data = resp.json()["data"]
        assert "order_no" in data
        assert data["status"] == "pending"
        assert len(data["items"]) == 1

    def test_create_no_auth(self):
        """未登录"""
        resp = anon.post(
            "/orders/",
            json={
                "items": [{"sku_id": SKU_ID, "quantity": 1}],
                "receiver_name": "测试",
                "receiver_phone": "13800138000",
                "receiver_address": "北京",
            },
        )
        assert resp.status_code == 401

    def test_create_empty_items(self):
        """空商品列表"""
        resp = self.client.post(
            "/orders/",
            json={
                "items": [],
                "receiver_name": "测试",
                "receiver_phone": "13800138000",
                "receiver_address": "北京",
            },
        )
        assert resp.status_code == 400
        assert resp.json()["message"] == "商品列表不能为空"

    def test_create_invalid_phone(self):
        """非法手机号"""
        resp = self.client.post(
            "/orders/",
            json={
                "items": [{"sku_id": SKU_ID, "quantity": 1}],
                "receiver_name": "测试",
                "receiver_phone": "12345",
                "receiver_address": "北京",
            },
        )
        assert resp.status_code == 400

    def test_create_insufficient_stock(self):
        """库存不足"""
        resp = self.client.post(
            "/orders/",
            json={
                "items": [{"sku_id": SKU_ID, "quantity": 999}],
                "receiver_name": "测试",
                "receiver_phone": "13800138000",
                "receiver_address": "北京",
            },
        )
        assert resp.status_code == 400
        assert "库存不足" in resp.json()["message"]


# ==================== 支付 ====================
@allure.feature("订单模块")
@allure.story("订单支付")
@allure.severity(allure.severity_level.CRITICAL)
class TestOrderPay:
    @pytest.fixture(autouse=True)
    def setup(self, auth):
        self.token = auth["token"]
        self.client = APIClient(self.token)

    def test_pay_success(self):
        """正常支付"""
        resp = _create_order(self.token)
        order_no = resp.json()["data"]["order_no"]

        resp = self.client.post(
            f"/orders/{order_no}/pay/", json={"pay_method": "wechat"}
        )
        assert resp.status_code == 200
        assert resp.json()["message"] == "支付成功"

    def test_pay_twice(self):
        """重复支付"""
        resp = _create_order(self.token)
        order_no = resp.json()["data"]["order_no"]

        self.client.post(f"/orders/{order_no}/pay/", json={"pay_method": "wechat"})

        resp = self.client.post(
            f"/orders/{order_no}/pay/", json={"pay_method": "wechat"}
        )
        assert resp.status_code == 400

    def test_pay_no_auth(self):
        """未登录"""
        resp = anon.post("/orders/ORDNOTEXISTS/pay/", json={"pay_method": "wechat"})
        assert resp.status_code == 401


# ==================== 取消订单 ====================
@allure.feature("订单模块")
@allure.story("取消订单")
@allure.severity(allure.severity_level.NORMAL)
class TestOrderCancel:
    @pytest.fixture(autouse=True)
    def setup(self, auth):
        self.token = auth["token"]
        self.client = APIClient(self.token)

    def test_cancel_success(self):
        """正常取消"""
        resp = _create_order(self.token)
        order_no = resp.json()["data"]["order_no"]

        resp = self.client.post(f"/orders/{order_no}/cancel/")
        assert resp.status_code == 200
        assert resp.json()["message"] == "订单已取消"

    def test_cancel_wrong_status(self):
        """已支付订单不能取消"""
        resp = _create_order(self.token)
        order_no = resp.json()["data"]["order_no"]

        self.client.post(f"/orders/{order_no}/pay/", json={"pay_method": "wechat"})

        resp = self.client.post(f"/orders/{order_no}/cancel/")
        assert resp.status_code == 400

    def test_cancel_no_auth(self):
        """未登录"""
        resp = anon.post("/orders/ORDNOTEXISTS/cancel/")
        assert resp.status_code == 401


# ==================== 发货（商家） ====================
@allure.feature("订单模块")
@allure.story("订单发货")
@allure.severity(allure.severity_level.CRITICAL)
class TestOrderShip:
    @pytest.fixture(autouse=True)
    def setup(self, auth, seller_auth):
        self.token = auth["token"]
        self.client = APIClient(self.token)
        self.seller_token = seller_auth["token"]
        self.seller_client = APIClient(self.seller_token)
        self.seller_id = seller_auth["user"]["id"]

    def test_ship_success(self):
        """商家发货成功"""
        sku_id = _get_seller_sku_id(self.seller_token, self.seller_id)
        resp = _create_order(self.token, sku_id=sku_id)
        assert resp.status_code == 201, f"创建订单失败: {resp.text}"
        order_no = resp.json()["data"]["order_no"]

        self.client.post(f"/orders/{order_no}/pay/", json={"pay_method": "wechat"})

        resp = self.seller_client.post(
            f"/orders/{order_no}/ship/", json={"express_no": "SF1234567890"}
        )
        assert resp.status_code == 200
        assert resp.json()["message"] == "发货成功"
        assert resp.json()["data"]["status"] == "shipped"

    def test_ship_not_owner(self):
        """商家发货他人商品 → 403"""
        resp = _create_order(self.token)
        order_no = resp.json()["data"]["order_no"]

        self.client.post(f"/orders/{order_no}/pay/", json={"pay_method": "wechat"})

        resp = self.seller_client.post(
            f"/orders/{order_no}/ship/", json={"express_no": "SF123456"}
        )
        assert resp.status_code == 403
        assert "您不是该订单商品的卖家" in resp.json()["message"]

    def test_ship_wrong_status(self):
        """pending 状态不能发货"""
        resp = _create_order(self.token)
        order_no = resp.json()["data"]["order_no"]

        resp = self.seller_client.post(
            f"/orders/{order_no}/ship/", json={"express_no": "SF123456"}
        )
        assert resp.status_code == 400
        assert "不允许发货" in resp.json()["message"]

    def test_ship_not_seller(self):
        """普通用户不能发货"""
        resp = _create_order(self.token)
        order_no = resp.json()["data"]["order_no"]

        self.client.post(f"/orders/{order_no}/pay/", json={"pay_method": "wechat"})

        resp = self.client.post(
            f"/orders/{order_no}/ship/", json={"express_no": "SF123456"}
        )
        assert resp.status_code == 403
        assert "商家" in resp.json()["message"]

    def test_ship_no_auth(self):
        """未登录"""
        resp = anon.post("/orders/ORDNOTEXISTS/ship/")
        assert resp.status_code == 401


# ==================== 确认收货 ====================
@allure.feature("订单模块")
@allure.story("确认收货")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.p2
class TestOrderComplete:
    """确认收货 (shipped → completed)"""

    @pytest.fixture(autouse=True)
    def setup(self, auth, seller_auth):
        self.token = auth["token"]
        self.client = APIClient(self.token)
        self.seller_token = seller_auth["token"]
        self.seller_client = APIClient(self.seller_token)
        self.seller_id = seller_auth["user"]["id"]

    def test_complete_success(self):
        """完整链路: 下单 → 支付 → 发货 → 确认收货"""
        sku_id = _get_seller_sku_id(self.seller_token, self.seller_id)
        resp = _create_order(self.token, sku_id=sku_id)
        assert resp.status_code == 201, f"创建订单失败: {resp.text}"
        order_no = resp.json()["data"]["order_no"]

        r = self.client.post(f"/orders/{order_no}/pay/", json={"pay_method": "wechat"})
        assert r.status_code == 200, f"支付失败: {r.text}"

        r = self.seller_client.post(
            f"/orders/{order_no}/ship/", json={"express_no": "SF1234567890"}
        )
        assert r.status_code == 200, f"发货失败: {r.text}"

        resp = self.client.post(f"/orders/{order_no}/complete/")
        assert resp.status_code == 200, f"确认收货失败: {resp.text}"

    def test_complete_wrong_status(self):
        """未发货不能确认收货"""
        resp = _create_order(self.token)
        order_no = resp.json()["data"]["order_no"]

        resp = self.client.post(f"/orders/{order_no}/complete/")
        assert resp.status_code == 400

    def test_complete_no_auth(self):
        """未登录"""
        resp = anon.post("/orders/ORDNOTEXISTS/complete/")
        assert resp.status_code == 401


# ==================== 退款 ====================
@allure.feature("订单模块")
@allure.story("申请退款")
@allure.severity(allure.severity_level.CRITICAL)
class TestOrderRefund:
    @pytest.fixture(autouse=True)
    def setup(self, auth):
        self.token = auth["token"]
        self.client = APIClient(self.token)

    def test_refund_success(self):
        """正常退款"""
        resp = _create_order(self.token)
        order_no = resp.json()["data"]["order_no"]

        self.client.post(f"/orders/{order_no}/pay/", json={"pay_method": "wechat"})

        resp = self.client.post(f"/orders/{order_no}/refund/")
        assert resp.status_code == 200
        assert resp.json()["message"] == "退款申请已提交"

    def test_refund_wrong_status(self):
        """未支付不能退款"""
        resp = _create_order(self.token)
        order_no = resp.json()["data"]["order_no"]

        resp = self.client.post(f"/orders/{order_no}/refund/")
        assert resp.status_code == 400

    def test_refund_no_auth(self):
        """未登录"""
        resp = anon.post("/orders/ORDNOTEXISTS/refund/")
        assert resp.status_code == 401


# ==================== 退款详情 ====================
@allure.feature("订单模块")
@allure.story("退款详情")
@allure.severity(allure.severity_level.NORMAL)
class TestRefundDetail:
    @pytest.fixture(autouse=True)
    def setup(self, auth):
        self.token = auth["token"]
        self.client = APIClient(self.token)

    def test_refund_detail(self):
        """查看退款详情"""
        resp = _create_order(self.token)
        order_no = resp.json()["data"]["order_no"]

        self.client.post(f"/orders/{order_no}/pay/", json={"pay_method": "wechat"})
        self.client.post(f"/orders/{order_no}/refund/")

        resp = self.client.get(f"/orders/refund/{order_no}/")
        assert resp.status_code == 200
        assert resp.json()["code"] == 200
        assert resp.json()["data"]["refund_no"] == order_no

    def test_refund_detail_wrong_status(self):
        """非退款状态查退款详情"""
        resp = _create_order(self.token)
        order_no = resp.json()["data"]["order_no"]

        resp = self.client.get(f"/orders/refund/{order_no}/")
        assert resp.status_code == 400

    def test_refund_detail_no_auth(self):
        """未登录"""
        resp = anon.get("/orders/refund/ORDNOTEXISTS/")
        assert resp.status_code == 401


# ==================== 订单并发 ====================
@allure.feature("订单模块")
@allure.story("订单并发")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.p1
class TestOrderConcurrency:
    """两人同时抢最后一个库存，验证不会超卖"""

    @pytest.fixture(autouse=True)
    def setup(self, new_user, seller_auth, shared_category, shared_brand):
        self.user_a_token = new_user["token"]
        self.seller_token = seller_auth["token"]
        self.seller_id = seller_auth["user"]["id"]
        self.seller_client = APIClient(self.seller_token)

        # 创建第二个用户
        import uuid

        username_b = f"concurrent_{uuid.uuid4().hex[:8]}"
        resp = anon.post(
            "/users/register/",
            json={
                "username": username_b,
                "password": "12345678",
                "password_confirm": "12345678",
            },
        )
        assert resp.status_code == 201
        self.user_b_token = resp.json()["data"]["tokens"]["access"]
        self.user_b_id = resp.json()["data"]["user"]["id"]

        # 卖家创建库存=1 的 SKU
        spu_resp = self.seller_client.post(
            "/goods/spus/",
            json={
                "name": f"并发测试商品_{uuid.uuid4().hex[:6]}",
                "brand": shared_brand["id"],
                "category_id": shared_category["id"],
            },
        )
        assert spu_resp.status_code == 201, f"创建 SPU 失败: {spu_resp.text}"
        spu_id = spu_resp.json()["id"]

        self.seller_client.patch(f"/goods/spus/{spu_id}/", json={"is_on_sale": True})

        sku_resp = self.seller_client.post(
            "/goods/skus/",
            json={
                "spu": spu_id,
                "name": "默认规格",
                "price": "9.90",
                "cost_price": "5.00",
                "stock": 1,
            },
        )
        assert sku_resp.status_code == 201, f"创建 SKU 失败: {sku_resp.text}"
        self.concurrent_sku_id = sku_resp.json()["id"]

        yield

        # 清理: 尝试删除临时用户 B
        _safe_delete(self.seller_token, f"/users/{self.user_b_id}/")

    def _try_create_order(self, token, results, idx):
        """在线程中尝试下单，存结果到列表"""
        try:
            resp = create_order(token, self.concurrent_sku_id)
            results[idx] = resp.status_code
        except requests.RequestException as e:
            results[idx] = str(e)

    def test_concurrent_last_stock(self):
        """两人同时抢库存=1 的商品，一个 201 一个 400"""
        results = [None, None]
        t_a = threading.Thread(
            target=self._try_create_order, args=(self.user_a_token, results, 0)
        )
        t_b = threading.Thread(
            target=self._try_create_order, args=(self.user_b_token, results, 1)
        )

        # 使用 barrier 让两个线程尽可能同时发起请求
        barrier = threading.Barrier(2, timeout=5)

        def _wrapped_try(token, results, idx):
            try:
                barrier.wait()
                self._try_create_order(token, results, idx)
            except threading.BrokenBarrierError:
                self._try_create_order(token, results, idx)

        t_a = threading.Thread(
            target=_wrapped_try, args=(self.user_a_token, results, 0)
        )
        t_b = threading.Thread(
            target=_wrapped_try, args=(self.user_b_token, results, 1)
        )
        t_a.start()
        t_b.start()
        t_a.join(timeout=15)
        t_b.join(timeout=15)

        statuses = sorted(r for r in results if isinstance(r, int))
        assert 201 in statuses, f"至少一个请求应该成功: {results}"
        assert 400 in statuses or len([s for s in statuses if s == 400]) >= 1, (
            f"应该有一个因库存不足返回 400: {results}"
        )


# ==================== 删除订单 ====================
@allure.feature("订单模块")
@allure.story("删除订单")
@allure.severity(allure.severity_level.NORMAL)
class TestOrderDelete:
    """删除订单: 仅 cancelled 和 completed 状态可删"""

    @pytest.fixture(autouse=True)
    def setup(self, auth, seller_auth):
        self.token = auth["token"]
        self.client = APIClient(self.token)
        self.seller_token = seller_auth["token"]
        self.seller_client = APIClient(self.seller_token)
        self.seller_id = seller_auth["user"]["id"]

    def test_delete_cancelled(self):
        """已取消的订单可删除"""
        resp = _create_order(self.token)
        order_no = resp.json()["data"]["order_no"]

        self.client.post(f"/orders/{order_no}/cancel/")

        resp = self.client.delete(f"/orders/{order_no}/")
        assert resp.status_code == 200
        assert resp.json()["message"] == "订单已删除"

    def test_delete_completed(self):
        """已完成的订单可删除"""
        sku_id = _get_seller_sku_id(self.seller_token, self.seller_id)
        resp = _create_order(self.token, sku_id=sku_id)
        assert resp.status_code == 201, f"创建订单失败: {resp.text}"
        order_no = resp.json()["data"]["order_no"]

        r = self.client.post(f"/orders/{order_no}/pay/", json={"pay_method": "wechat"})
        assert r.status_code == 200, f"支付失败: {r.text}"

        r = self.seller_client.post(
            f"/orders/{order_no}/ship/", json={"express_no": "SF123456"}
        )
        assert r.status_code == 200, f"发货失败: {r.text}"

        r = self.client.post(f"/orders/{order_no}/complete/")
        assert r.status_code == 200, f"确认收货失败: {r.text}"

        resp = self.client.delete(f"/orders/{order_no}/")
        assert resp.status_code == 200, f"删除失败: {resp.text}"

    def test_delete_wrong_status(self):
        """pending 状态不能删除"""
        resp = _create_order(self.token)
        order_no = resp.json()["data"]["order_no"]

        resp = self.client.delete(f"/orders/{order_no}/")
        assert resp.status_code == 400

    def test_delete_no_auth(self):
        """未登录"""
        resp = anon.delete("/orders/ORDNOTEXISTS/")
        assert resp.status_code == 401
