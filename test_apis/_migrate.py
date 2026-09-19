"""迁移剩余文件到 APIClient - 精确替换版本"""

import re
from pathlib import Path

FILES = [
    "test_coupons.py",
    "test_users.py",
    "test_goods.py",
    "test_cart.py",
]

BASE = Path(__file__).parent

for fname in FILES:
    fpath = BASE / fname
    text = fpath.read_text(encoding="utf-8")

    # ── 1. 替换 import ──
    # 移除 BASE_URL 从 conftest import
    text = re.sub(r"from conftest import BASE_URL,?\s*", "", text)
    text = re.sub(
        r"from conftest import (.+?), BASE_URL", r"from conftest import \1", text
    )
    text = re.sub(r"BASE_URL\s*=\s*.+\n", "", text)

    # 在最后一个 import 后插入 client import
    if "from client import APIClient, anon" not in text:
        lines = text.split("\n")
        last_import = 0
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped and stripped.startswith(("import ", "from ")):
                last_import = i
        lines.insert(last_import + 1, "")
        lines.insert(last_import + 1, "from client import APIClient, anon")
        text = "\n".join(lines)

    # ── 2. f-string 中替换 BASE_URL ──
    text = re.sub(r'f"\{BASE_URL\}/', 'f"/', text)

    # ── 3. auth headers ──
    # requests.xxx(url, ..., headers={"Authorization": f"Bearer {self.token}"})
    # → 保留 URL/JSON，删除 headers 行

    # 模式：后面单独一行的 headers
    auth_header_lines = [
        '            headers={"Authorization": f"Bearer {self.token}"},',
        '                headers={"Authorization": f"Bearer {self.token}"},',
        '            headers={"Authorization": f"Bearer {self.token}"}',
        '                headers={"Authorization": f"Bearer {self.token}"}',
        '        headers={"Authorization": f"Bearer {self.token}"},',
        '        headers={"Authorization": f"Bearer {self.token}"}',
    ]
    for pat in auth_header_lines:
        text = text.replace(pat + "\n", "")
        text = text.replace(pat, "")

    # ── 4. 替换 requests → self.client (有 auth 的调用) ──
    # 这步留着手工做，因为有太多了变体

    # ── 5. 替换 requests.get(f"{BASE_URL}/... → anon.get("/... ──
    # 这步也需要人工判断哪些需要 auth 哪些不需要

    fpath.write_text(text, encoding="utf-8")
    remaining = len(re.findall(r"BASE_URL", text))
    auth_remaining = len(re.findall(r"Authorization", text))
    print(f"{fname}: BASE_URL={remaining} auth_refs={auth_remaining}")

print("\n=== 手工步骤 ===")
print("python _migrate.py")
