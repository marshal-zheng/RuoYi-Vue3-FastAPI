<template>
  <tr :data-row="rowId">
    <td>{{ rowId }} · {{ dictType }}</td>
    <td><DictSelect v-model="selected" :dict-type="dictType" placeholder="选择字典项" /></td>
    <td>
      <DictAutocomplete v-model="autocompleteValue" :dict-type="dictType" placeholder="输入草稿" />
    </td>
    <td><DictTag :options="options" :value="selected" /></td>
    <td>
      <DictStatus :types="[dictType]" />
      <output>select={{ selected }}; autocomplete={{ autocompleteValue }}</output>
    </td>
  </tr>
</template>
<script setup lang="ts">
import { onMounted, ref } from 'vue';
import DictSelect from '@/components/business/DictSelect/index.vue';
import DictAutocomplete from '@/components/business/DictAutocomplete/index.vue';
import DictStatus from '@/components/business/DictStatus/index.vue';
import DictTag from '@/components/ui/DictTag/index.vue';
import { useDict } from '@/utils/dict';

const props = defineProps<{ rowId: number; dictType: string }>();
const emit = defineEmits<{ mounted: [rowId: number] }>();
const selected = ref('');
const autocompleteValue = ref('');
const options = useDict(props.dictType)[props.dictType];
onMounted(() => emit('mounted', props.rowId));
</script>
