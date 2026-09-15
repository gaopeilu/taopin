"""购物车模块接口自动化测试

数据存在 Redis Hash: cart:{user_id}，字段 sku_id → JSON
响应格式: {code, message, data}，同 users 模块
"""
import time
import pytest
import requests

BASE_URL = "http://localhost:8000/api/v1"


def _get_sku_id():
    """拿一个可用的 SKU ID（用于加入购物车）"""
    resp = requests.get(f"{BASE_URL}/goods/skus/")
    assert resp.status_code == 200
    results = resp.json()["results"]
    assert len(results) > 0, "没有可用的 SKU，请先运行 goods 模块测试创建数据"
    return results[0]["id"]


# ==================== 读接口 ====================
class TestCartRead:
    """购物车列表 — 需要登录"""

    def test_list_empty(self, auth):
        """空购物车 → data=[]"""
        resp = requests.get(f"{BASE_URL}/cart/", headers={
            "Authorization": f"Bearer {auth['token']}"
        })
        assert resp.status_code == 200
        body = resp.json()
        assert body["code"] == 200
        assert body["data"] == []

    def test_list_with_items(self, auth):
        """加入商品后列表有数据"""
        sku_id = _get_sku_id()
        requests.post(f"{BASE_URL}/cart/add/", json={
            "sku_id": sku_id, "quantity": 1
        }, headers={"Authorization": f"Bearer {auth['token']}"})

        resp = requests.get(f"{BASE_URL}/cart/", headers={
            "Authorization": f"Bearer {auth['token']}"
        })
        assert resp.status_code == 200
        body = resp.json()
        assert len(body["data"]) >= 1
        item = body["data"][0]
        assert "sku_id" in item
        assert "quantity" in item
        assert "is_selected" in item
        assert "goods_name" in item
        assert "price" in item
        assert "subtotal" in item

        requests.delete(f"{BASE_URL}/cart/clear/", headers={
            "Authorization": f"Bearer {auth['token']}"
        })

    def test_list_fields(self, auth):
        """列表每项的必有字段"""
        sku_id = _get_sku_id()
        requests.post(f"{BASE_URL}/cart/add/", json={
            "sku_id": sku_id, "quantity": 2
        }, headers={"Authorization": f"Bearer {auth['token']}"})

        resp = requests.get(f"{BASE_URL}/cart/", headers={
            "Authorization": f"Bearer {auth['token']}"
        })
        item = resp.json()["data"][0]
        required_fields = [
            "id", "sku_id", "spu_id", "quantity", "is_selected",
            "goods_name", "goods_image", "sku_name", "price", "stock", "subtotal"
        ]
        for field in required_fields:
            assert field in item, f"缺少字段: {field}"
        assert isinstance(item["quantity"], int)
        assert isinstance(item["is_selected"], bool)

        requests.delete(f"{BASE_URL}/cart/clear/", headers={
            "Authorization": f"Bearer {auth['token']}"
        })

    def test_no_token(self):
        """无 token → 401"""
        resp = requests.get(f"{BASE_URL}/cart/")
        assert resp.status_code == 401


