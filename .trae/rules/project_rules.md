## CRUD 专项流程
1. **字段与权限梳理**：梳理实体字段、筛选条件、操作权限。
2. **API 设计**：在模块 `const.ts`、`types.ts`、`index.ts` 中补齐 URL、类型与导出，保持与当前项目的接口封装风格一致，确保命名统一。
3. **选择器封装**：下拉/树等组件置于 `components/selector/`，暴露 `modelValue` / `update:modelValue`，并在 `index.ts` 聚合导出；必要时标注数据加载时机。
4. **列表页**：
   - 必须遵循 `list.mdc` 的合同与模板：使用 `ZxContentWrap` + `ZxGridList`，`form`/`table` 两个插槽，`:load-data` 返回 `{ list,total }`；搜索/筛选先 `updateState('pager.page',1)` 再 `refresh()`；不手写分页，分页/挂载加载使用组件默认行为。
   - 布局建议：`<ZxContentWrap>` + `<ZxGridList class="zx-grid-list--page">`；工具栏左侧主操作、中间筛选、右侧 `ZxSearch`，与 `list.mdc` 保持一致。
   - 表格使用 `el-table :data="grid.list || []"`；操作列遵循 MoreAction 收纳规则：当行内操作数 `<=2` 全部直出；`>2` 仅直出第 1 个，余下由一个 `ZxMoreAction` 收纳（位于第 2 个控件位置）。
   - 危险操作必须 `ElMessageBox.confirm`；成功后 `ElMessage.success` 并触发 `refresh()` 或 `gridListRef.value?.refresh()`。
5. **表单弹窗/抽屉**：
   - 字段 ≤5 且简单采用 `ZxDialog` + `useDialog`；字段复杂或多步骤用 `ZxDrawer` + `useDrawer`。
   - `<el-form>` 绑定 `ref`、`model`、`rules`；选择字段引用 selector 组件；提交成功通过 `emit('success')` 通知刷新。
   - `defineExpose({ open, close })`，`open` 根据是否携带数据判断新增/编辑逻辑。
6. **详情或独立编辑页（可选）**：使用 `<content-detail-wrap>`，路由配置 `hidden: true` 并设置 `activeMenu` 指回列表。

## 生成代码务必执行
- 批量或危险操作必须校验权限、勾选状态，并在成功后调用 `gridListRef.value?.refresh()` 或等效刷新逻辑。
- 所有删除/停用类操作都要包裹 `ElMessageBox.confirm`，并在确认成功后给出刷新步骤提示。
- 返回数据中包含嵌套、枚举或字典值时，需明确字段映射方式（格式化函数、字典表或 selector 数据源）。
- 引用 ZXUI 组件前先搜索仓库现有示例；若无结果，标明需对照 `docs/com-docs/` 并解释核心用法，避免输出不符合的属性。
- 列表页产出需通过 `list.mdc` 的验收清单（结构、加载合同、搜索重置、MoreAction 收纳规则、自适应高度等）。



## 弹窗生成规则（Vue 3 + Element Plus + ZXUI useDialog）

面向 AI 生成代码的高内聚提示规范，指导使用 `@zxio/zxui` 的 `useDialog` 搭配 `ZxDialog` 实现表单弹窗：支持新增/编辑复用、校验、异步提交、滚动到错误、状态重置与对外暴露 `open/close`。

### 适用技术栈

- Vue 3 + <script setup>
- Element Plus 表单 `el-form`、`el-form-item`、`el-input`、`el-switch` 等
- ZXUI：`useDialog`、`ZxDialog`

### 核心合同（必须满足）

1) 容器与绑定
- 结构：`<ZxDialog v-bind="dialogProps" v-on="dialogEvents"> ... </ZxDialog>`。
- 表单：`<el-form ref="formRef" :model="state.data" :rules="formRules">`。
- 字段统一绑定到 `state.data.xxx`。

2) useDialog 配置要点
- `title`: (data) => data.id ? '编辑【实体】' : '新建【实体】'
- `width`: 合理宽度（如 '45%' 或具体 px）
- `okText`: computed(() => state.data.id ? '保存' : '创建')
- `formRef`: 传入 `formRef`，配合 `preValidate: true`
- `preValidate: true`: 点击确认先校验表单
- `autoScrollToError: true`: 校验失败时滚动定位
- `autoResetForm: true`: 关闭时自动重置表单
- `defaultData`: () => 返回初始表单结构（可从父级 props 注入必需字段，如 category）
- `onConfirm`: async (data) => 根据是否有 `data.id` 决定调用 `update` 或 `create`，返回接口结果
- `onConfirmError`: (e) => 可按需提示/记录

3) 对外 API
- `defineExpose({ open, close })`。
- `open(payload?)` 约定：
	- 新建：`open()` → 使用 `defaultData()`
	- 编辑：`open(rowOrId)` → 若提供标识（如 `id`），需先拉取详情 `getDetail(id)`，拿到完整数据后再 `open(detail)`

