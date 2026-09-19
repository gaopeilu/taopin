"""商品模块接口自动化测试

覆盖: categories / brands / spus / skus / images

注意: goods 模块的列表接口走 DRF 分页，格式为 {count, next, previous, results}
      详情/创建/更新 直接返回对象
      tree/ 接口直接返回列表
"""

import time

import allure
import pytest
from client import APIClient, anon
from schemas import (
    BrandItem,
    CategoryListResponse,
    SKUItem,
    SKUListResponse,
    SPUItem,
    SPUListResponse,
    assert_valid,
)

_SHARED = {}


def _get_category_id():
    if "cat_id" not in _SHARED:
        resp = anon.get("/goods/categories/")
        assert resp.status_code == 200, f"获取分类列表失败: {resp.status_code}"
        _SHARED["cat_id"] = resp.json()["results"][0]["id"]
    return _SHARED["cat_id"]


def _get_brand_id():
    if "brand_id" not in _SHARED:
        resp = anon.get("/goods/brands/")
        if resp.status_code == 200 and resp.json()["results"]:
            _SHARED["brand_id"] = resp.json()["results"][0]["id"]
        else:
            _SHARED["brand_id"] = None
    return _SHARED["brand_id"]


def _create_spu_and_get_id(token, name_prefix="测试"):
    """创建 SPU 并返回 ID"""
    name = f"{name_prefix}SPU_{int(time.time() * 1000)}"
    cat_id = _get_category_id()
    client = APIClient(token)
    resp = client.post(
        "/goods/spus/",
        json={"name": name, "category": cat_id},
    )
    assert resp.status_code == 201
    assert_valid(SPUItem, resp.json(), context="创建SPU")
    time.sleep(0.5)
    results = client.get(f"/goods/spus/?search={name}").json()["results"]
    return results[0]["id"]


@allure.feature("商品模块")
@allure.story("分类查询")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.p1
class TestCategoryRead:
    """分类 读接口 — 无需登录"""

    def test_list_returns_top_level_only(self):
        """列表只返回顶级分类，每个带 children"""
        resp = anon.get("/goods/categories/")
        assert resp.status_code == 200
        data = assert_valid(CategoryListResponse, resp.json(), context="分类列表")
        results = [r.model_dump() for r in data.results]
        assert isinstance(results, list)
        assert len(results) > 0, "数据库没有任何分类"

        first = results[0]
        assert "id" in first
        assert "name" in first
        assert "level" in first
        assert "children" in first
        assert isinstance(first["children"], list)
        assert first["level"] == 1

    def test_children_have_correct_level(self):
        """子分类 level >= 父级 level"""
        resp = anon.get("/goods/categories/")
        results = resp.json()["results"]

        for parent in results:
            for child in parent.get("children", []):
                assert child["level"] >= parent["level"], (
                    f"子分类 {child['name']} level({child['level']}) < 父级({parent['level']})"
                )
                for grandchild in child.get("children", []):
                    assert grandchild["level"] >= child["level"], (
                        f"孙分类 {grandchild['name']} level 不对"
                    )

    def test_no_duplicate_ids(self):
        """树中没有重复 ID"""
        resp = anon.get("/goods/categories/")
        results = resp.json()["results"]

        ids = set()

        def collect(cats):
            for c in cats:
                assert c["id"] not in ids, f"ID {c['id']} 重复"
                ids.add(c["id"])
                collect(c.get("children", []))

        collect(results)

    def test_detail_by_id(self):
        """查单个分类详情 — 直接返回对象"""
        cat_id = anon.get("/goods/categories/").json()["results"][0]["id"]
        resp = anon.get(f"/goods/categories/{cat_id}/")
        assert resp.status_code == 200
        assert resp.json()["id"] == cat_id

    def test_detail_not_found(self):
        """不存在的分类 → 404"""
        resp = anon.get("/goods/categories/99999/")
        assert resp.status_code == 404

    def test_tree_endpoint(self):
        """tree/ 直接返回列表"""
        resp = anon.get("/goods/categories/tree/")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) > 0
        assert "id" in data[0]
        assert "children" in data[0]


