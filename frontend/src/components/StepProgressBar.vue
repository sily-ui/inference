<template>
  <div class="step-progress-bar">
    <div 
      v-for="(step, idx) in steps" 
      :key="idx"
      class="progress-step"
      :class="{ 
        'completed': step.status === 'completed', 
        'active': step.status === 'running',
        'viewing': step.status === 'viewing',
        'pending': step.status === 'pending',
        'need-rerun': step.needRerun,
        'clickable': isClickable(idx)
      }"
      @click="handleClick(idx)"
    >
      <div class="step-circle">
        <span v-if="step.status === 'completed'">✓</span>
        <span v-else-if="step.needRerun" class="rerun-icon">↻</span>
        <span v-else>{{ idx + 1 }}</span>
      </div>
      <span class="step-label">{{ step.name }}</span>
      <div v-if="idx < steps.length - 1" class="step-line" :class="{ 'completed': step.status === 'completed' || step.needRerun }"></div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  steps: {
    type: Array,
    required: true
  },
  currentStep: {
    type: Number,
    default: 0
  }
})

const emit = defineEmits(['step-click'])

const isClickable = (idx) => {
  return idx <= props.currentStep
}

const handleClick = (idx) => {
  if (isClickable(idx)) {
    emit('step-click', idx)
  }
}
</script>

<style scoped>
.step-progress-bar {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 12px 24px;
  background: #fff;
  border-bottom: 1px solid #eaeaea;
  gap: 8px;
}

.progress-step {
  display: flex;
  align-items: center;
  gap: 8px;
  position: relative;
  cursor: default;
  transition: all 0.2s ease;
}

.progress-step.clickable {
  cursor: pointer;
}

.progress-step.clickable:hover {
  opacity: 0.8;
}

.step-circle {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 600;
  background: #f5f5f5;
  color: #999;
  border: 2px solid #e0e0e0;
  transition: all 0.2s ease;
}

.progress-step.pending .step-circle {
  background: #f5f5f5;
  color: #999;
  border-color: #e0e0e0;
}

.progress-step.active .step-circle {
  background: #000;
  color: #fff;
  border-color: #000;
}

.progress-step.completed .step-circle {
  background: #1a936f;
  color: #fff;
  border-color: #1a936f;
}

.progress-step.viewing .step-circle {
  background: #007bff;
  color: #fff;
  border-color: #007bff;
}

.progress-step.need-rerun .step-circle {
  background: #ff9800;
  color: #fff;
  border-color: #ff9800;
}

.step-label {
  font-size: 12px;
  font-weight: 500;
  color: #999;
  white-space: nowrap;
}

.progress-step.active .step-label,
.progress-step.completed .step-label,
.progress-step.viewing .step-label {
  color: #333;
}

.step-line {
  width: 40px;
  height: 2px;
  background: #e0e0e0;
  margin: 0 8px;
}

.step-line.completed {
  background: #1a936f;
}

.rerun-icon {
  font-size: 14px;
}
</style>
