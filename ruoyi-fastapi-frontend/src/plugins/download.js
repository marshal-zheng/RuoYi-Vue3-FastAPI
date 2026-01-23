import { ElLoading, ElMessage } from 'element-plus';
import { saveAs } from 'file-saver';
import { http } from '@/utils/http';
import errorCode from '@/utils/errorCode';
import { blobValidate } from '@/utils/ruoyi';

let downloadLoadingInstance;

const downloadRequestOptions = {
  isReturnNativeResponse: true,
  isTransformResponse: false,
};

async function requestFile(config) {
  return http.get(
    {
      responseType: 'blob',
      ...config,
    },
    downloadRequestOptions
  );
}

async function handleBlobResponse(response, defaultName, mimeType) {
  const data = response?.data;
  if (blobValidate(data)) {
    const inferredName =
      response?.headers?.['download-filename'] &&
      decodeURIComponent(response.headers['download-filename']);
    const blob = mimeType ? new Blob([data], { type: mimeType }) : new Blob([data]);
    saveAs(blob, inferredName || defaultName || 'download');
    return;
  }
  await printErrMsg(data);
}

async function printErrMsg(data) {
  try {
    const text =
      typeof data === 'string'
        ? data
        : typeof data?.text === 'function'
          ? await data.text()
          : '';
    if (!text) {
      ElMessage.error('下载文件出现错误，请联系管理员！');
      return;
    }
    const rspObj = JSON.parse(text);
    const errMsg = errorCode[rspObj?.code] || rspObj?.msg || errorCode['default'];
    ElMessage.error(errMsg);
  } catch (error) {
    console.error(error);
    ElMessage.error('下载文件出现错误，请联系管理员！');
  }
}

export default {
  async name(name, isDelete = true) {
    try {
      const url = `/common/download?fileName=${encodeURIComponent(name)}&delete=${isDelete}`;
      const response = await requestFile({ url });
      await handleBlobResponse(response, name);
    } catch (error) {
      console.error(error);
      ElMessage.error('下载文件出现错误，请联系管理员！');
    }
  },
  async resource(resource) {
    try {
      const url = `/common/download/resource?resource=${encodeURIComponent(resource)}`;
      const response = await requestFile({ url });
      await handleBlobResponse(response, resource);
    } catch (error) {
      console.error(error);
      ElMessage.error('下载文件出现错误，请联系管理员！');
    }
  },
  async zip(url, name) {
    downloadLoadingInstance = ElLoading.service({
      text: '正在下载数据，请稍候',
      background: 'rgba(0, 0, 0, 0.7)',
    });
    try {
      const response = await requestFile({ url });
      await handleBlobResponse(response, name, 'application/zip');
    } catch (error) {
      console.error(error);
      ElMessage.error('下载文件出现错误，请联系管理员！');
    } finally {
      downloadLoadingInstance?.close?.();
    }
  },
  saveAs(text, name, opts) {
    saveAs(text, name, opts);
  },
  printErrMsg,
};
