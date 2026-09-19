"""诊断脚本 v2：排查订单完整链路"""

import time

import requests

BASE = "http://localhost:8000/api/v1"


def login(u, p):
    r = requests.post(f"{BASE}/users/login/", json={"username": u, "password": p})
    return r.json()["data"]["tokens"]["access"]


user_token = login("test111", "1234567811")
seller_token = login("seller111", "1234567811")

# 模拟 _get_seller_sku_id 逻辑（不缓存）
ts = int(time.time() * 1000)
resp = requests.get(f"{BASE}/goods/categories/")
cat_id = resp.json()["results"][0]["id"]

spu_name = f"发货测试SPU_{ts}"
resp = requests.post(
    f"{BASE}/goods/spus/",
    json={
        "name": spu_name,
        "category": cat_id,
    },
    headers={"Authorization": f"Bearer {seller_token}"},
)
print(f"[1] 创建 SPU: status={resp.status_code}")

resp = requests.get(
    f"{BASE}/goods/spus/?search={spu_name}",
    headers={"Authorization": f"Bearer {seller_token}"},
)
spu_id = resp.json()["results"][0]["id"]
print(f"[2] SPU ID: {spu_id}")

requests.patch(
    f"{BASE}/goods/spus/{spu_id}/",
    json={"is_on_sale": True},
    headers={"Authorization": f"Bearer {seller_token}"},
)
print("[3] 上架 OK")

sku_name = f"发货测试SKU_{ts}"
resp = requests.post(
    f"{BASE}/goods/skus/",
    json={
        "spu": spu_id,
        "name": sku_name,
        "price": "88.00",
        "stock": 100,
    },
    headers={"Authorization": f"Bearer {seller_token}"},
)
print(f"[4] 创建 SKU: status={resp.status_code} body={resp.text[:200]}")
sku_id = resp.json()["id"]
print(f"   SKU ID: {sku_id}")

# 创建订单
resp = requests.post(
    f"{BASE}/orders/",
    json={
        "items": [{"sku_id": sku_id, "quantity": 1}],
        "receiver_name": "测试",
        "receiver_phone": "13800138000",
        "receiver_address": "测试地址",
    },
    headers={"Authorization": f"Bearer {user_token}"},
)
print(f"[5] 创建订单: status={resp.status_code}")
if resp.status_code == 201:
    order_no = resp.json()["data"]["order_no"]
    print(f"   order_no={order_no}")

    # 支付
    r = requests.post(
        f"{BASE}/orders/{order_no}/pay/",
        json={"pay_method": "wechat"},
        headers={"Authorization": f"Bearer {user_token}"},
    )
    print(f"[6] 支付: status={r.status_code}")

    # 发货
    r = requests.post(
        f"{BASE}/orders/{order_no}/ship/",
        json={"express_no": "SF1234567890"},
        headers={"Authorization": f"Bearer {seller_token}"},
    )
    print(f"[7] 发货: status={r.status_code} body={r.text[:300]}")

    # 确认收货
    r = requests.post(
        f"{BASE}/orders/{order_no}/complete/",
        headers={"Authorization": f"Bearer {user_token}"},
    )
    print(f"[8] 确认收货: status={r.status_code} body={r.text[:300]}")

    # 删除
    r = requests.delete(
        f"{BASE}/orders/{order_no}/", headers={"Authorization": f"Bearer {user_token}"}
    )
    print(f"[9] 删除: status={r.status_code} body={r.text[:200]}")
else:
    print(f"   失败: {resp.text[:300]}")
