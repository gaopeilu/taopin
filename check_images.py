import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dianshang.settings')
import django
django.setup()

from apps.goods.models import GoodsSPU, Category

spus = list(GoodsSPU.objects.all())
print(f'Total: {len(spus)} products')

no_img = [s for s in spus if not s.main_image]
unsplash = [s for s in spus if s.main_image and 'unsplash' in (s.main_image or '')]
other = [s for s in spus if s.main_image and 'unsplash' not in (s.main_image or '') and 'placeholder' not in (s.main_image or '')]
print(f'No image: {len(no_img)}')
print(f'Unsplash: {len(unsplash)}')
print(f'Other: {len(other)}')

cats = {}
for s in spus:
    cname = s.category.name if s.category else 'none'
    cats[cname] = cats.get(cname, 0) + 1

print('\nCategories:')
for k, v in sorted(cats.items(), key=lambda x: -x[1]):
    print(f'  {k}: {v}')

print('\nSample products with categories:')
for s in spus[:30]:
    cname = s.category.name if s.category else 'none'
    img = s.main_image[:60] if s.main_image else 'NONE'
    print(f'  [{cname}] {s.name}: {img}')
