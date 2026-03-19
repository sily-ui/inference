<template>
  <div class="step-progress-bar">
    <div 
      v-for="(step, idx) in steps" 
      :key="idx"
      class="progress-step"
      :class="{ 
        'completed': idx < currentStep, 
        'active': idx === currentStep,
        'pending': idx > currentStep,
        'clickable': idx < currentStep
      }"
      @click="handleStepClick(idx)"
    >
      <div class="step-circle">
        <span v-if="idx < currentStep">✓</span>
        <span v-else>{{ idx + 1 }}</span>
      </div>
      <span class="step-label">{{ step }}</span>
      <div v-if="idx < steps.length - 1" class="step-line" :class="{ 'completed': idx < currentStep }"></div>
    </div>
  </div>
</template>

<script setup>
import { defineEmits } from 'vue'

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

const handleStepClick = (idx) => {
  if (idx < props.currentStep) {
    emit('step-click', idx)
  }
}
</script>

<style scoped>
.step-progress-bar {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 16px 24px;
  background: #fff;
  border-bottom: 1px solid #eaeaea;
  gap: 4px;
}

.progress-step {
  display: flex;
  align-items: center;
  gap: 8px;
  position: relative;
}

.step-circle {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  font-weight: 600;
  transition: all 0.2s ease;
}

.progress-step.pending .step-circle {
  background: #f5f5f5;
  color: #999;
  border: 2px solid #e0e0e0;
}

.progress-step.active .step-circle {
  background: #000;
  color: #fff;
  border: 2px solid #000;
}

.progress-step.completed .step-circle {
  background: #1a936f;
  color: #fff;
  border: 2px solid #1a936f;
}

.step-label {
  font-size: 13px;
  font-weight: 500;
  color: #999;
  white-space: nowrap;
}

.progress-step.active .step-label {
  color: #000;
  font-weight: 600;
}

.progress-step.completed .step-label {
  color: #1a936f;
}

.progress-step.clickable {
  cursor: pointer;
}

.progress-step.clickable:hover .step-circle {
  transform: scale(1.1);
  box-shadow: 0 2px 8px rgba(26, 147, 111, 0.3);
}

.progress-step.clickable:hover .step-label {
  text-decoration: underline;
}

.step-line {
  width: 60px;
  height: 2px;
  background: #e0e0e0;
  margin: 0 12px;
}

.step-line.completed {
  background: #1a936f;
}
</style>
