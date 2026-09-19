"""购物车模块接口自动化测试

数据存在 Redis Hash: cart:{user_id}，字段 sku_id → JSON
响应格式: {code, message, data}，同 users 模块
"""

import allure
import pytest
from client import APIClient, anon
from conftest import get_any_sku_id
from schemas import WrappedCartListResponse, assert_valid


def _get_sku_id():
    """拿一个可用的 SKU ID（有库存，SPU 未下架，用于加入购物车）"""
    sku_id = get_any_sku_id()
    assert sku_id is not None, "没有可用的 SKU，请先运行 goods 模块测试创建数据"
    return sku_id


# ==================== 读接口 ====================
@allure.feature("购物车模块")
@allure.story("查询购物车")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.p1
class TestCartRead:
    """购物车列表 — 需要登录"""

    @pytest.fixture(autouse=True)
    def setup(self, auth):
        self.client = APIClient(auth["token"])

    def test_list_empty(self, auth):
        """空购物车 → data=[]"""
        resp = self.client.get("/cart/")
        assert resp.status_code == 200
        body = resp.json()
        assert body["code"] == 200
        assert body["data"] == []

    def test_list_with_items(self, auth):
        """加入商品后列表有数据"""
        sku_id = _get_sku_id()
        self.client.post("/cart/add/", json={"sku_id": sku_id, "quantity": 1})

        resp = self.client.get("/cart/")
        assert resp.status_code == 200
        assert_valid(WrappedCartListResponse, resp.json(), context="购物车列表")
        body = resp.json()
        assert len(body["data"]) >= 1
        item = body["data"][0]
        assert "sku_id" in item
        assert "quantity" in item
        assert "is_selected" in item
        assert "goods_name" in item
        assert "price" in item
        assert "subtotal" in item

        self.client.delete("/cart/clear/")

    def test_list_fields(self, auth):
        """列表每项的必有字段"""
        sku_id = _get_sku_id()
        self.client.post("/cart/add/", json={"sku_id": sku_id, "quantity": 2})

        resp = self.client.get("/cart/")
        item = resp.json()["data"][0]
        required_fields = [
            "id",
            "sku_id",
            "spu_id",
            "quantity",
            "is_selected",
            "goods_name",
            "goods_image",
            "sku_name",
            "price",
            "stock",
            "subtotal",
        ]
        for field in required_fields:
            assert field in item, f"缺少字段: {field}"
        assert isinstance(item["quantity"], int)
        assert isinstance(item["is_selected"], bool)

        self.client.delete("/cart/clear/")

    def test_no_token(self):
        """无 token → 401"""
        resp = anon.get("/cart/")
        assert resp.status_code == 401


# ==================== 添加 ====================
@allure.feature("购物车模块")
@allure.story("添加商品")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.p2
class TestCartAdd:
    """加入购物车 — 需要登录"""

    @pytest.fixture(autouse=True)
    def setup(self, auth):
        self.client = APIClient(auth["token"])

    @pytest.mark.smoke
    def test_add(self, auth):
        """正常加入"""
        sku_id = _get_sku_id()
        resp = self.client.post("/cart/add/", json={"sku_id": sku_id, "quantity": 1})
        assert resp.status_code == 201
        body = resp.json()
        assert body["code"] == 200
        assert "已加入" in body["message"]
        assert body["data"]["sku_id"] == sku_id

        self.client.delete("/cart/clear/")

    def test_add_multiple(self, auth):
        """多次加入同一个 SKU → 数量累加"""
        sku_id = _get_sku_id()
        self.client.post("/cart/add/", json={"sku_id": sku_id, "quantity": 1})
        self.client.post("/cart/add/", json={"sku_id": sku_id, "quantity": 2})

        resp = self.client.get("/cart/")
        items = resp.json()["data"]
        assert items[0]["quantity"] == 3

        self.client.delete("/cart/clear/")

    def test_add_missing_sku_id(self, auth):
        """缺 sku_id → 400"""
        resp = self.client.post("/cart/add/", json={"quantity": 1})
        assert resp.status_code == 400

    def test_add_invalid_sku(self, auth):
        """不存在的 SKU → 404"""
        resp = self.client.post("/cart/add/", json={"sku_id": 999999, "quantity": 1})
        assert resp.status_code == 404

    def test_add_negative_quantity(self, auth):
        """负数量 → 400"""
        sku_id = _get_sku_id()
        resp = self.client.post("/cart/add/", json={"sku_id": sku_id, "quantity": -1})
        assert resp.status_code == 400

    def test_add_zero_quantity(self, auth):
        """数量为 0 → 400"""
        sku_id = _get_sku_id()
        resp = self.client.post("/cart/add/", json={"sku_id": sku_id, "quantity": 0})
        assert resp.status_code == 400

    def test_add_exceed_stock(self, auth):
        """超库存 → 400"""
        sku_id = _get_sku_id()
        resp = self.client.post(
            "/cart/add/", json={"sku_id": sku_id, "quantity": 999999}
        )
        assert resp.status_code == 400
        assert "库存不足" in resp.json()["message"]

    def test_add_no_token(self):
        """无 token → 401"""
        resp = anon.post("/cart/add/", json={"sku_id": 1, "quantity": 1})
        assert resp.status_code == 401