4) 事件
- 完成提交后必须 `emit('success', response)`，由父组件接收并触发列表刷新（见 list.mdc）。

5) 校验
- 使用 Element Plus 规则；支持基于 `state.data` 的动态校验（如 dataType 为 'enum' 时 `options` 至少一个非空）。

### 代码模板（按需替换占位符）

```vue

<template>
	<ZxDialog v-bind="dialogProps" v-on="dialogEvents">
		<div class="py-4">
			<el-form
				ref="formRef"
				:model="state.data"
				:rules="formRules"
				label-width="100px"
				label-position="right"
			>
				<!-- 字段示例：按业务替换/增删 -->
				<el-form-item label="名称" prop="name">
					<zx-input v-model="state.data.name" placeholder="请输入名称" maxlength="50" show-word-limit clearable />
				</el-form-item>

				<el-form-item label="类型" prop="type">
					<TypeSelector v-model="state.data.type" @change="handleTypeChange" />
				</el-form-item>

				<el-form-item v-if="state.data.type === 'enum'" label="枚举选项" prop="options">
					<div class="w-full">
						<div v-for="(opt, idx) in state.data.options" :key="idx" class="flex gap-2 mb-2 items-center">
							<zx-input v-model="state.data.options[idx]" placeholder="请输入选项值" clearable class="flex-1" />
							<zx-button type="danger" icon="Close" circle size="small" @click="removeOption(idx)" />
						</div>
						<zx-button type="primary" plain icon="Plus" @click="addOption">添加选项</zx-button>
					</div>
				</el-form-item>

				<el-form-item label="是否必填" prop="required">
					<el-switch v-model="state.data.required" />
				</el-form-item>

				<el-form-item label="描述" prop="description">
					<zx-input v-model="state.data.description" type="textarea" :rows="3" maxlength="200" show-word-limit />
				</el-form-item>
			</el-form>
		</div>
	</ZxDialog>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { FormInstance } from 'element-plus'
import { useDialog } from '@zxio/zxui'
// import { entityApi } from '@/api/modules/entity'
// import { TypeSelector } from './selector'

// 可选：接收父层必需上下文（如分类）
const props = defineProps<{ category?: string }>()

// 事件
const emit = defineEmits<{ success: [data?: any] }>()

// 表单引用
const formRef = ref<FormInstance>()

// 表单规则（含动态校验示例）
const formRules = computed(() => ({
	name: [
		{ required: true, message: '请输入名称', trigger: 'blur' },
		{ min: 2, max: 50, message: '名称长度在 2 到 50 个字符', trigger: 'blur' }
	],
	type: [
		{ required: true, message: '请选择类型', trigger: 'change' }
	],
	options: [
		{
			validator: (_rule: any, value: string[]) => {
				if (state.data.type === 'enum' && (!value?.length || !value.filter(v => v?.trim()).length)) {
					return new Error('枚举类型至少需要一个非空选项')
				}
				return true
			},
			trigger: 'change'
		}
	],
	description: [
		{ max: 200, message: '描述不能超过 200 个字符', trigger: 'blur' }
	]
}))

// useDialog
const { state, dialogProps, dialogEvents, open, close } = useDialog<any>({
	title: (data) => (data?.id ? '编辑【实体】' : '新建【实体】'),
	okText: computed(() => (state.data.id ? '保存' : '创建')),
	formRef,
	preValidate: true,
	autoScrollToError: true,
	autoResetForm: true,
	defaultData: () => ({
		name: '',
		type: 'text',
		options: [],
		required: false,
		description: '',
		...(props.category ? { category: props.category } : {})
	}),
	onConfirm: async (data) => {
		const { id, ...submitData } = data
		if (submitData.type === 'enum') {
			submitData.options = (submitData.options || []).filter((v: string) => v?.trim())
		} else {
			submitData.options = []
		}
		// const res = id ? await entityApi.update({ id, ...submitData }) : await entityApi.create(submitData)
		const res = { id: id || Date.now(), ...submitData } // 占位，生成时替换
		emit('success', res)
		return res
	},
	onConfirmError: (_e) => {}
})

// 打开（编辑时先拉详情）
const openDialog = async (payload?: any) => {
	if (payload?.id) {
		// const detail = await entityApi.getDetail(payload.id)
		const detail = { id: payload.id, name: '示例', type: 'text' } // 占位
		open(detail)
	} else {
		open()
	}
}

// 类型变更
const handleTypeChange = () => {
	state.data.options = state.data.type === 'enum'
		? (state.data.options?.length ? state.data.options : [''])
		: []
}

// 枚举选项增删
const addOption = () => { state.data.options.push('') }
const removeOption = (idx: number) => {
	if ((state.data.options?.length || 0) > 1) state.data.options.splice(idx, 1)
}

// 暴露方法
defineExpose({ open: openDialog, close })
</script>
```

