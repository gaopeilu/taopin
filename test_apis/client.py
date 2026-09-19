"""
API 客户端层

消除 262 处重复的 headers={"Authorization": f"Bearer {token}"} 样板代码。

用法:
    from client import anon, APIClient

    # 无需认证
    resp = anon.get("/goods/categories/")

    # 带认证
    client = APIClient(token)
    resp = client.post("/orders/", json={"items": [...]})

    # 临时覆盖 token
    resp = client.get("/orders/", token=other_token)

    # 临时追加 header
    resp = client.post("/payment/callback/", json={...}, extra_headers={"X-Callback-Secret": "xxx"})
"""

import requests

BASE_URL = "http://localhost:8000/api/v1"


def url(path: str) -> str:
    """拼接完整 URL: url('/goods/spus/') → http://localhost:8000/api/v1/goods/spus/"""
    return f"{BASE_URL}{path}"


class APIClient:
    """带 token 自动注入的 HTTP 客户端"""

    def __init__(self, token: str | None = None):
        self._token = token

    def _auth(self, extra: dict | None = None, token: str | None = None) -> dict:
        """构建 headers，自动注入 Authorization"""
        h = dict(extra or {})
        t = token or self._token
        if t:
            h["Authorization"] = f"Bearer {t}"
        return h

    def get(
        self,
        path: str,
        *,
        token: str | None = None,
        extra_headers: dict | None = None,
        **kwargs,
    ):
        return requests.get(
            url(path), headers=self._auth(extra_headers, token), **kwargs
        )

    def post(
        self,
        path: str,
        *,
        token: str | None = None,
        extra_headers: dict | None = None,
        **kwargs,
    ):
        return requests.post(
            url(path), headers=self._auth(extra_headers, token), **kwargs
        )

    def put(
        self,
        path: str,
        *,
        token: str | None = None,
        extra_headers: dict | None = None,
        **kwargs,
    ):
        return requests.put(
            url(path), headers=self._auth(extra_headers, token), **kwargs
        )

    def patch(
        self,
        path: str,
        *,
        token: str | None = None,
        extra_headers: dict | None = None,
        **kwargs,
    ):
        return requests.patch(
            url(path), headers=self._auth(extra_headers, token), **kwargs
        )

    def delete(
        self,
        path: str,
        *,
        token: str | None = None,
        extra_headers: dict | None = None,
        **kwargs,
    ):
        return requests.delete(
            url(path), headers=self._auth(extra_headers, token), **kwargs
        )


anon = APIClient()
