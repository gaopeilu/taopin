"""
购物车模块测试
覆盖：添加、列表、更新、删除、清空、全选
"""
import pytest


@pytest.mark.django_db
class TestCartAdd:
    """添加购物车测试"""

    def test_add_to_cart(self, auth_client, sku):
        """添加商品到购物车"""
        resp = auth_client.post('/api/v1/cart/add/', {
            'sku_id': sku.id,
            'quantity': 2
        })
        assert resp.status_code == 201
        assert resp.data['code'] == 200

    def test_add_nonexistent_sku(self, auth_client):
        """添加不存在的SKU"""
        resp = auth_client.post('/api/v1/cart/add/', {
            'sku_id': 99999,
            'quantity': 1
        })
        assert resp.status_code == 404

    def test_add_exceed_stock(self, auth_client, sku):
        """添加数量超过库存"""
        resp = auth_client.post('/api/v1/cart/add/', {
            'sku_id': sku.id,
            'quantity': 999
        })
        assert resp.status_code == 400

    def test_add_same_sku_twice(self, auth_client, sku):
        """重复添加同一SKU会累加数量"""
        auth_client.post('/api/v1/cart/add/', {'sku_id': sku.id, 'quantity': 2})
        resp = auth_client.post('/api/v1/cart/add/', {'sku_id': sku.id, 'quantity': 3})
        assert resp.status_code == 201


@pytest.mark.django_db
class TestCartList:
    """购物车列表测试"""

    def test_cart_list(self, auth_client, sku):
        """获取购物车列表"""
        auth_client.post('/api/v1/cart/add/', {'sku_id': sku.id, 'quantity': 1})
        resp = auth_client.get('/api/v1/cart/')
        assert resp.status_code == 200
        assert len(resp.data['data']) >= 1

    def test_cart_list_unauthenticated(self, api_client):
        """未登录获取购物车"""
        resp = api_client.get('/api/v1/cart/')
        assert resp.status_code == 401


@pytest.mark.django_db
class TestCartUpdate:
    """更新购物车测试"""

    def test_update_quantity(self, auth_client, sku):
        """更新数量"""
        auth_client.post('/api/v1/cart/add/', {'sku_id': sku.id, 'quantity': 1})
        resp = auth_client.put(f'/api/v1/cart/{sku.id}/', {'quantity': 5})
        assert resp.status_code == 200

    def test_update_selected(self, auth_client, sku):
        """更新选中状态"""
        auth_client.post('/api/v1/cart/add/', {'sku_id': sku.id, 'quantity': 1})
        resp = auth_client.put(f'/api/v1/cart/{sku.id}/', {'is_selected': False})
        assert resp.status_code == 200


@pytest.mark.django_db
class TestCartDelete:
    """删除购物车测试"""

    def test_delete_cart_item(self, auth_client, sku):
        """删除购物车项"""
        auth_client.post('/api/v1/cart/add/', {'sku_id': sku.id, 'quantity': 1})
        resp = auth_client.delete(f'/api/v1/cart/{sku.id}/delete/')
        assert resp.status_code == 200

    def test_delete_nonexistent_item(self, auth_client):
        """删除不存在的购物车项"""
        resp = auth_client.delete('/api/v1/cart/99999/delete/')
        assert resp.status_code == 404


@pytest.mark.django_db
class TestCartClear:
    """清空购物车测试"""

    def test_clear_cart(self, auth_client, sku):
        """清空购物车"""
        auth_client.post('/api/v1/cart/add/', {'sku_id': sku.id, 'quantity': 1})
        resp = auth_client.delete('/api/v1/cart/clear/')
        assert resp.status_code == 200


@pytest.mark.django_db
class TestCartSelectAll:
    """全选测试"""

    def test_select_all(self, auth_client, sku):
        """全选"""
        auth_client.post('/api/v1/cart/add/', {'sku_id': sku.id, 'quantity': 1})
        resp = auth_client.post('/api/v1/cart/select-all/', {'is_selected': True})
        assert resp.status_code == 200
