import { ElMessageBox, ElLoading } from 'element-plus';

let loadingInstance;

export default {
  // 弹出提示
  alert(content) {
    ElMessageBox.alert(content, '系统提示');
  },
  // 错误提示
  alertError(content) {
    ElMessageBox.alert(content, '系统提示', { type: 'error' });
  },
  // 成功提示
  alertSuccess(content) {
    ElMessageBox.alert(content, '系统提示', { type: 'success' });
  },
  // 警告提示
  alertWarning(content) {
    ElMessageBox.alert(content, '系统提示', { type: 'warning' });
  },
  // 确认窗体
  confirm(content) {
    return ElMessageBox.confirm(content, '系统提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    });
  },
  // 提交内容
  prompt(content) {
    return ElMessageBox.prompt(content, '系统提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    });
  },
  // 打开遮罩层
  loading(content) {
    // The mask colour comes from the theme (--el-mask-color).
    loadingInstance = ElLoading.service({
      lock: true,
      text: content,
    });
  },
  // 关闭遮罩层
  closeLoading() {
    loadingInstance.close();
  },
};