### 验收清单

- 使用 `ZxDialog v-bind="dialogProps" v-on="dialogEvents"` 包裹表单；`el-form` 绑定 `ref/model/rules`。
- `useDialog` 已配置 `preValidate/autoScrollToError/autoResetForm/formRef`，`okText` 与 `title` 随 `id` 状态联动。
- `defaultData` 完整定义；如需从父层注入（如 `category`），通过 `props` 带入并合并。
- `onConfirm` 根据是否存在 `id` 调用 `create/update`，并在成功后 `emit('success', res)`。
- `open(payload?)` 支持新建/编辑：编辑场景先拉取详情再 `open(detail)`。
- 动态校验示例可运行（如 enum 的 options 非空）；类型切换时自动清理无效字段。
- `defineExpose({ open, close })` 已对外暴露。

### 注意事项与最佳实践

- 校验规则里引用响应式数据时，建议放入 `computed`，避免闭包旧值问题。
- 提交前的数据整理（如去空白、类型转换、字典映射）在 `onConfirm` 里完成，保持表单层干净。
- 与列表联动：父层监听 `@success` 后刷新列表（遵循 `list.mdc`）。

## 抽屉表单生成规则（Vue 3 + Element Plus + ZXUI useDrawer）

面向 AI 生成代码的高内聚提示规范，指导使用 `@zxio/zxui` 的 `useDrawer` 搭配 `ZxDrawer` 实现中等复杂度的表单：支持新增/编辑复用、校验、异步提交、骨架屏加载、状态重置与对外暴露 `open/close`。

### 适用技术栈

- Vue 3 + <script setup>
- Element Plus 表单 `el-form`、`el-form-item`、`el-input`（或项目内输入组件如 `zx-input`）等
- ZXUI：`useDrawer`、`ZxDrawer`

### 核心合同（必须满足）

1) 容器与绑定
- 结构：`<ZxDrawer v-bind="drawer.drawerProps.value" v-on="drawer.drawerEvents.value"> ... </ZxDrawer>`。
- 建议表单 `label-position="top"` 以节省水平空间。
- 表单：`<el-form ref="formRef" :model="drawer.state.data" :rules="formRules">`。
- 字段统一绑定到 `drawer.state.data.xxx`。

2) useDrawer 配置要点
- `size`: 推荐 35% ~ 50%。
- `placement`: 固定为 `right`。
- `okText`: computed 文案随编辑/新增联动（如 编辑=保存 / 新建=创建）。
- `formRef`: 传入 `formRef`，配合 `preValidate: true`。
- `formModel`: `computed(() => drawer.state.data)`，确保校验与提交指向同一数据源。
- `preValidate: true`: 点击确认先校验表单。
- `autoScrollToError: true`: 校验失败时滚动定位。
- `autoResetForm: true`: 关闭时自动重置表单。
- `loadingType: 'skeleton'`（可选）：配合详情加载呈现骨架屏。
- `defaultData`: () => 返回初始表单结构。
- `onConfirm`: async () => 读取 `drawer.state.data` 组织 `submitData`，根据模式调用 `update/create` 并返回响应。
- `onConfirmError`: (e) => 统一提示错误信息。

3) 对外 API
- `defineExpose({ open: openDrawer, close: drawer.close })`。
- `openDrawer(payload?)` 约定：
	- 打开前可先加载辅助数据（如字典/标签/分类）。
	- 编辑：`payload?.id` 存在 → `drawer.open()` 后异步 `getDetail(id)` 并回填；避免内容闪烁可结合骨架屏。
	- 新建：直接 `drawer.open()`，表单取 `defaultData()`。

4) 事件
- 提交成功必须 `emit('success', response)`，由父组件接收并触发列表刷新（参照 list.mdc）。

5) 校验
- 使用 Element Plus 规则；支持基于 `drawer.state.data` 的动态校验（如必选项、枚举项非空等）。

### 扩展合同：两步流「下一步」场景（不落库中转）

当抽屉用于“先收集基础信息 → 下一步进入复杂表单（新页面/更复杂编辑器/第二个抽屉）”的两步流程时，按以下方式实现，让生成器能够稳定产出：

1) 确认按钮文案
- 新增模式：`okText` 必须为“下一步”。
- 编辑模式：通常为“保存”（也可按业务需要仍用“下一步”）。

2) 提交行为（不直接调用后端落库）
- 在 `onConfirm` 内仅整理并返回基础信息，不调用 `create/update` 接口：
	- 通过 `emit('success', submitData)` 将收集到的数据上抛给父层；
	- 建议同时 `drawer.close()` 关闭当前抽屉，交由父层进行路由跳转或打开下一阶段容器；
	- 如确需保持抽屉不关闭，可通过配置开关控制（如 `keepOpenOnNext`），但默认关闭体验更一致。