@allure.feature("商品模块")
@allure.story("分类管理")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.p2
class TestCategoryWrite:
    """分类 写接口 — 需要商家 token"""

    @pytest.fixture(autouse=True)
    def setup(self, seller_auth):
        self.seller_token = seller_auth["token"]
        self.client = APIClient(self.seller_token)

    def test_create_top_level(self):
        """创建一级分类 — 返回对象"""
        name = f"测试一级_{int(time.time() * 1000)}"
        resp = self.client.post("/goods/categories/", json={"name": name})
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == name
        assert data["level"] == 1
        assert data["parent"] is None
        assert data["children"] == []

    def test_create_sub_category(self):
        """创建子分类 — level 自动+1"""
        parent_id = anon.get("/goods/categories/").json()["results"][0]["id"]
        name = f"测试子分类_{int(time.time() * 1000)}"
        resp = self.client.post(
            "/goods/categories/",
            json={"name": name, "parent": parent_id},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == name
        assert data["parent"] == parent_id
        assert data["level"] >= 1

    def test_create_no_name(self):
        """缺 name → 400"""
        resp = self.client.post("/goods/categories/", json={})
        assert resp.status_code == 400

    def test_create_no_token(self):
        """无 token → 401"""
        resp = anon.post("/goods/categories/", json={"name": "x"})
        assert resp.status_code == 401

    def test_create_not_seller(self, auth):
        """非商家 → 403"""
        client = APIClient(auth["token"])
        resp = client.post("/goods/categories/", json={"name": "x"})
        assert resp.status_code == 403

    def test_update_category(self):
        """修改分类名称"""
        create_resp = self.client.post(
            "/goods/categories/", json={"name": f"原始_{int(time.time() * 1000)}"}
        )
        cat_id = create_resp.json()["id"]

        new_name = f"新名称_{int(time.time() * 1000)}"
        resp = self.client.put(f"/goods/categories/{cat_id}/", json={"name": new_name})
        assert resp.status_code == 200
        assert resp.json()["name"] == new_name

    def test_delete_category(self):
        """删除分类 → 204 + 确认已删"""
        create_resp = self.client.post(
            "/goods/categories/", json={"name": f"待删_{int(time.time() * 1000)}"}
        )
        cat_id = create_resp.json()["id"]

        resp = self.client.delete(f"/goods/categories/{cat_id}/")
        assert resp.status_code == 204

        resp = anon.get(f"/goods/categories/{cat_id}/")
        assert resp.status_code == 404

    def test_pagination_format(self):
        """分页格式 {count, next, previous, results}"""
        resp = anon.get("/goods/categories/")
        body = resp.json()
        assert "count" in body
        assert "results" in body
        assert body["count"] >= len(body["results"])

    def test_fields_have_correct_types(self):
        """所有节点字段类型正确 — id=int, name=str, children=list"""
        resp = anon.get("/goods/categories/")
        results = resp.json()["results"]

        def check(node):
            assert isinstance(node["id"], int)
            assert isinstance(node["name"], str) and len(node["name"]) > 0
            assert isinstance(node["level"], int)
            assert isinstance(node["children"], list)
            for child in node["children"]:
                check(child)

        for item in results:
            check(item)


@allure.feature("商品模块")
@allure.story("品牌查询")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.p1
class TestBrandRead:
    """品牌 读接口 — 无需登录"""

    def test_list(self):
        """品牌列表"""
        resp = anon.get("/goods/brands/")
        assert resp.status_code == 200
        results = resp.json()["results"]
        assert isinstance(results, list)
        if len(results) > 0:
            brand = results[0]
            assert "id" in brand
            assert "name" in brand
            assert "first_letter" in brand
            assert "is_active" in brand

    def test_filter_by_letter(self):
        """按首字母筛选 — ?letter=A"""
        resp = anon.get("/goods/brands/?letter=A")
        assert resp.status_code == 200
        for brand in resp.json()["results"]:
            assert brand["first_letter"].upper() == "A"

    def test_filter_letter_empty_result(self):
        """不存在的字母 — 返回空"""
        resp = anon.get("/goods/brands/?letter=Z")
        assert resp.status_code == 200
        assert resp.json()["count"] == 0

    def test_detail(self):
        """品牌详情"""
        brands = anon.get("/goods/brands/").json()["results"]
        if brands:
            brand_id = brands[0]["id"]
            resp = anon.get(f"/goods/brands/{brand_id}/")
            assert resp.status_code == 200
            assert resp.json()["id"] == brand_id

    def test_detail_not_found(self):
        """不存在的品牌 → 404"""
        resp = anon.get("/goods/brands/99999/")
        assert resp.status_code == 404


@allure.feature("商品模块")
@allure.story("品牌管理")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.p2
class TestBrandWrite:
    """品牌 写接口 — 需要商家 token"""

    @pytest.fixture(autouse=True)
    def setup(self, seller_auth):
        self.seller_token = seller_auth["token"]
        self.client = APIClient(self.seller_token)

    def test_create(self):
        """创建品牌"""
        name = f"测试品牌_{int(time.time() * 1000)}"
        resp = self.client.post(
            "/goods/brands/", json={"name": name, "first_letter": "C"}
        )
        assert resp.status_code == 201
        assert_valid(BrandItem, resp.json(), context="创建品牌")

    def test_create_no_name(self):
        """缺 name → 400"""
        resp = self.client.post("/goods/brands/", json={})
        assert resp.status_code == 400

    def test_create_no_token(self):
        """无 token → 401"""
        resp = anon.post("/goods/brands/", json={"name": "x"})
        assert resp.status_code == 401

    def test_create_not_seller(self, auth):
        """非商家 → 403"""
        client = APIClient(auth["token"])
        resp = client.post("/goods/brands/", json={"name": "x"})
        assert resp.status_code == 403

    def test_update_brand(self):
        """修改品牌"""
        name = f"改前_{int(time.time() * 1000)}"
        brand_id = self.client.post("/goods/brands/", json={"name": name}).json()["id"]

        resp = self.client.put(
            f"/goods/brands/{brand_id}/",
            json={"name": f"改后_{int(time.time() * 1000)}"},
        )
        assert resp.status_code == 200

    def test_delete_brand(self):
        """删除品牌"""
        name = f"待删品牌_{int(time.time() * 1000)}"
        brand_id = self.client.post("/goods/brands/", json={"name": name}).json()["id"]

        resp = self.client.delete(f"/goods/brands/{brand_id}/")
        assert resp.status_code == 204


@allure.feature("商品模块")
@allure.story("SPU查询")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.p1
class TestSPURead:
    """SPU 读接口 — 无需登录"""

    @pytest.mark.smoke
    def test_list(self):
        """商品列表"""
        resp = anon.get("/goods/spus/")
        assert resp.status_code == 200
        list_data = assert_valid(SPUListResponse, resp.json(), context="SPU列表")
        results = [r.model_dump() for r in list_data.results]
        assert isinstance(results, list)
        if len(results) > 0:
            spu = results[0]
            assert "id" in spu
            assert "name" in spu
            assert "brand_name" in spu
            assert "category_name" in spu
            assert "is_on_sale" in spu

    def test_filter_on_sale(self):
        """筛选上架商品 — ?is_on_sale=true"""
        resp = anon.get("/goods/spus/?is_on_sale=true")
        assert resp.status_code == 200
        for spu in resp.json()["results"]:
            assert spu["is_on_sale"] is True

    def test_filter_off_sale(self):
        """筛选下架商品 — ?is_on_sale=false"""
        resp = anon.get("/goods/spus/?is_on_sale=false")
        assert resp.status_code == 200
        for spu in resp.json()["results"]:
            assert spu["is_on_sale"] is False

    def test_detail(self):
        """商品详情 — 包含 skus/images/brand/category 嵌套"""
        spus = anon.get("/goods/spus/").json()["results"]
        if not spus:
            pytest.skip("没有 SPU 数据")
        spu_id = spus[0]["id"]
        resp = anon.get(f"/goods/spus/{spu_id}/")
        assert resp.status_code == 200
        detail = resp.json()
        assert "brand" in detail
        assert "category" in detail
        assert "skus" in detail
        assert "images" in detail
        assert detail["brand"] is not None

    def test_detail_not_found(self):
        """不存在的商品 → 404"""
        resp = anon.get("/goods/spus/99999/")
        assert resp.status_code == 404

    def test_hot(self):
        """热销商品"""
        resp = anon.get("/goods/spus/hot/")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert isinstance(data, list)

    def test_hot_with_limit(self):
        """热销商品 — ?limit=3"""
        resp = anon.get("/goods/spus/hot/?limit=3")
        assert resp.status_code == 200
        assert len(resp.json()["data"]) <= 3

    def test_search(self):
        """搜索商品"""
        resp = anon.get("/goods/spus/search/?q=手机")
        assert resp.status_code == 200
        assert "results" in resp.json()

    def test_search_empty_keyword(self):
        """搜索无关键词 — 服务端返回 400 或分页空结果"""
        resp = anon.get("/goods/spus/search/")
        assert resp.status_code in [200, 400]

    def test_spu_skus(self):
        """商品下的 SKU 列表"""
        spus = anon.get("/goods/spus/").json()["results"]
        if not spus:
            pytest.skip("没有 SPU 数据")
        resp = anon.get(f"/goods/spus/{spus[0]['id']}/skus/")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_spu_images(self):
        """商品下的图片列表"""
        spus = anon.get("/goods/spus/").json()["results"]
        if not spus:
            pytest.skip("没有 SPU 数据")
        resp = anon.get(f"/goods/spus/{spus[0]['id']}/images/")
        assert resp.status_code == 200
        assert "data" in resp.json()


@allure.feature("商品模块")
@allure.story("SPU管理")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.p2
class TestSPUWrite:
    """SPU 写接口 — 需要商家 token"""

    @pytest.fixture(autouse=True)
    def setup(self, seller_auth):
        self.seller_token = seller_auth["token"]
        self.client = APIClient(self.seller_token)
        self.category_id = _get_category_id()
        self.brand_id = _get_brand_id()

    def test_create(self):
        """创建商品"""
        name = f"测试商品_{int(time.time() * 1000)}"
        body = {"name": name, "category": self.category_id}
        if self.brand_id:
            body["brand"] = self.brand_id
        resp = self.client.post("/goods/spus/", json=body)
        assert resp.status_code == 201
        assert_valid(SPUItem, resp.json(), context="创建SPU")

    def test_create_name_too_short(self):
        """名称 < 2 字符 → 400"""
        resp = self.client.post(
            "/goods/spus/", json={"name": "x", "category": self.category_id}
        )
        assert resp.status_code == 400

    def test_create_no_token(self):
        resp = anon.post("/goods/spus/", json={"name": "x"})
        assert resp.status_code == 401

    def test_create_not_seller(self, auth):
        client = APIClient(auth["token"])
        resp = client.post("/goods/spus/", json={"name": "x"})
        assert resp.status_code == 403

    def test_toggle_sale(self):
        """切换上下架"""
        spu_id = _create_spu_and_get_id(self.seller_token)
        resp = self.client.put(f"/goods/spus/{spu_id}/toggle_sale/")
        assert resp.status_code == 200
        assert resp.json()["data"]["is_on_sale"] is True

    def test_delete(self):
        """软删除商品"""
        spu_id = _create_spu_and_get_id(self.seller_token)
        resp = self.client.delete(f"/goods/spus/{spu_id}/")
        assert resp.status_code == 204
        resp = anon.get(f"/goods/spus/{spu_id}/")
        assert resp.status_code == 404


@allure.feature("商品模块")
@allure.story("SKU查询")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.p1
class TestSKURead:
    """SKU 读接口 — 无需登录"""

    def test_list(self):
        """SKU 列表"""
        resp = anon.get("/goods/skus/")
        assert resp.status_code == 200
        list_data = assert_valid(SKUListResponse, resp.json(), context="SKU列表")
        results = [r.model_dump() for r in list_data.results]
        assert isinstance(results, list)

    def test_filter_by_spu(self):
        """按 SPU 筛选 — ?spu=1"""
        spus = anon.get("/goods/spus/").json()["results"]
        if not spus:
            pytest.skip("没有 SPU 数据")
        resp = anon.get(f"/goods/skus/?spu={spus[0]['id']}")
        assert resp.status_code == 200

    def test_filter_in_stock(self):
        """筛选有库存 — ?in_stock=true"""
        resp = anon.get("/goods/skus/?in_stock=true")
        assert resp.status_code == 200
        for sku in resp.json()["results"]:
            assert sku["is_in_stock"] is True

    def test_detail(self):
        """SKU 详情"""
        skus = anon.get("/goods/skus/").json()["results"]
        if not skus:
            pytest.skip("没有 SKU 数据")
        resp = anon.get(f"/goods/skus/{skus[0]['id']}/")
        assert resp.status_code == 200
        assert "price" in resp.json()
        assert "stock" in resp.json()


@allure.feature("商品模块")
@allure.story("SKU管理")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.p2
class TestSKUWrite:
    """SKU 写接口 — 需要商家 token"""

    @pytest.fixture(scope="class")
    def spu(self, seller_auth):
        """类级 fixture：只创建一个 SPU"""
        return _create_spu_and_get_id(seller_auth["token"], "SKU测试")

    @pytest.fixture(autouse=True)
    def setup(self, seller_auth, spu):
        self.seller_token = seller_auth["token"]
        self.client = APIClient(self.seller_token)
        self.spu_id = spu

    def test_create(self):
        """创建 SKU"""
        name = f"测试SKU_{int(time.time() * 1000)}"
        resp = self.client.post(
            "/goods/skus/",
            json={
                "spu": self.spu_id,
                "name": name,
                "price": "99.00",
                "stock": 100,
            },
        )
        assert resp.status_code == 201
        assert_valid(SKUItem, resp.json(), context="创建SKU")

    def test_create_no_token(self):
        resp = anon.post("/goods/skus/", json={"name": "x"})
        assert resp.status_code == 401

    def test_create_not_seller(self, auth):
        client = APIClient(auth["token"])
        resp = client.post("/goods/skus/", json={"name": "x"})
        assert resp.status_code == 403

    def test_deduct_stock(self):
        """扣库存"""
        sku_id = self.client.post(
            "/goods/skus/",
            json={
                "spu": self.spu_id,
                "name": f"扣库存SKU_{int(time.time() * 1000)}",
                "price": "50.00",
                "stock": 10,
            },
        ).json()["id"]

        resp = self.client.post(
            f"/goods/skus/{sku_id}/deduct_stock/", json={"quantity": 3}
        )
        assert resp.status_code == 200
        assert resp.json()["message"] == "库存扣减成功"
        assert resp.json()["data"]["stock"] == 7

    def test_deduct_insufficient(self):
        """超库存扣减 → 400"""
        sku_id = self.client.post(
            "/goods/skus/",
            json={
                "spu": self.spu_id,
                "name": f"超库存_{int(time.time() * 1000)}",
                "price": "10.00",
                "stock": 2,
            },
        ).json()["id"]

        resp = self.client.post(
            f"/goods/skus/{sku_id}/deduct_stock/", json={"quantity": 100}
        )
        assert resp.status_code == 400

    def test_deduct_negative_quantity(self):
        """负数扣库存 → 400"""
        sku_id = self.client.post(
            "/goods/skus/",
            json={
                "spu": self.spu_id,
                "name": f"负数_{int(time.time() * 1000)}",
                "price": "10.00",
                "stock": 10,
            },
        ).json()["id"]

        resp = self.client.post(
            f"/goods/skus/{sku_id}/deduct_stock/", json={"quantity": -1}
        )
        assert resp.status_code == 400

    def test_restore_stock(self):
        """恢复库存"""
        sku_id = self.client.post(
            "/goods/skus/",
            json={
                "spu": self.spu_id,
                "name": f"恢复库存_{int(time.time() * 1000)}",
                "price": "30.00",
                "stock": 5,
            },
        ).json()["id"]

        resp = self.client.post(
            f"/goods/skus/{sku_id}/restore_stock/", json={"quantity": 5}
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["stock"] == 10

    def test_delete(self):
        """删除 SKU"""
        sku_id = self.client.post(
            "/goods/skus/",
            json={
                "spu": self.spu_id,
                "name": f"待删SKU_{int(time.time() * 1000)}",
                "price": "1.00",
                "stock": 1,
            },
        ).json()["id"]

        resp = self.client.delete(f"/goods/skus/{sku_id}/")
        assert resp.status_code == 204


@allure.feature("商品模块")
@allure.story("图片管理")
@allure.severity(allure.severity_level.NORMAL)
class TestImageWrite:
    """图片 写接口 — 需要商家 token"""

    @pytest.fixture(scope="class")
    def img_spu(self, seller_auth):
        """类级 fixture：只创建一个 SPU 用于图片测试"""
        return _create_spu_and_get_id(seller_auth["token"], "图片测试")

    @pytest.fixture(autouse=True)
    def setup(self, seller_auth, img_spu):
        self.seller_token = seller_auth["token"]
        self.client = APIClient(self.seller_token)
        self.spu_id = img_spu

    def _fake_png(self):
        from io import BytesIO

        img = BytesIO(
            b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
            b"\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\x0f"
            b"\x00\x00\x01\x01\x00\x05\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82"
        )
        img.name = "test.png"
        return img

    def test_upload_image(self):
        """上传图片 — multipart/form-data"""
        fake_img = self._fake_png()
        resp = self.client.post(
            f"/goods/spus/{self.spu_id}/upload_image/",
            files={"image": (fake_img.name, fake_img, "image/png")},
        )
        assert resp.status_code == 200
        assert resp.json()["message"] == "上传成功"

    def test_set_main(self):
        """设置主图"""
        fake_img = self._fake_png()
        upload = self.client.post(
            f"/goods/spus/{self.spu_id}/upload_image/",
            files={"image": (fake_img.name, fake_img, "image/png")},
        )
        assert upload.status_code == 200
        img_id = upload.json()["data"]["id"]

        resp = self.client.put(f"/goods/images/{img_id}/set_main/")
        assert resp.status_code == 200
        assert "成功" in resp.json()["message"]

    def test_delete_image(self):
        """删除图片"""
        fake_img = self._fake_png()
        upload = self.client.post(
            f"/goods/spus/{self.spu_id}/upload_image/",
            files={"image": (fake_img.name, fake_img, "image/png")},
        )
        img_id = upload.json()["data"]["id"]

        resp = self.client.delete(f"/goods/images/{img_id}/")
        assert resp.status_code in [200, 204]
