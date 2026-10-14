import { ElMessageBox, ElLoading } from 'element-plus';

let loadingInstance;

const modal = {
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

// Preserve the business Promise contract: cancel/close must reject so callers
// never execute a mutation from their confirmation success branch.
export function createModal(feedback) {
  async function invoke(kind, content, title = '系统提示', options = {}) {
    if (title && typeof title === 'object') {
      options = title;
      title = '系统提示';
    }
    const defaults =
      kind === 'alert'
        ? {}
        : { confirmButtonText: '确定', cancelButtonText: '取消', type: 'warning' };
    const result = await feedback.modal[kind]({
      title,
      message: content,
      ...defaults,
      ...options,
    });
    if (!result.ok) {
      throw new Error(result.diagnostics.map(({ code }) => code).join(', '));
    }
    if (result.value === 'cancel' || result.value === 'close') throw result.value;
    return result.value;
  }

  return {
    ...modal,
    alert: (content, title, options) => invoke('alert', content, title, options),
    alertError: (content) => invoke('alert', content, '系统提示', { type: 'error' }),
    alertSuccess: (content) => invoke('alert', content, '系统提示', { type: 'success' }),
    alertWarning: (content) => invoke('alert', content, '系统提示', { type: 'warning' }),
    confirm: (content, title, options) => invoke('confirm', content, title, options),
    prompt: (content, title, options) => invoke('prompt', content, title, options),
  };
}

export default modal;