3) 父层对接（列表页/上层容器）
- 监听 `@success`：
	- 新建场景（payload 无 id）：将 `submitData` 持久到 `sessionStorage`（或临时状态管理），随后跳转到下一页（参考 gen-crud 的“新页面规范”）或打开第二阶段抽屉；
	- 编辑场景（payload 含 id）：可直接跳转编辑页或继续后续步骤；
- 参考 list.mdc 的“表单组件与刷新”与 gen-crud 中的“列表页跳转逻辑”。

4) 只读关键字段（编辑态）
- 对部分一旦创建后不允许变更的关键字段（如“图类型 graphType”），编辑模式下应改为只读展示（如使用 `el-tag` 显示当前枚举文本），新增时提供选择器。

5) 详情映射与赋值
- 详情回填建议整对象覆盖：`drawer.state.data = { ...detail, ...派生映射 }`；
- 对数组/派生字段进行显式映射（如将 `detail.relations[].id` 映射为 `drawer.state.data.tagId`）。

6) 可选交互增强
- 抽屉可设置 `:draggable="false"` 避免拖拽误操作；
- 使用 `loadingType='skeleton'` 与 `drawerLoading` 遮挡编辑详情加载；
- 复杂选择类组件可按需提供便捷交互（如双击切换）（可选）。

### 代码模板（按需替换占位符）

```vue
<template>
	<ZxDrawer
		v-bind="drawer.drawerProps.value"
		v-on="drawer.drawerEvents.value"
	>
		<div class="drawer-form-container">
			<el-form
				ref="formRef"
				:model="drawer.state.data"
				:rules="formRules"
				label-position="top"
				class="mb-6"
			>
				<el-form-item label="名称" prop="name">
					<zx-input v-model="drawer.state.data.name" placeholder="请输入名称" maxlength="50" show-word-limit clearable />
				</el-form-item>

				<el-form-item label="分类" prop="categoryId">
					<CategorySelector v-model="drawer.state.data.categoryId" placeholder="请选择分类" style="width: 100%" />
				</el-form-item>

				<el-form-item label="描述" prop="description">
					<zx-input v-model="drawer.state.data.description" type="textarea" placeholder="请输入描述" :rows="4" maxlength="200" show-word-limit />
				</el-form-item>
			</el-form>
		</div>
	</ZxDrawer>
  
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import type { FormInstance } from 'element-plus'
import { useDrawer } from '@zxio/zxui'
// import { entityApi } from '@/api/modules/entity'
// import { CategorySelector } from '../selector'

// 事件
const emit = defineEmits<{ success: [data?: any] }>()

// 引用与状态
const formRef = ref<FormInstance | null>(null)
const drawerLoading = ref(false)
const isEditMode = ref(false)
const editingId = ref<string | number | null>(null)

// 表单规则
const formRules = {
	name: [
		{ required: true, message: '请输入名称', trigger: 'blur' },
		{ min: 2, max: 50, message: '名称长度在 2 到 50 个字符', trigger: 'blur' }
	],
	categoryId: [
		{ required: true, message: '请选择分类', trigger: 'change' }
	],
	description: [
		{ max: 200, message: '描述不能超过 200 个字符', trigger: 'blur' }
	]
}

// useDrawer
const drawer = useDrawer<any>({
	title: computed(() => (isEditMode.value ? '编辑' : '新建')),
	size: '40%',
	okText: computed(() => (isEditMode.value ? '保存' : '创建')),
	placement: 'right',
	formRef,
	formModel: computed(() => drawer.state.data),
	autoResetForm: true,
	preValidate: true,
	autoScrollToError: true,
	loadingType: 'skeleton',
	defaultData: () => ({
		name: '',
		categoryId: '',
		description: ''
	}),
	onConfirm: async () => {
		const submitData = {
			name: drawer.state.data.name,
			categoryId: drawer.state.data.categoryId,
			description: drawer.state.data.description
		}

		// const res = isEditMode.value && editingId.value
		//   ? await entityApi.update({ id: editingId.value, ...submitData })
		//   : await entityApi.create(submitData)
		const res = { id: editingId.value || Date.now(), ...submitData } // 占位
		emit('success', res)
		return res
	},
	onConfirmError: (error: any) => {
	}
})

// 可在打开前加载辅助数据（如分类/字典等），示例略

// 加载详情（编辑）
const loadDetail = async (id: string | number) => {
	drawerLoading.value = true
	try {
		// const detail = await entityApi.getDetail(id)
		const detail = { id, name: '示例', categoryId: '', description: '' } // 占位
		Object.assign(drawer.state.data, detail)
	} finally {
		drawerLoading.value = false
	}
}

// 打开
const openDrawer = async (payload?: { id?: string | number }) => {
	// 可在此处按需加载辅助数据
	if (payload?.id) {
		isEditMode.value = true
		editingId.value = payload.id
		drawer.open()
		await loadDetail(payload.id)
	} else {
		isEditMode.value = false
		editingId.value = null
		drawer.open()
	}
}

// 暴露方法
defineExpose({ open: openDrawer, close: drawer.close })
</script>

<style scoped>
.drawer-form-container {
	/* 局部样式占位 */
}
</style>
```

