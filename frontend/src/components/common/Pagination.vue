<template>
  <!-- 通用分页组件 -->
  <div class="pagination-wrap" v-if="total > 0">
    <el-pagination background layout="prev, pager, next" :total="total" :page-size="pageSize"
      :current-page="currentPage" @current-change="$emit('page-change', $event)" />
  </div>
</template>

<script setup>
defineProps({
  total: { type: Number, default: 0 },
  pageSize: { type: Number, default: 20 },
  currentPage: { type: Number, default: 1 }
})
defineEmits(['page-change'])
</script>

<style scoped>
.pagination-wrap { display: flex; justify-content: center; padding: 20px 0; }
</style>
