import json
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django_redis import get_redis_connection
from .serializers import AddCartSerializer, UpdateCartSerializer
from apps.goods.models import GoodsSKU, GoodsSPU

# Redis Key设计: cart:{user_id} -> Hash, field=sku_id, value=JSON
CART_KEY_PREFIX = 'cart'


def _cart_key(user_id):
    return f'{CART_KEY_PREFIX}:{user_id}'


def _get_cart_items(user_id):
    """从Redis获取用户购物车所有项"""
    con = get_redis_connection('default')
    key = _cart_key(user_id)
    raw = con.hgetall(key)
    items = []
    for sku_id_bytes, data_bytes in raw.items():
        sku_id = int(sku_id_bytes)
        data = json.loads(data_bytes)
        items.append({'sku_id': sku_id, **data})
    return items


def _build_cart_item(sku_id, data):
    """根据Redis数据构建购物车项的完整信息"""
    try:
        sku = GoodsSKU.objects.get(id=sku_id)
        spu = sku.spu
        quantity = data.get('quantity', 1)
        return {
            'id': sku_id,  # 用sku_id作为唯一标识
            'sku_id': sku_id,
            'spu_id': data.get('spu_id', sku.spu_id),
            'quantity': quantity,
            'is_selected': data.get('is_selected', True),
            'goods_name': spu.name,
            'goods_image': spu.main_image or '',
            'sku_name': sku.name,
            'price': str(sku.price),
            'stock': sku.stock,
            'subtotal': str(sku.price * quantity),
        }
    except (GoodsSKU.DoesNotExist, GoodsSPU.DoesNotExist):
        return None


class CartListView(APIView):
    """购物车列表"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        raw_items = _get_cart_items(request.user.id)
        if not raw_items:
            return Response({'code': 200, 'data': []})

        # [性能优化] 批量查询SKU和SPU，避免N+1
        sku_ids = [item['sku_id'] for item in raw_items]
        sku_map = {
            sku.id: sku
            for sku in GoodsSKU.objects.filter(id__in=sku_ids).select_related('spu')
        }

        result = []
        for item in raw_items:
            sku = sku_map.get(item['sku_id'])
            if not sku:
                continue
            quantity = item.get('quantity', 1)
            result.append({
                'id': item['sku_id'],
                'sku_id': item['sku_id'],
                'spu_id': item.get('spu_id', sku.spu_id),
                'quantity': quantity,
                'is_selected': item.get('is_selected', True),
                'goods_name': sku.spu.name,
                'goods_image': sku.spu.main_image or '',
                'sku_name': sku.name,
                'price': str(sku.price),
                'stock': sku.stock,
                'subtotal': str(sku.price * quantity),
            })
        return Response({'code': 200, 'data': result})


class CartAddView(APIView):
    """添加商品到购物车"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        ser = AddCartSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        sku_id = ser.validated_data['sku_id']
        quantity = ser.validated_data['quantity']

        # 验证SKU存在
        try:
            sku = GoodsSKU.objects.get(id=sku_id, is_active=True)
        except GoodsSKU.DoesNotExist:
            return Response({'code': 404, 'message': '商品不存在或已下架'}, status=404)

        # 检查库存
        if sku.stock < quantity:
            return Response({'code': 400, 'message': f'库存不足，剩余{sku.stock}件'}, status=400)

        con = get_redis_connection('default')
        key = _cart_key(request.user.id)
        existing = con.hget(key, str(sku_id))

        if existing:
            data = json.loads(existing)
            data['quantity'] = min(data['quantity'] + quantity, sku.stock)
        else:
            data = {'quantity': quantity, 'spu_id': sku.spu_id, 'is_selected': True}

        con.hset(key, str(sku_id), json.dumps(data))

        built = _build_cart_item(sku_id, data)
        return Response({'code': 200, 'message': '已加入购物车', 'data': built}, status=201)


class CartUpdateView(APIView):
    """更新购物车（数量/选中状态）"""
    permission_classes = [IsAuthenticated]

    def put(self, request, pk):
        # pk 即 sku_id
        con = get_redis_connection('default')
        key = _cart_key(request.user.id)
        existing = con.hget(key, str(pk))
        if not existing:
            return Response({'code': 404, 'message': '购物车项不存在'}, status=404)

        ser = UpdateCartSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        data = json.loads(existing)

        if 'quantity' in ser.validated_data:
            new_qty = ser.validated_data['quantity']
            try:
                sku = GoodsSKU.objects.get(id=pk, is_active=True)
                if new_qty > sku.stock:
                    return Response({'code': 400, 'message': f'库存不足，剩余{sku.stock}件'}, status=400)
            except GoodsSKU.DoesNotExist:
                pass
            data['quantity'] = new_qty
        if 'is_selected' in ser.validated_data:
            data['is_selected'] = ser.validated_data['is_selected']

        con.hset(key, str(pk), json.dumps(data))
        built = _build_cart_item(pk, data)
        return Response({'code': 200, 'message': '更新成功', 'data': built})


class CartDeleteView(APIView):
    """删除购物车项"""
    permission_classes = [IsAuthenticated]

    def delete(self, request, pk):
        # pk 即 sku_id
        con = get_redis_connection('default')
        key = _cart_key(request.user.id)
        if not con.hexists(key, str(pk)):
            return Response({'code': 404, 'message': '购物车项不存在'}, status=404)
        con.hdel(key, str(pk))
        return Response({'code': 200, 'message': '已删除'})


class CartClearView(APIView):
    """清空购物车"""
    permission_classes = [IsAuthenticated]

    def delete(self, request):
        con = get_redis_connection('default')
        con.delete(_cart_key(request.user.id))
        return Response({'code': 200, 'message': '购物车已清空'})


class CartSelectAllView(APIView):
    """全选/取消全选"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        is_selected = request.data.get('is_selected', True)
        con = get_redis_connection('default')
        key = _cart_key(request.user.id)
        raw = con.hgetall(key)
        for sku_id_bytes, data_bytes in raw.items():
            data = json.loads(data_bytes)
            data['is_selected'] = is_selected
            con.hset(key, sku_id_bytes, json.dumps(data))
        return Response({'code': 200, 'message': '操作成功'})