### 代码模板（两步「下一步」模式）

用于“先收集基础信息 → 下一步”的不落库中转抽屉模板。确认后仅上抛数据，父层负责跳转或打开下一阶段。

```vue
<template>
	<ZxDrawer
		v-bind="drawer.drawerProps.value"
		:draggable="false"
		:title="isEditMode ? '编辑' : '新建'"
		:loading="drawerLoading"
		loadingType="skeleton"
		v-on="drawer.drawerEvents.value"
	>
		<div class="drawer-form-container">
			<el-form
				ref="formRef"
				:model="drawer.state.data"
				:rules="formRules"
				label-position="top"
				class="mb-6"
			>
				<!-- 示例：编辑态关键字段只读展示，新建态可选 -->
				<el-form-item label="图类型" prop="graphType">
					<template v-if="isEditMode">
						<el-tag :type="graphTypeTagType">{{ GraphTypeLabels[drawer.state.data.graphType] }}</el-tag>
					</template>
					<GraphTypeSelector v-else v-model="drawer.state.data.graphType" placeholder="请选择图类型" />
				</el-form-item>

				<!-- 其他基础字段 -->
				<el-form-item label="名称" prop="name">
					<zx-input v-model="drawer.state.data.name" placeholder="请输入名称" maxlength="50" show-word-limit />
				</el-form-item>
				<el-form-item label="分类" prop="categoryId">
					<CategorySelector v-model="drawer.state.data.categoryId" placeholder="请选择分类" />
				</el-form-item>
				<el-form-item label="说明" prop="description">
					<zx-input v-model="drawer.state.data.description" type="textarea" :rows="4" maxlength="200" show-word-limit />
				</el-form-item>
			</el-form>
		</div>
	</ZxDrawer>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import type { FormInstance } from 'element-plus'
import { useDrawer } from '@zxio/zxui'
// import { GraphType, GraphTypeLabels } from '@/consts/xxx'
// import { CategorySelector, GraphTypeSelector } from '../selector'

const emit = defineEmits<{ success: [data?: any] }>()

const formRef = ref<FormInstance | null>(null)
const drawerLoading = ref(false)
const isEditMode = ref(false)

// 示例：按 graphType 计算只读 tag 的样式
const graphTypeTagType = computed(() => {
	const t = (drawer.state.data as any)?.graphType
	return t === 'TREE' ? 'success' : 'primary'
})

// 校验规则
const formRules = {
	name: [
		{ required: true, message: '请输入名称', trigger: 'blur' },
		{ min: 2, max: 50, message: '名称长度在 2 到 50 个字符', trigger: 'blur' }
	],
	categoryId: [{ required: true, message: '请选择分类', trigger: 'change' }],
	graphType: [{ required: true, message: '请选择图类型', trigger: 'change' }]
}

// 「下一步」模式：新增=下一步，编辑=保存（可按需仍用下一步）
const okText = computed(() => (isEditMode.value ? '保存' : '下一步'))

const drawer = useDrawer<any>({
	size: '35%',
	placement: 'right',
	okText,
	formRef,
	formModel: computed(() => drawer.state.data),
	autoResetForm: true,
	preValidate: true,
	autoScrollToError: true,
	defaultData: () => ({
		name: '',
		categoryId: '',
		description: '',
		graphType: 'TREE'
	}),
	onConfirm: async () => {
		// 仅收集数据并上抛，不调用后端接口
		const { /* 派生/冗余字段剔除 */ ...submitData } = drawer.state.data
		emit('success', submitData)
		// 建议默认关闭，交由父层进行跳转/打开下一阶段
		drawer.close()
	},
	onConfirmError: () => {}
})

// 打开逻辑：先 open，再在编辑态加载详情并整对象覆盖
const openDrawer = async (payload?: { id?: string | number }) => {
	if (payload?.id) {
		isEditMode.value = true
		drawer.open()
		drawerLoading.value = true
		try {
			// const detail = await api.getDetail(payload.id)
			const detail: any = { id: payload.id, name: '示例', categoryId: '', description: '', graphType: 'TREE' }
			drawer.state.data = {
				...detail,
				// 示例：派生映射，如 detail.tags[].id -> state.tagId
				// tagId: Array.isArray(detail.tags) ? detail.tags.map(t => t.id) : []
			}
		} finally {
			drawerLoading.value = false
		}
	} else {
		isEditMode.value = false
		drawer.open()
	}
}

defineExpose({ open: openDrawer, close: drawer.close })
</script>

<style scoped>
.drawer-form-container { }
</style>
```

