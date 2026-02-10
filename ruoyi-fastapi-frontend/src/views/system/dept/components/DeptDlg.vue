<template>
  <ZxDialog v-bind="dialogProps" v-on="dialogEvents">
    <el-form :model="state.data" :rules="formRules" label-width="80px">
      <el-row>
        <el-col :span="24" v-if="state.data.parentId !== 0">
          <el-form-item label="上级部门" prop="parentId">
            <el-tree-select
              v-model="state.data.parentId"
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
            <el-input v-model="state.data.deptName" placeholder="请输入部门名称" />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="显示排序" prop="orderNum">
            <el-input-number v-model="state.data.orderNum" controls-position="right" :min="0" />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="负责人" prop="leader">
            <el-input v-model="state.data.leader" placeholder="请输入负责人" maxlength="20" />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="联系电话" prop="phone">
            <el-input v-model="state.data.phone" placeholder="请输入联系电话" maxlength="11" />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="邮箱" prop="email">
            <el-input v-model="state.data.email" placeholder="请输入邮箱" maxlength="50" />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="部门状态">
            <el-radio-group v-model="state.data.status">
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
  </ZxDialog>
</template>

<script setup lang="ts" name="DeptDlg">
import { addDept, updateDept, listDept, listDeptExcludeChild } from '@/api/system/dept';
import { useDialog } from '@zxio/zxui';
import { ElMessage } from 'element-plus';
import { ref } from 'vue';

const { proxy } = getCurrentInstance();

// 延迟加载字典数据
const sys_normal_disable = ref<any[]>([]);
let dictLoaded = false;

interface DeptForm {
  deptId?: number;
  parentId?: number;
  deptName?: string;
  orderNum?: number;
  leader?: string;
  phone?: string;
  email?: string;
  status?: string;
}

const emit = defineEmits(['success']);

const deptOptions = ref([]);

const formRules = {
  parentId: [{ required: true, message: '上级部门不能为空', trigger: 'blur' }],
  deptName: [{ required: true, message: '部门名称不能为空', trigger: 'blur' }],
  orderNum: [{ required: true, message: '显示排序不能为空', trigger: 'blur' }],
  email: [{ type: 'email', message: '请输入正确的邮箱地址', trigger: ['blur', 'change'] }],
  phone: [
    { pattern: /^1[3|4|5|6|7|8|9][0-9]\d{8}$/, message: '请输入正确的手机号码', trigger: 'blur' },
  ],
};

const { state, dialogProps, dialogEvents, open } = useDialog<DeptForm>({
  title: (data: DeptForm) => (data?.deptId ? '修改部门' : '添加部门'),
  width: '600px',
  defaultData: () => ({
    deptId: undefined,
    parentId: undefined,
    deptName: undefined,
    orderNum: 0,
    leader: undefined,
    phone: undefined,
    email: undefined,
    status: '0',
  }),
  onOpen: async (data: DeptForm) => {
    // 只在第一次打开时加载字典
    if (!dictLoaded) {
      const dict = proxy.useDict('sys_normal_disable');
      sys_normal_disable.value = dict.sys_normal_disable?.value || [];
      dictLoaded = true;
    }
    
    if (data?.deptId) {
      const response = await listDeptExcludeChild(data.deptId);
      deptOptions.value = proxy.handleTree(response, 'deptId');
    } else {
      const response = await listDept();
      deptOptions.value = proxy.handleTree(response, 'deptId');
    }
  },
  onConfirm: async (data: DeptForm) => {
    if (data.deptId !== undefined) {
      await updateDept(data);
      ElMessage.success('修改成功');
    } else {
      await addDept(data);
      ElMessage.success('新增成功');
    }
    emit('success');
    return true;
  },
  onConfirmError: (e: any) => {
    ElMessage.error(e?.message || '提交失败，请重试');
  },
});

defineExpose({ open });
</script>