# ==================== 添加 ====================
class TestCartAdd:
    """加入购物车 — 需要登录"""

    def test_add(self, auth):
        """正常加入"""
        sku_id = _get_sku_id()
        resp = requests.post(f"{BASE_URL}/cart/add/", json={
            "sku_id": sku_id, "quantity": 1
        }, headers={"Authorization": f"Bearer {auth['token']}"})
        assert resp.status_code == 201
        body = resp.json()
        assert body["code"] == 200
        assert "已加入" in body["message"]
        assert body["data"]["sku_id"] == sku_id

        requests.delete(f"{BASE_URL}/cart/clear/", headers={
            "Authorization": f"Bearer {auth['token']}"
        })

    def test_add_multiple(self, auth):
        """多次加入同一个 SKU → 数量累加"""
        sku_id = _get_sku_id()
        requests.post(f"{BASE_URL}/cart/add/", json={
            "sku_id": sku_id, "quantity": 1
        }, headers={"Authorization": f"Bearer {auth['token']}"})
        requests.post(f"{BASE_URL}/cart/add/", json={
            "sku_id": sku_id, "quantity": 2
        }, headers={"Authorization": f"Bearer {auth['token']}"})

        resp = requests.get(f"{BASE_URL}/cart/", headers={
            "Authorization": f"Bearer {auth['token']}"
        })
        items = resp.json()["data"]
        assert items[0]["quantity"] == 3

        requests.delete(f"{BASE_URL}/cart/clear/", headers={
            "Authorization": f"Bearer {auth['token']}"
        })

    def test_add_missing_sku_id(self, auth):
        """缺 sku_id → 400"""
        resp = requests.post(f"{BASE_URL}/cart/add/", json={
            "quantity": 1
        }, headers={"Authorization": f"Bearer {auth['token']}"})
        assert resp.status_code == 400

    def test_add_invalid_sku(self, auth):
        """不存在的 SKU → 404"""
        resp = requests.post(f"{BASE_URL}/cart/add/", json={
            "sku_id": 999999, "quantity": 1
        }, headers={"Authorization": f"Bearer {auth['token']}"})
        assert resp.status_code == 404

    def test_add_negative_quantity(self, auth):
        """负数量 → 400"""
        sku_id = _get_sku_id()
        resp = requests.post(f"{BASE_URL}/cart/add/", json={
            "sku_id": sku_id, "quantity": -1
        }, headers={"Authorization": f"Bearer {auth['token']}"})
        assert resp.status_code == 400

    def test_add_zero_quantity(self, auth):
        """数量为 0 → 400"""
        sku_id = _get_sku_id()
        resp = requests.post(f"{BASE_URL}/cart/add/", json={
            "sku_id": sku_id, "quantity": 0
        }, headers={"Authorization": f"Bearer {auth['token']}"})
        assert resp.status_code == 400

    def test_add_exceed_stock(self, auth):
        """超库存 → 400"""
        sku_id = _get_sku_id()
        resp = requests.post(f"{BASE_URL}/cart/add/", json={
            "sku_id": sku_id, "quantity": 999999
        }, headers={"Authorization": f"Bearer {auth['token']}"})
        assert resp.status_code == 400
        assert "库存不足" in resp.json()["message"]

    def test_add_no_token(self):
        """无 token → 401"""
        resp = requests.post(f"{BASE_URL}/cart/add/", json={
            "sku_id": 1, "quantity": 1
        })
        assert resp.status_code == 401


# ==================== 修改 ====================
class TestCartUpdate:
    """修改购物车项 — 需要登录"""

    def test_update_quantity(self, auth):
        """修改数量"""
        sku_id = _get_sku_id()
        requests.post(f"{BASE_URL}/cart/add/", json={
            "sku_id": sku_id, "quantity": 1
        }, headers={"Authorization": f"Bearer {auth['token']}"})

        resp = requests.put(f"{BASE_URL}/cart/{sku_id}/", json={
            "quantity": 5
        }, headers={"Authorization": f"Bearer {auth['token']}"})
        assert resp.status_code == 200
        assert resp.json()["data"]["quantity"] == 5

        requests.delete(f"{BASE_URL}/cart/clear/", headers={
            "Authorization": f"Bearer {auth['token']}"
        })

    def test_update_selected(self, auth):
        """取消选中"""
        sku_id = _get_sku_id()
        requests.post(f"{BASE_URL}/cart/add/", json={
            "sku_id": sku_id, "quantity": 1
        }, headers={"Authorization": f"Bearer {auth['token']}"})

        resp = requests.put(f"{BASE_URL}/cart/{sku_id}/", json={
            "is_selected": False
        }, headers={"Authorization": f"Bearer {auth['token']}"})
        assert resp.status_code == 200
        assert resp.json()["data"]["is_selected"] is False

        requests.delete(f"{BASE_URL}/cart/clear/", headers={
            "Authorization": f"Bearer {auth['token']}"
        })

    def test_update_not_exist(self, auth):
        """修改不存在的项 → 404"""
        resp = requests.put(f"{BASE_URL}/cart/999999/", json={
            "quantity": 1
        }, headers={"Authorization": f"Bearer {auth['token']}"})
        assert resp.status_code == 404

    def test_update_no_body(self, auth):
        """空 body → 不做任何修改，返回 200"""
        sku_id = _get_sku_id()
        requests.post(f"{BASE_URL}/cart/add/", json={
            "sku_id": sku_id, "quantity": 1
        }, headers={"Authorization": f"Bearer {auth['token']}"})

        resp = requests.put(f"{BASE_URL}/cart/{sku_id}/", json={}, headers={
            "Authorization": f"Bearer {auth['token']}"
        })
        assert resp.status_code == 200

        requests.delete(f"{BASE_URL}/cart/clear/", headers={
            "Authorization": f"Bearer {auth['token']}"
        })

    def test_update_no_token(self):
        """无 token → 401"""
        resp = requests.put(f"{BASE_URL}/cart/1/", json={"quantity": 1})
        assert resp.status_code == 401


