<template>
  <ZxContentWrap>
    <ZxGridList
      ref="gridListRef"
      :load-data="loadDeptData"
      :show-pagination="false"
      :load-on-mounted="true"
      class="zx-grid-list--page"
    >
      <template #form="{ query, loading, refresh: handleRefresh, updateState }">
        <div class="zx-grid-form-bar">
          <div class="zx-grid-form-bar__left">
            <ZxButton type="primary" icon="Plus" @click="handleAdd" v-hasPermi="['system:dept:add']"
              >新增</ZxButton
            >
            <ZxButton type="info" icon="Sort" @click="toggleExpandAll">展开/折叠</ZxButton>
          </div>
          <div class="zx-grid-form-bar__filters">
            <el-input
              v-model="query.deptName"
              placeholder="请输入部门名称"
              clearable
              style="width: 200px"
              @keyup.enter="() => onSearch({ handleRefresh, updateState })"
            />
            <el-select
              v-model="query.status"
              placeholder="部门状态"
              clearable
              style="width: 200px"
              @change="(v) => onFilterChange('status', v, { handleRefresh, updateState })"
            >
              <el-option
                v-for="dict in sys_normal_disable"
                :key="dict.value"
                :label="dict.label"
                :value="dict.value"
              />
            </el-select>
          </div>
          <div class="zx-grid-form-bar__right">
            <ZxSearch
              v-model="query.deptName"
              placeholder="搜索部门名称"
              :loading="loading"
              search-mode="click"
              @search="() => onSearch({ handleRefresh, updateState })"
              @clear="() => onSearch({ handleRefresh, updateState })"
            />
          </div>
        </div>
      </template>

      <template #table="{ grid }">
        <el-table
          v-if="refreshTable"
          v-loading="grid.loading"
          :data="grid.list || []"
          row-key="deptId"
          :default-expand-all="isExpandAll"
          :tree-props="{ children: 'children', hasChildren: 'hasChildren' }"
        >
          <el-table-column prop="deptName" label="部门名称"></el-table-column>
          <el-table-column prop="orderNum" label="排序"></el-table-column>
          <el-table-column prop="status" label="状态">
            <template #default="scope">
              <dict-tag :options="sys_normal_disable" :value="scope.row.status" />
            </template>
          </el-table-column>
          <el-table-column label="创建时间" prop="createTime" width="200">
            <template #default="scope">
              <span>{{ parseTime(scope.row.createTime) }}</span>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="200" class-name="small-padding fixed-width">
            <template #default="scope">
               <div class="op-col__wrap">
                <zx-button
                  link
                  type="primary"
                  @click="handleUpdate(scope.row)"
                  v-hasPermi="['system:dept:edit']"
                  >修改</zx-button
                >
                <zx-button
                  link
                  type="primary"
                  @click="handleAdd(scope.row)"
                  v-hasPermi="['system:dept:add']"
                  >新增</zx-button
                >
                <ZxMoreAction
                  v-if="scope.row.parentId != 0"
                  :list="getMoreActionList(scope.row)"
                  @select="handleMoreActionSelect($event, scope.row)"
                />
               </div>
            </template>
          </el-table-column>
        </el-table>
      </template>
    </ZxGridList>

    <el-dialog :title="title" v-model="open" width="600px" append-to-body>
      <el-form ref="deptRef" :model="form" :rules="rules" label-width="80px">
        <el-row>
          <el-col :span="24" v-if="form.parentId !== 0">
            <el-form-item label="上级部门" prop="parentId">
              <el-tree-select
                v-model="form.parentId"
                :data="deptOptions"
                :props="{ value: 'deptId', label: 'deptName', children: 'children' }"
                value-key="deptId"
                placeholder="选择上级部门"
                check-strictly
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="部门名称" prop="deptName">
              <el-input v-model="form.deptName" placeholder="请输入部门名称" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="显示排序" prop="orderNum">
              <el-input-number v-model="form.orderNum" controls-position="right" :min="0" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="负责人" prop="leader">
              <el-input v-model="form.leader" placeholder="请输入负责人" maxlength="20" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="联系电话" prop="phone">
              <el-input v-model="form.phone" placeholder="请输入联系电话" maxlength="11" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="邮箱" prop="email">
              <el-input v-model="form.email" placeholder="请输入邮箱" maxlength="50" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="部门状态">
              <el-radio-group v-model="form.status">
                <el-radio
                  v-for="dict in sys_normal_disable"
                  :key="dict.value"
                  :value="dict.value"
                  >{{ dict.label }}</el-radio
                >
              </el-radio-group>
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
      <template #footer>
        <div class="dialog-footer">
          <el-button type="primary" @click="submitForm">确 定</el-button>
          <el-button @click="cancel">取 消</el-button>
        </div>
      </template>
    </el-dialog>
  </ZxContentWrap>
