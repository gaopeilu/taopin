/**
 * 购物车状态管理 (Pinia)
 * 后端无购物车接口，使用localStorage本地存储
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

const CART_KEY = 'cart_items'

export const useCartStore = defineStore('cart', () => {
  /* ========== 状态 ========== */
  const items = ref(JSON.parse(localStorage.getItem(CART_KEY) || '[]'))

  /* ========== 计算属性 ========== */
  const totalCount = computed(() => items.value.reduce((sum, item) => sum + item.quantity, 0))
  const totalPrice = computed(() => items.value.reduce((sum, item) => sum + item.price * item.quantity, 0).toFixed(2))

  /* ========== 方法 ========== */

  /** 持久化到localStorage */
  function save() {
    localStorage.setItem(CART_KEY, JSON.stringify(items.value))
  }

  /**
   * 添加商品到购物车
   * @param {Object} product - { skuId, spuId, name, price, image, specText, quantity }
   */
  function addItem(product) {
    const existing = items.value.find(i => i.skuId === product.skuId)
    if (existing) {
      existing.quantity += (product.quantity || 1)
    } else {
      items.value.push({ ...product, quantity: product.quantity || 1 })
    }
    save()
  }

  /** 更新商品数量 */
  function updateQuantity(skuId, quantity) {
    const item = items.value.find(i => i.skuId === skuId)
    if (item) {
      item.quantity = Math.max(1, quantity)
      save()
    }
  }

  /** 移除单个商品 */
  function removeItem(skuId) {
    items.value = items.value.filter(i => i.skuId !== skuId)
    save()
  }

  /** 清空购物车 */
  function clear() {
    items.value = []
    save()
  }

  return { items, totalCount, totalPrice, addItem, updateQuantity, removeItem, clear }
})
