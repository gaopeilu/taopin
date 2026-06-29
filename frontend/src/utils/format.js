/**
 * 通用格式化工具函数
 */

/**
 * 格式化时间为友好显示
 * @param {string|Date} time - 时间字符串或Date对象
 * @returns {string} 格式化后的时间
 */
export function formatTime(time) {
  if (!time) return ''
  const date = new Date(time)
  const now = new Date()
  const diff = (now - date) / 1000 // 秒

  if (diff < 60) return '刚刚'
  if (diff < 3600) return `${Math.floor(diff / 60)}分钟前`
  if (diff < 86400) return `${Math.floor(diff / 3600)}小时前`
  if (diff < 2592000) return `${Math.floor(diff / 86400)}天前`

  const y = date.getFullYear()
  const m = String(date.getMonth() + 1).padStart(2, '0')
  const d = String(date.getDate()).padStart(2, '0')
  return `${y}-${m}-${d}`
}

/**
 * 格式化日期为 YYYY-MM-DD
 * @param {string|Date} date
 * @returns {string}
 */
export function fmtDate(date) {
  if (!date) return ''
  const d = new Date(date)
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${y}-${m}-${day}`
}

/**
 * 格式化日期时间为 YYYY-MM-DD HH:mm
 * @param {string|Date} date
 * @returns {string}
 */
export function fmtDateTime(date) {
  if (!date) return ''
  const d = new Date(date)
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  const h = String(d.getHours()).padStart(2, '0')
  const min = String(d.getMinutes()).padStart(2, '0')
  return `${y}-${m}-${day} ${h}:${min}`
}

/**
 * 订单状态映射
 */
export const STATUS_MAP = {
  pending: '待付款',
  paid: '待发货',
  shipped: '已发货',
  completed: '已完成',
  cancelled: '已取消',
  refund: '退款中'
}

/**
 * 获取订单状态文本
 * @param {string} status
 * @returns {string}
 */
export function statusText(status) {
  return STATUS_MAP[status] || status
}

/**
 * 格式化金额（保留2位小数）
 * @param {number|string} amount
 * @returns {string}
 */
export function fmtAmount(amount) {
  return Number(amount || 0).toFixed(2)
}

/**
 * 格式化销量数字
 * @param {number} n
 * @returns {string}
 */
export function fmtSales(n) {
  if (!n) return '0'
  if (n >= 10000) return (n / 10000).toFixed(1) + '万'
  if (n >= 1000) return (n / 1000).toFixed(1) + 'k'
  return String(n)
}
