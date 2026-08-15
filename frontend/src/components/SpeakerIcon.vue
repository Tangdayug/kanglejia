<template>
  <svg
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    stroke-width="2"
    stroke-linecap="round"
    stroke-linejoin="round"
    class="speaker-icon"
  >
    <!-- 音响主体 -->
    <path d="M4 9h4l6-5v16l-6-5H4V9z" />
    <!-- 一级广播线（中低音量） -->
    <path v-if="level >= 2" d="M16 8a5 5 0 0 1 0 8" />
    <!-- 二级广播线（高音量） -->
    <path v-if="level >= 3" d="M19 5a9 9 0 0 1 0 14" />
    <!-- 静音斜杠 -->
    <line v-if="level === 0" x1="2" y1="2" x2="22" y2="22" />
  </svg>
</template>

<script setup>
defineProps({
  level: {
    type: Number,
    default: 3,
    validator: (val) => [0, 1, 2, 3].includes(val)
  }
})
</script>

<style scoped>
.speaker-icon {
  width: 1em;
  height: 1em;
  display: inline-block;
  vertical-align: middle;
}
</style>