</template>

<script setup name="Dept">
import {
  listDept,
  getDept,
  delDept,
  addDept,
  updateDept,
  listDeptExcludeChild,
} from '@/api/system/dept';

const { proxy } = getCurrentInstance();
const { sys_normal_disable } = proxy.useDict('sys_normal_disable');

const open = ref(false);
const showSearch = ref(true);
const title = ref('');
const deptOptions = ref([]);
const isExpandAll = ref(true);
const refreshTable = ref(true);
const gridListRef = ref(null);

const data = reactive({
  form: {},
  rules: {
    parentId: [{ required: true, message: '上级部门不能为空', trigger: 'blur' }],
    deptName: [{ required: true, message: '部门名称不能为空', trigger: 'blur' }],
    orderNum: [{ required: true, message: '显示排序不能为空', trigger: 'blur' }],
    email: [{ type: 'email', message: '请输入正确的邮箱地址', trigger: ['blur', 'change'] }],
    phone: [
      { pattern: /^1[3|4|5|6|7|8|9][0-9]\d{8}$/, message: '请输入正确的手机号码', trigger: 'blur' },
    ],
  },
});

const { form, rules } = toRefs(data);

async function loadDeptData(params) {
  const query = {
    deptName: params.query?.deptName,
    status: params.query?.status,
  };
  try {
    const response = await listDept(query);
    const tree = proxy.handleTree(response.data, 'deptId');
    return { data: tree || [], total: 0 };
  } catch (e) {
    return { data: [], total: 0 };
  }
}

function onFilterChange(field, value, { handleRefresh, updateState }) {
  updateState({ [field]: value });
  handleRefresh();
}

function onSearch({ handleRefresh }) {
  handleRefresh();
}
function cancel() {
  open.value = false;
  reset();
}
/** 表单重置 */
function reset() {
  form.value = {
    deptId: undefined,
    parentId: undefined,
    deptName: undefined,
    orderNum: 0,
    leader: undefined,
    phone: undefined,
    email: undefined,
    status: '0',
  };
  proxy.resetForm('deptRef');
}
/** 新增按钮操作 */
function handleAdd(row) {
  reset();
  listDept().then((response) => {
    deptOptions.value = proxy.handleTree(response.data, 'deptId');
  });
  if (row != undefined) {
    form.value.parentId = row.deptId;
  }
  open.value = true;
  title.value = '添加部门';
}
/** 展开/折叠操作 */
function toggleExpandAll() {
  refreshTable.value = false;
  isExpandAll.value = !isExpandAll.value;
  nextTick(() => {
    refreshTable.value = true;
  });
}
/** 修改按钮操作 */
function handleUpdate(row) {
  reset();
  listDeptExcludeChild(row.deptId).then((response) => {
    deptOptions.value = proxy.handleTree(response.data, 'deptId');
  });
  getDept(row.deptId).then((response) => {
    form.value = response.data;
    open.value = true;
    title.value = '修改部门';
  });
}
/** 提交按钮 */
function submitForm() {
  proxy.$refs['deptRef'].validate((valid) => {
    if (valid) {
      if (form.value.deptId != undefined) {
        updateDept(form.value).then((response) => {
          proxy.$modal.msgSuccess('修改成功');
          open.value = false;
          gridListRef.value?.refresh();
        });
      } else {
        addDept(form.value).then((response) => {
          proxy.$modal.msgSuccess('新增成功');
          open.value = false;
          gridListRef.value?.refresh();
        });
      }
    }
  });
}
/** 删除按钮操作 */
function handleDelete(row) {
  proxy.$modal
    .confirm('是否确认删除名称为"' + row.deptName + '"的数据项?')
    .then(function () {
      return delDept(row.deptId);
    })
    .then(() => {
      gridListRef.value?.refresh();
      proxy.$modal.msgSuccess('删除成功');
    })
    .catch(() => {});
}

/** 获取更多操作列表 */
function getMoreActionList(row) {
  const actions = [];
  if (row.parentId != 0) {
    actions.push({
      label: '删除',
      eventTag: 'delete',
      icon: 'Delete',
      danger: true,
      permission: 'system:dept:remove'
    });
  }
  return actions;
}

/** 处理更多操作选择 */
function handleMoreActionSelect(item, row) {
  switch (item.eventTag) {
    case 'delete':
      handleDelete(row);
      break;
    default:
      break;
  }
}
</script>
