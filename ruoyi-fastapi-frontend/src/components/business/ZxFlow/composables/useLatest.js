import { ref, isRef, watch } from 'vue'

export function useLatest(source) {
  const latest = ref(isRef(source) ? source.value : source)

  if (isRef(source)) {
    watch(source, (v) => {
      latest.value = v
    })
  }

  return latest
}