# ==================== 删除 ====================
class TestCartDelete:
    """删除购物车项 — 需要登录"""

    def test_delete_item(self, auth):
        """删除单项"""
        sku_id = _get_sku_id()
        requests.post(f"{BASE_URL}/cart/add/", json={
            "sku_id": sku_id, "quantity": 1
        }, headers={"Authorization": f"Bearer {auth['token']}"})

        resp = requests.delete(f"{BASE_URL}/cart/{sku_id}/delete/", headers={
            "Authorization": f"Bearer {auth['token']}"
        })
        assert resp.status_code == 200
        assert "已删除" in resp.json()["message"]

        list_resp = requests.get(f"{BASE_URL}/cart/", headers={
            "Authorization": f"Bearer {auth['token']}"
        })
        assert list_resp.json()["data"] == []

    def test_delete_not_exist(self, auth):
        """删除不存在的项 → 404"""
        resp = requests.delete(f"{BASE_URL}/cart/999999/delete/", headers={
            "Authorization": f"Bearer {auth['token']}"
        })
        assert resp.status_code == 404

    def test_delete_no_token(self):
        """无 token → 401"""
        resp = requests.delete(f"{BASE_URL}/cart/1/delete/")
        assert resp.status_code == 401


# ==================== 清空 ====================
class TestCartClear:
    """清空购物车 — 需要登录"""

    def test_clear(self, auth):
        """清空后列表为空"""
        sku_id = _get_sku_id()
        requests.post(f"{BASE_URL}/cart/add/", json={
            "sku_id": sku_id, "quantity": 1
        }, headers={"Authorization": f"Bearer {auth['token']}"})

        resp = requests.delete(f"{BASE_URL}/cart/clear/", headers={
            "Authorization": f"Bearer {auth['token']}"
        })
        assert resp.status_code == 200
        assert "清空" in resp.json()["message"]

        list_resp = requests.get(f"{BASE_URL}/cart/", headers={
            "Authorization": f"Bearer {auth['token']}"
        })
        assert list_resp.json()["data"] == []

    def test_clear_empty(self, auth):
        """空购物车清空也不报错"""
        resp = requests.delete(f"{BASE_URL}/cart/clear/", headers={
            "Authorization": f"Bearer {auth['token']}"
        })
        assert resp.status_code == 200

    def test_clear_no_token(self):
        """无 token → 401"""
        resp = requests.delete(f"{BASE_URL}/cart/clear/")
        assert resp.status_code == 401


# ==================== 全选 ====================
class TestCartSelectAll:
    """全选/取消全选 — 需要登录"""

    def test_select_all(self, auth):
        """全选所有商品"""
        sku_id = _get_sku_id()
        requests.post(f"{BASE_URL}/cart/add/", json={
            "sku_id": sku_id, "quantity": 1
        }, headers={"Authorization": f"Bearer {auth['token']}"})
        requests.put(f"{BASE_URL}/cart/{sku_id}/", json={
            "is_selected": False
        }, headers={"Authorization": f"Bearer {auth['token']}"})

        resp = requests.post(f"{BASE_URL}/cart/select-all/", json={
            "is_selected": True
        }, headers={"Authorization": f"Bearer {auth['token']}"})
        assert resp.status_code == 200

        list_resp = requests.get(f"{BASE_URL}/cart/", headers={
            "Authorization": f"Bearer {auth['token']}"
        })
        for item in list_resp.json()["data"]:
            assert item["is_selected"] is True

        requests.delete(f"{BASE_URL}/cart/clear/", headers={
            "Authorization": f"Bearer {auth['token']}"
        })

    def test_unselect_all(self, auth):
        """取消全选"""
        sku_id = _get_sku_id()
        requests.post(f"{BASE_URL}/cart/add/", json={
            "sku_id": sku_id, "quantity": 1
        }, headers={"Authorization": f"Bearer {auth['token']}"})

        resp = requests.post(f"{BASE_URL}/cart/select-all/", json={
            "is_selected": False
        }, headers={"Authorization": f"Bearer {auth['token']}"})
        assert resp.status_code == 200

        list_resp = requests.get(f"{BASE_URL}/cart/", headers={
            "Authorization": f"Bearer {auth['token']}"
        })
        for item in list_resp.json()["data"]:
            assert item["is_selected"] is False

        requests.delete(f"{BASE_URL}/cart/clear/", headers={
            "Authorization": f"Bearer {auth['token']}"
        })

    def test_select_all_no_token(self):
        """无 token → 401"""
        resp = requests.post(f"{BASE_URL}/cart/select-all/", json={
            "is_selected": True
        })
        assert resp.status_code == 401