### 验收清单

- 使用 `ZxDrawer v-bind="drawer.drawerProps.value" v-on="drawer.drawerEvents.value"` 包裹表单；`el-form` 绑定 `ref/model/rules` 且 `label-position="top"`。
- `useDrawer` 已配置 `preValidate/autoScrollToError/autoResetForm/formRef/formModel`，`okText` 与 `title` 随模式联动，`placement='right'`，`size` 合理。
- `defaultData` 完整定义；`onConfirm` 组织数据并返回结果；`onConfirmError` 明确用户级错误提示。
- `open(payload?)` 支持新建/编辑：打开前可加载辅助数据；编辑场景在 `drawer.open()` 后拉详情回填，骨架屏遮挡等待。
- 成功提交 `emit('success', res)`，由父层刷新列表（遵循 `list.mdc`）。

— 「下一步」场景专项 —
- 新增态 `okText` 为“下一步”，编辑态为“保存”（或按需统一为“下一步”）。
- `onConfirm` 仅上抛基础数据，不调用后端接口；默认调用 `drawer.close()`。
- 父层在 `@success` 中接收 payload：
	- 新建：写入 sessionStorage/临时状态后跳转到创建/设计页，或打开第二阶段抽屉；
	- 编辑：按需跳转编辑页或继续后续步骤；
- 编辑态对关键字段只读展示（如图类型），新增态提供选择控件。

### 注意事项与最佳实践

- 辅助数据（如字典/标签）应在 `open` 前或打开后立即加载；需要遮挡时配合骨架屏。
- 大表单建议字段分组与折叠，避免一次渲染过多组件影响性能。
- 避免在模板中写复杂逻辑：提交前的数据规整放在 `onConfirm` 内完成。
- 关闭抽屉后通过 `autoResetForm` 自动清理状态，避免复用造成脏数据。
- 与列表联动：父层监听 `@success` 后刷新列表（遵循 `list.mdc`），危险操作仍需二次确认（见 `crud.mdc`）。
- 两步流程推荐：用抽屉收集“基础信息”，通过 `emit('success')` 交给父层后再进行路由跳转或打开更复杂的编辑容器；确保 payload 结构清晰且剔除冗余字段。

## 列表页面生成规则（Vue 3 + Element Plus + ZxGridList）

面向 AI 生成代码的高内聚提示规范。用于快速产出“通用列表页”：包含工具栏（新建/筛选/搜索）、表格、分页、CRUD 操作与刷新流程。严格遵循下述合同与验收标准，避免自造轮子。

### 适用技术栈

- 视图框架：Vue 3 + <script setup>
- UI：Element Plus（配合项目的 Zx 组件）
- 列表容器：ZxGridList（封装分页/加载/状态）
- 自动导入：已启用 unplugin-auto-import（Vue/Router/部分 Element Plus API 可省略显式导入；如需手动导入，保持一致）

### 生成目标（合同）

1) 布局结构
- 外层必须使用 `ZxContentWrap`。
- 列表容器使用 `<ZxGridList />`，开启页面高度自适应：添加类名 `zx-grid-list--page`。
- 不在表格内部手写分页；分页由 ZxGridList 接管。

2) ZxGridList 必备 props
- `:load-data="loadData"` 数据加载函数，返回 Promise。
- 分页、挂载加载、选择清理等使用组件默认行为，无需显式传参。
- 可选：`:auto-fit-table-height="true"` 让表格自适应容器高度；或为 `el-table` 设置 `max-height`（如 `calc(100vh - 300px)`）。

3) 槽位与状态协议
- `form` 插槽入参：`{ query, loading, refresh, updateState }`。
	- 搜索/筛选字段用 `v-model="query.xxx"` 绑定；触发搜索/筛选时先 `updateState('pager.page', 1)` 再 `refresh()`。
- `table` 插槽入参：`{ grid, refresh }`。
	- `grid.list` 为表格数据；空时渲染空态或设置 `empty-text`。
- 如使用排序：监听 `@sort-change`，将 `{ prop, order }` 写入 `query` 或专门的 `sort` 字段，随后重置页码并刷新。

4) loadData 函数合同（关键）
- 入参（ZxGridList 注入）：`{ query: Record<string, any>, pager: { page, size }, [extra...] }`。
- 返回 Promise，解析为：`{ list: any[], total: number }`。
- 若后端返回即为此结构，可直接 `return res`；否则做一层适配：
	```ts
	return { list: res.data ?? [], total: res.total ?? 0 }
	```
- 页码从 1 开始；如后端从 0 开始，可改用 ZxGridList 的 `page-from-0` 配置或在适配中处理。

