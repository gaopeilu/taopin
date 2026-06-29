"""
商品模块测试
覆盖：商品列表、详情、搜索、分类筛选、热销商品
"""
import pytest


@pytest.mark.django_db
class TestGoodsList:
    """商品列表测试"""

    def test_goods_list_public(self, api_client, spu, sku):
        """公开访问商品列表"""
        resp = api_client.get('/api/v1/goods/spus/')
        assert resp.status_code == 200

    def test_goods_list_filter_by_category(self, api_client, spu, sku, category):
        """按分类筛选"""
        resp = api_client.get(f'/api/v1/goods/spus/?category={category.id}')
        assert resp.status_code == 200

    def test_goods_list_filter_on_sale(self, api_client, spu, sku):
        """按上架状态筛选"""
        resp = api_client.get('/api/v1/goods/spus/?is_on_sale=true')
        assert resp.status_code == 200

    def test_goods_detail(self, api_client, spu, sku):
        """商品详情"""
        resp = api_client.get(f'/api/v1/goods/spus/{spu.id}/')
        assert resp.status_code == 200
        assert resp.data['name'] == '测试手机 Pro'
        assert len(resp.data['skus']) >= 1


@pytest.mark.django_db
class TestGoodsSearch:
    """商品搜索测试"""

    def test_search_by_name(self, api_client, spu, sku):
        """按名称搜索"""
        resp = api_client.get('/api/v1/goods/spus/search/?q=测试手机')
        assert resp.status_code == 200

    def test_search_empty_keyword(self, api_client):
        """空关键词搜索"""
        resp = api_client.get('/api/v1/goods/spus/search/?q=')
        assert resp.status_code == 200
        assert resp.data['code'] == 400


@pytest.mark.django_db
class TestHotGoods:
    """热销商品测试"""

    def test_hot_goods(self, api_client, spu, sku):
        """获取热销商品"""
        resp = api_client.get('/api/v1/goods/spus/hot/')
        assert resp.status_code == 200
        assert resp.data['code'] == 200

    def test_hot_goods_with_limit(self, api_client, spu, sku):
        """指定返回数量"""
        resp = api_client.get('/api/v1/goods/spus/hot/?limit=5')
        assert resp.status_code == 200


@pytest.mark.django_db
class TestCategory:
    """分类测试"""

    def test_category_tree(self, api_client, category):
        """获取分类树"""
        resp = api_client.get('/api/v1/goods/categories/tree/')
        assert resp.status_code == 200

    def test_category_list(self, api_client, category):
        """获取顶级分类列表"""
        resp = api_client.get('/api/v1/goods/categories/')
        assert resp.status_code == 200
