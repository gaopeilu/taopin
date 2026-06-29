<template>
  <div class="search-history-page">
    <div class="page-header">
      <h2>搜索历史</h2>
      <el-button type="danger" text @click="handleClearAll" v-if="historyList.length > 0">
        清空历史
      </el-button>
    </div>

    <div class="history-content">
      <el-empty v-if="historyList.length === 0" description="暂无搜索历史" />

      <div v-else class="history-list">
        <div
          v-for="item in historyList"
          :key="item.id"
          class="history-item"
          @click="handleSearch(item.keyword)"
        >
          <div class="history-info">
            <el-icon class="history-icon"><Clock /></el-icon>
            <span class="history-keyword">{{ item.keyword }}</span>
          </div>
          <div class="history-meta">
            <span class="history-time">{{ formatTime(item.created_at) }}</span>
            <el-button
              type="danger"
              text
              size="small"
              @click.stop="handleDelete(item.id)"
            >
              删除
            </el-button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Clock } from '@element-plus/icons-vue'
import { getSearchHistory, clearSearchHistory } from '@/api/search'
import { formatTime } from '@/utils/format'

const router = useRouter()
const historyList = ref([])

// 加载搜索历史
const loadHistory = async () => {
  try {
    const res = await getSearchHistory()
    historyList.value = res.data || []
  } catch (error) {
    console.error('加载搜索历史失败:', error)
  }
}

onMounted(loadHistory)

// 搜索
const handleSearch = (keyword) => {
  router.push({ path: '/goods', query: { q: keyword } })
}

// 删除单条历史
const handleDelete = (id) => {
  historyList.value = historyList.value.filter(item => item.id !== id)
  ElMessage.success('已删除')
}

// 清空所有历史
const handleClearAll = async () => {
  try {
    await ElMessageBox.confirm('确定清空所有搜索历史？', '提示', { type: 'warning' })
    await clearSearchHistory()
    historyList.value = []
    ElMessage.success('已清空')
  } catch (error) {
    if (error !== 'cancel') {
      console.error('清空搜索历史失败:', error)
    }
  }
}
</script>

<style scoped>
.search-history-page {
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.page-header h2 {
  font-size: 20px;
  font-weight: 600;
  color: #333;
}

.history-content {
  background: #fff;
  border-radius: 8px;
  padding: 20px;
}

.history-list {
  display: flex;
  flex-direction: column;
}

.history-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 0;
  border-bottom: 1px solid #f0f0f0;
  cursor: pointer;
}

.history-item:hover {
  background: #f5f5f5;
}

.history-item:last-child {
  border-bottom: none;
}

.history-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.history-icon {
  color: #999;
}

.history-keyword {
  font-size: 14px;
  color: #333;
}

.history-meta {
  display: flex;
  align-items: center;
  gap: 12px;
}

.history-time {
  font-size: 12px;
  color: #999;
}
</style>
