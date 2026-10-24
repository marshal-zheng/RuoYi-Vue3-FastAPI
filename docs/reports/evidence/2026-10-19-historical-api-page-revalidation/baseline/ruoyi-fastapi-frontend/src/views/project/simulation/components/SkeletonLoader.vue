<template>
  <div class="skeleton-loader">
    <div v-if="type === 'chart'" class="skeleton-chart">
      <div class="skeleton-chart__header">
        <div class="skeleton-line skeleton-line--short"></div>
        <div class="skeleton-line skeleton-line--tiny"></div>
      </div>
      <div class="skeleton-chart__body">
        <div class="skeleton-bars">
          <div
            v-for="i in 8"
            :key="i"
            class="skeleton-bar"
            :style="{ height: `${Math.random() * 60 + 20}%` }"
          ></div>
        </div>
      </div>
    </div>

    <div v-else-if="type === 'table'" class="skeleton-table">
      <div class="skeleton-table__header">
        <div v-for="i in columns" :key="i" class="skeleton-line skeleton-line--medium"></div>
      </div>
      <div class="skeleton-table__body">
        <div v-for="row in rows" :key="row" class="skeleton-table__row">
          <div v-for="col in columns" :key="col" class="skeleton-line skeleton-line--long"></div>
        </div>
      </div>
    </div>

    <div v-else-if="type === 'card'" class="skeleton-card">
      <div class="skeleton-card__header">
        <div class="skeleton-circle"></div>
        <div class="skeleton-line skeleton-line--medium"></div>
      </div>
      <div class="skeleton-card__body">
        <div class="skeleton-line skeleton-line--long"></div>
        <div class="skeleton-line skeleton-line--medium"></div>
      </div>
    </div>

    <div v-else class="skeleton-default">
      <div
        v-for="i in 3"
        :key="i"
        class="skeleton-line"
        :class="`skeleton-line--${i % 2 === 0 ? 'long' : 'medium'}`"
      ></div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  type: {
    type: String,
    default: 'default',
    validator: (value) => ['chart', 'table', 'card', 'default'].includes(value),
  },
  rows: {
    type: Number,
    default: 5,
  },
  columns: {
    type: Number,
    default: 4,
  },
});
</script>

<style lang="less" scoped>
@keyframes skeleton-loading {
  0% {
    background-position: -200px 0;
  }
  100% {
    background-position: calc(200px + 100%) 0;
  }
}

.skeleton-loader {
  width: 100%;
  padding: 12px;
}

.skeleton-line,
.skeleton-circle,
.skeleton-bar {
  background: linear-gradient(
    90deg,
    var(--sim-fill-light, var(--zx-semantic-surface-panel-fill)) 25%,
    var(--sim-bg-hover, var(--zx-semantic-border-default)) 37%,
    var(--sim-fill-light, var(--zx-semantic-surface-panel-fill)) 63%
  );
  background-size: 400px 100%;
  animation: skeleton-loading 1.4s ease infinite;
  border-radius: 4px;
}

.skeleton-line {
  height: 16px;
  margin-bottom: 12px;

  &--tiny {
    width: 60px;
  }

  &--short {
    width: 40%;
  }

  &--medium {
    width: 60%;
  }

  &--long {
    width: 100%;
  }
}

.skeleton-circle {
  width: 40px;
  height: 40px;
  border-radius: 50%;
}

// Chart skeleton
.skeleton-chart {
  &__header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
  }

  &__body {
    height: 200px;
    display: flex;
    align-items: flex-end;
    padding: 20px 0;
  }
}

.skeleton-bars {
  display: flex;
  align-items: flex-end;
  justify-content: space-around;
  width: 100%;
  height: 100%;
  gap: 8px;
}

.skeleton-bar {
  flex: 1;
  min-height: 20%;
  border-radius: 4px 4px 0 0;
}

// Table skeleton
.skeleton-table {
  &__header {
    display: flex;
    gap: 12px;
    margin-bottom: 16px;
    padding-bottom: 12px;
    border-bottom: 1px solid
      var(--sim-border-base, color-mix(in srgb, var(--zx-semantic-border-default) 50%, transparent));
  }

  &__row {
    display: flex;
    gap: 12px;
    margin-bottom: 12px;
  }
}

// Card skeleton
.skeleton-card {
  &__header {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 16px;
  }

  &__body {
    .skeleton-line {
      margin-bottom: 8px;
    }
  }
}
</style>
