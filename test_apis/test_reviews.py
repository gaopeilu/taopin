"""评价模块的接口测试"""

import time

import allure
import pytest
from client import APIClient, anon

SKU_ID = 18  # 稳定的测试 SKU
SKU_ID_2 = 13  # 另一个测试 SKU，用于避免重复评价冲突


def _get_spu_id():
    """从商品列表获取一个可用的 SPU ID"""
    resp = anon.get("/goods/spus/")
    for item in resp.json()["results"]:
        return item["id"]
    pytest.skip("没有可用商品")


def _unique_order_no(prefix="TEST"):
    """生成唯一的 order_no，避免数据库重复评价校验冲突"""
    return f"{prefix}_{int(time.time() * 1000)}"


# ==================== 评价列表 ====================
@allure.feature("评价模块")
@allure.story("评价列表")
@allure.severity(allure.severity_level.NORMAL)
class TestReviewList:
    def test_list_with_spu_id(self):
        """有 spu_id 参数"""
        spu_id = _get_spu_id()
        resp = anon.get(f"/reviews/?spu_id={spu_id}")
        assert resp.status_code == 200
        assert "results" in resp.json()

    def test_list_without_spu_id(self):
        """无 spu_id 参数 → 返回空"""
        resp = anon.get("/reviews/")
        assert resp.status_code == 200
        assert len(resp.json()["results"]) == 0


# ==================== 提交评价 ====================
@allure.feature("评价模块")
@allure.story("创建评价")
@allure.severity(allure.severity_level.CRITICAL)
class TestReviewCreate:
    @pytest.fixture(autouse=True)
    def setup(self, auth):
        self.token = auth["token"]
        self.client = APIClient(self.token)

    def test_create_success(self):
        """正常提交评价"""
        spu_id = _get_spu_id()
        resp = self.client.post(
            "/reviews/create/",
            json={
                "sku_id": SKU_ID,
                "spu_id": spu_id,
                "order_no": _unique_order_no(),
                "rating": 5,
                "content": "很好用",
                "is_anonymous": False,
            },
        )
        assert resp.status_code == 201
        assert resp.json()["message"] == "评价成功"
        data = resp.json()["data"]
        assert data["rating"] == 5
        assert data["content"] == "很好用"

    def test_create_anonymous(self):
        """匿名评价"""
        spu_id = _get_spu_id()
        resp = self.client.post(
            "/reviews/create/",
            json={
                "sku_id": SKU_ID_2,
                "spu_id": spu_id,
                "order_no": _unique_order_no("ANON"),
                "rating": 4,
                "content": "还行",
                "is_anonymous": True,
            },
        )
        assert resp.status_code == 201
        assert "***" in resp.json()["data"]["username"]

    def test_create_duplicate(self):
        """重复评价 → 400"""
        spu_id = _get_spu_id()
        data = {
            "sku_id": SKU_ID,
            "spu_id": spu_id,
            "order_no": "TEST_DUP_001",
            "rating": 3,
            "content": "测试重复",
        }
        self.client.post("/reviews/create/", json=data)
        resp = self.client.post("/reviews/create/", json=data)
        assert resp.status_code == 400
        assert "已评价过" in resp.json()["message"]

    def test_create_rating_out_of_range(self):
        """评分越界"""
        spu_id = _get_spu_id()
        resp = self.client.post(
            "/reviews/create/",
            json={"sku_id": SKU_ID, "spu_id": spu_id, "rating": 6, "content": "超范围"},
        )
        assert resp.status_code == 400

    def test_create_no_auth(self):
        """未登录"""
        spu_id = _get_spu_id()
        resp = anon.post(
            "/reviews/create/",
            json={"sku_id": SKU_ID, "spu_id": spu_id, "rating": 5, "content": "测试"},
        )
        assert resp.status_code == 401


# ==================== 我的评价 ====================
@allure.feature("评价模块")
@allure.story("我的评价")
@allure.severity(allure.severity_level.NORMAL)
class TestMyReviews:
    @pytest.fixture(autouse=True)
    def setup(self, auth):
        self.token = auth["token"]
        self.client = APIClient(self.token)

    def test_mine_success(self):
        """查看我的评价"""
        resp = self.client.get("/reviews/mine/")
        assert resp.status_code == 200
        assert "results" in resp.json()

    def test_mine_no_auth(self):
        """未登录"""
        resp = anon.get("/reviews/mine/")
        assert resp.status_code == 401


# ==================== 评价点赞 ====================
@allure.feature("评价模块")
@allure.story("点赞评价")
@allure.severity(allure.severity_level.MINOR)
class TestReviewLike:
    @pytest.fixture(autouse=True)
    def setup(self, auth):
        self.token = auth["token"]
        self.client = APIClient(self.token)

    def test_like_success(self):
        """正常点赞"""
        spu_id = _get_spu_id()
        resp = self.client.post(
            "/reviews/create/",
            json={
                "sku_id": SKU_ID,
                "spu_id": spu_id,
                "order_no": _unique_order_no("LIKE"),
                "rating": 5,
                "content": "点赞测试",
            },
        )
        review_id = resp.json()["data"]["id"]

        resp = self.client.post(f"/reviews/{review_id}/like/")
        assert resp.status_code == 200
        assert resp.json()["message"] == "点赞成功"
        assert resp.json()["data"]["like_count"] >= 1

    def test_like_duplicate(self):
        """重复点赞 → 400"""
        spu_id = _get_spu_id()
        resp = self.client.post(
            "/reviews/create/",
            json={
                "sku_id": SKU_ID,
                "spu_id": spu_id,
                "order_no": _unique_order_no("DUPLIKE"),
                "rating": 5,
                "content": "重复点赞测试",
            },
        )
        review_id = resp.json()["data"]["id"]

        self.client.post(f"/reviews/{review_id}/like/")
        resp = self.client.post(f"/reviews/{review_id}/like/")
        assert resp.status_code == 400
        assert "已点赞过" in resp.json()["message"]

    def test_like_not_found(self):
        """点赞不存在的评价"""
        resp = self.client.post("/reviews/99999/like/")
        assert resp.status_code == 404

    def test_like_no_auth(self):
        """未登录"""
        resp = anon.post("/reviews/1/like/")
        assert resp.status_code == 401
