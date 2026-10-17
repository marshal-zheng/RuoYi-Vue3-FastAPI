import { saveAs } from 'file-saver';
import { downloadFile } from '@/utils/request';

export default {
  zip(url, name, config = {}) {
    return downloadFile({ ...config, url, method: 'get' }, name);
  },
  saveAs(text, name, opts) {
    saveAs(text, name, opts);
  },
};