5) 工具栏规范
- 左侧：主操作（如“新建”）。
- 中间：可选筛选器（下拉/状态/日期等），变更即重置到第 1 页并刷新。
- 右侧：`ZxSearch` 搜索框，采用 `search-mode="click"`；`@search` 与 `@clear` 均调用统一的 `onSearch({ refresh, updateState })`。

6) 表格与操作列
- 使用 `el-table :data="grid.list || []"`，设置 `empty-text="暂无数据"`。
- 操作列固定在右侧，常见按钮：查看/编辑/删除；删除使用 `ElMessageBox.confirm` 二次确认，成功后 `ElMessage.success('删除成功')` 并调用 `refresh()`。
 - 操作按钮收纳（ZxMoreAction）逻辑：
	 - 若行内可用操作数量 `<= 2`：全部直接展示为按钮（不使用 MoreAction）。
	 - 若 `> 2`：仅保留第 1 个为直接按钮，第 2 个位置使用 `ZxMoreAction` 收纳其余所有操作（从第 2 个起）。最终只显示两个控件：第一个按钮 + 一个 MoreAction。
	 - 可通过 `isDivider: true` 在 MoreAction 列表中插入分隔符。

7) 表单组件与刷新
- 表单组件（Dialog/Drawer）对外暴露 `open(row?)`；Drawer 组件请遵循 `drawer.mdc` 规范。
- 表单提交成功后，父列表通过 `ref` 调用 `gridRef.value?.refresh()` 刷新，并在子组件内 `emit('success', data)` 通知父层。

8) 代码风格
- 优先使用 `<script setup lang="ts">`，但在无类型信息时可先行 JS，保留类型注释占位。
- 文案与变量命名清晰，尽量中文可读（或接入 i18n 的情况下使用 `useI18n`）。

### 代码模板（请据此生成并按需替换占位符）