# ==================== 修改 ====================
@allure.feature("购物车模块")
@allure.story("更新商品")
@allure.severity(allure.severity_level.NORMAL)
class TestCartUpdate:
    """修改购物车项 — 需要登录"""

    @pytest.fixture(autouse=True)
    def setup(self, auth):
        self.client = APIClient(auth["token"])

    def test_update_quantity(self, auth):
        """修改数量"""
        sku_id = _get_sku_id()
        self.client.post("/cart/add/", json={"sku_id": sku_id, "quantity": 1})

        resp = self.client.put(f"/cart/{sku_id}/", json={"quantity": 5})
        assert resp.status_code == 200
        assert resp.json()["data"]["quantity"] == 5

        self.client.delete("/cart/clear/")

    def test_update_selected(self, auth):
        """取消选中"""
        sku_id = _get_sku_id()
        self.client.post("/cart/add/", json={"sku_id": sku_id, "quantity": 1})

        resp = self.client.put(f"/cart/{sku_id}/", json={"is_selected": False})
        assert resp.status_code == 200
        assert resp.json()["data"]["is_selected"] is False

        self.client.delete("/cart/clear/")

    def test_update_not_exist(self, auth):
        """修改不存在的项 → 404"""
        resp = self.client.put("/cart/999999/", json={"quantity": 1})
        assert resp.status_code == 404

    def test_update_no_body(self, auth):
        """空 body → 不做任何修改，返回 200"""
        sku_id = _get_sku_id()
        self.client.post("/cart/add/", json={"sku_id": sku_id, "quantity": 1})

        resp = self.client.put(f"/cart/{sku_id}/", json={})
        assert resp.status_code == 200

        self.client.delete("/cart/clear/")

    def test_update_no_token(self):
        """无 token → 401"""
        resp = anon.put("/cart/1/", json={"quantity": 1})
        assert resp.status_code == 401


# ==================== 删除 ====================
@allure.feature("购物车模块")
@allure.story("删除商品")
@allure.severity(allure.severity_level.NORMAL)
class TestCartDelete:
    """删除购物车项 — 需要登录"""

    @pytest.fixture(autouse=True)
    def setup(self, auth):
        self.client = APIClient(auth["token"])

    def test_delete_item(self, auth):
        """删除单项"""
        sku_id = _get_sku_id()
        self.client.post("/cart/add/", json={"sku_id": sku_id, "quantity": 1})

        resp = self.client.delete(f"/cart/{sku_id}/delete/")
        assert resp.status_code == 200
        assert "已删除" in resp.json()["message"]

        list_resp = self.client.get("/cart/")
        assert list_resp.json()["data"] == []

    def test_delete_not_exist(self, auth):
        """删除不存在的项 → 404"""
        resp = self.client.delete("/cart/999999/delete/")
        assert resp.status_code == 404

    def test_delete_no_token(self):
        """无 token → 401"""
        resp = anon.delete("/cart/1/delete/")
        assert resp.status_code == 401


# ==================== 清空 ====================
@allure.feature("购物车模块")
@allure.story("清空购物车")
@allure.severity(allure.severity_level.NORMAL)
class TestCartClear:
    """清空购物车 — 需要登录"""

    @pytest.fixture(autouse=True)
    def setup(self, auth):
        self.client = APIClient(auth["token"])

    def test_clear(self, auth):
        """清空后列表为空"""
        sku_id = _get_sku_id()
        self.client.post("/cart/add/", json={"sku_id": sku_id, "quantity": 1})

        resp = self.client.delete("/cart/clear/")
        assert resp.status_code == 200
        assert "清空" in resp.json()["message"]

        list_resp = self.client.get("/cart/")
        assert list_resp.json()["data"] == []

    def test_clear_empty(self, auth):
        """空购物车清空也不报错"""
        resp = self.client.delete("/cart/clear/")
        assert resp.status_code == 200

    def test_clear_no_token(self):
        """无 token → 401"""
        resp = anon.delete("/cart/clear/")
        assert resp.status_code == 401


# ==================== 全选 ====================
@allure.feature("购物车模块")
@allure.story("全选/取消")
@allure.severity(allure.severity_level.MINOR)
class TestCartSelectAll:
    """全选/取消全选 — 需要登录"""

    @pytest.fixture(autouse=True)
    def setup(self, auth):
        self.client = APIClient(auth["token"])

    def test_select_all(self, auth):
        """全选所有商品"""
        sku_id = _get_sku_id()
        self.client.post("/cart/add/", json={"sku_id": sku_id, "quantity": 1})
        self.client.put(f"/cart/{sku_id}/", json={"is_selected": False})

        resp = self.client.post("/cart/select-all/", json={"is_selected": True})
        assert resp.status_code == 200

        list_resp = self.client.get("/cart/")
        for item in list_resp.json()["data"]:
            assert item["is_selected"] is True

        self.client.delete("/cart/clear/")

    def test_unselect_all(self, auth):
        """取消全选"""
        sku_id = _get_sku_id()
        self.client.post("/cart/add/", json={"sku_id": sku_id, "quantity": 1})

        resp = self.client.post("/cart/select-all/", json={"is_selected": False})
        assert resp.status_code == 200

        list_resp = self.client.get("/cart/")
        for item in list_resp.json()["data"]:
            assert item["is_selected"] is False

        self.client.delete("/cart/clear/")

    def test_select_all_no_token(self):
        """无 token → 401"""
        resp = anon.post("/cart/select-all/", json={"is_selected": True})
        assert resp.status_code == 401
