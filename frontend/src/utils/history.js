/**
 * 搜索历史管理
 * 使用localStorage存储
 */
const HISTORY_KEY = 'search_history'
const MAX_HISTORY = 10

export function getSearchHistory() {
  try { return JSON.parse(localStorage.getItem(HISTORY_KEY) || '[]') } catch { return [] }
}

export function addSearchHistory(keyword) {
  if (!keyword || !keyword.trim()) return
  let history = getSearchHistory()
  history = history.filter(h => h !== keyword.trim())
  history.unshift(keyword.trim())
  if (history.length > MAX_HISTORY) history = history.slice(0, MAX_HISTORY)
  localStorage.setItem(HISTORY_KEY, JSON.stringify(history))
}

export function clearSearchHistory() {
  localStorage.removeItem(HISTORY_KEY)
}