```vue
<template>
	<ZxContentWrap>
		<ZxGridList
			ref="gridRef"
			:load-data="loadData"
			class="zx-grid-list--page"
		>
			<!-- 工具栏：左-操作 | 中-筛选 | 右-搜索 -->
			<template #form="{ query, loading, refresh, updateState }">
				<div class="zx-grid-form-bar">
					<div class="zx-grid-form-bar__left">
						<ZxButton type="primary" icon="Plus" @click="handleCreate">新建【实体】</ZxButton>
					</div>
					<div class="zx-grid-form-bar__filters">
						<!-- 可选：筛选器示例 -->
						<!--
						<SelectStatus
							v-model="query.status"
							placeholder="选择状态"
							@change="(v) => onFilterChange(v, { refresh, updateState })"
						/>
						-->
					</div>
					<div class="zx-grid-form-bar__right">
						<ZxSearch
							v-model="query.keyword"
							placeholder="搜索【关键字段】"
							:loading="loading"
							search-mode="click"
							@search="() => onSearch({ refresh, updateState })"
							@clear="() => onSearch({ refresh, updateState })"
						/>
					</div>
				</div>
			</template>

			<!-- 表格内容 -->
			<template #table="{ grid, refresh }">
				<el-table
					:data="grid.list || []"
				>
					<!-- 列定义：按需替换字段 -->
					<el-table-column prop="name" label="名称" min-width="180" show-overflow-tooltip />
					<el-table-column prop="code" label="编码" min-width="160" />
					<el-table-column prop="createTime" label="创建时间" width="180" />

					<el-table-column label="操作" width="200" fixed="right">
						<template #default="{ row }">
							<div class="op-col__wrap">
								<template v-for="item in getDirectActions(row)" :key="item.eventTag">
									<ZxButton
										link
										:type="item.danger ? 'danger' : 'primary'"
										@click="() => handleActionClick(item, row, refresh)"
									>
										{{ item.label }}
									</ZxButton>
								</template>
								<ZxMoreAction
									v-if="getMoreActions(row).length"
									:list="getMoreActions(row)"
									@select="(item) => handleActionClick(item, row, refresh)"
								/>
							</div>
						</template>
					</el-table-column>
				</el-table>
			</template>
		</ZxGridList>

		<!-- 表单对话框：替换为实际组件 -->
		<FormDialog ref="formDialogRef" @success="handleFormSuccess" />

		<!-- 可选：表单抽屉（遵循 drawer.mdc）：替换为实际组件 -->
		<FormDrawer ref="formDrawerRef" @success="handleFormSuccess" />
	</ZxContentWrap>
  
</template>

<script setup lang="ts">
import { ElMessage, ElMessageBox } from 'element-plus'
// import FormDialog from './components/FormDialog.vue'
// import { entityApi } from '@/api/modules/entity' // 替换为实际模块

const gridRef = ref<any>(null)
const formDialogRef = ref<any>()
const formDrawerRef = ref<any>()

// 可选：为行数据定义类型
// interface Row { id: string | number; name: string; code: string; createTime?: string }

const loadData = async (params: any) => {
	// const res = await entityApi.getList({ ...params })
	// 标准返回：{ list, total }；如后端返回不同结构，请在此适配
	// return { list: res.data ?? [], total: res.total ?? 0 }
	return res // 占位，生成时请替换为真实实现
}

// 统一搜索处理：重置到第1页并刷新
const onSearch = ({ refresh, updateState }) => {
	updateState('pager.page', 1)
	refresh()
}

// 筛选变更（可选）
const onFilterChange = (_val, { refresh, updateState }) => {
	updateState('pager.page', 1)
	nextTick(() => refresh())
}

// 新建/编辑/删除
const handleCreate = () => formDialogRef.value?.open()
const handleEdit = (row: any) => formDialogRef.value?.open(row)
const handleDelete = async (row: any, refresh: () => void) => {
	await ElMessageBox.confirm(
		`您即将删除“${row.name ?? row.id}”，此操作不可恢复，是否确认删除？`,
		'删除确认',
		{
			confirmButtonText: '确认删除',
			cancelButtonText: '取消',
			type: 'warning',
			confirmButtonClass: 'el-button--danger'
		}
	)
	// await entityApi.delete(row.id)
	refresh()
}

// 表单提交成功后刷新列表
const handleFormSuccess = () => gridRef.value?.refresh()

// 可选：使用抽屉表单（遵循 drawer.mdc）
const handleCreateDrawer = () => formDrawerRef.value?.open()
const handleEditDrawer = (row: any) => formDrawerRef.value?.open(row)

// —— 操作栏（ZxMoreAction）通用逻辑 ——
type ActionItem = {
	label: string
	eventTag: string
	icon?: any
	danger?: boolean
	disabled?: boolean
	show?: (row: any) => boolean
}

// 基础操作清单：按业务场景替换/扩展
const buildActionList = (row: any): ActionItem[] => [
	{ label: '编辑', eventTag: 'edit' },
	{ label: '删除', eventTag: 'delete', danger: true },
]

// 拆分规则：<=2 直接展示；>2 仅第1个直出，其余进入 MoreAction（第2个控件）
const splitActions = (row: any) => {
	const all = buildActionList(row).filter((i) => (i.show ? i.show(row) : true))
	if (all.length <= 2) {
		return { direct: all, more: [] as ActionItem[] }
	}
	return { direct: [all[0]], more: all.slice(1) }
}

const getDirectActions = (row: any) => splitActions(row).direct
const getMoreActions = (row: any) => splitActions(row).more

// 统一处理点击（直出按钮与 MoreAction 共用）
const handleActionClick = (item: ActionItem, row: any, refresh: () => void) => {
	switch (item.eventTag) {
		case 'edit':
			return handleEdit(row)
		case 'delete':
			return handleDelete(row, refresh)
		default:
			// 可扩展：export/enable/disable/查看表 等
			break
	}
}
</script>
```

### 验收清单（生成后逐项自检）

- 结构：`ZxContentWrap` + `ZxGridList` + form/table 两槽位齐全。
- 分页：不手写；由 ZxGridList 默认处理（无需额外 props）。
- 搜索/筛选：均通过 `query.*` 绑定；触发后重置页码并刷新。
- 加载：挂载后自动触发（组件默认）；`loadData` 返回 `{ list, total }`。
- 表格：空态可见；操作列固定右侧；按钮语义清晰。
- 操作栏：当行操作数 <= 2 时全部直出；> 2 时仅直出第 1 个，余下收纳进一个 MoreAction（第二个控件）。
 - 刷新：删除或表单成功后，调用 `refresh()` 或 `gridRef.value?.refresh()`；如使用 Drawer，需在子组件内 `emit('success')` 并由父层统一刷新（遵循 `drawer.mdc`）。
- 自适应：使用 `zx-grid-list--page`；必要时设置 `max-height` 或 `auto-fit-table-height`。
- 错误与确认：删除有二次确认；成功/失败有用户提示（ElMessage）。

### 可选增强

- 更多操作下拉（`ZxMoreAction`）统一收纳高级动作（如：设为模板）。
- 排序：`@sort-change` 写入 `query` 并刷新；后端排序字段与方向清晰映射。
- 权限：根据权限指令/变量控制按钮显隐。
- i18n：在有翻译需求时用 `useI18n` 管理文本。

### 禁止与注意

- 禁止在表格内部实现分页；统一由 ZxGridList 处理。
- 禁止绕过 `query` 私自管理搜索/筛选状态。
- 注意：搜索/筛选必须将页码重置为 1 再刷新，避免越界空页。
- 注意：如后端页码从 0 开始，需统一在 ZxGridList 或适配层处理。
