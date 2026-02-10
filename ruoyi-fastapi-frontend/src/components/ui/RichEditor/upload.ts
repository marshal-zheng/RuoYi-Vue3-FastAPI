import request from '@/utils/request';

/**
 * Custom Upload Adapter for CKEditor 5
 */
export default class MyUploadAdapter {
  loader: any;
  uploadUrl: string;

  constructor(loader: any, uploadUrl: string) {
    // The file loader instance to use during the upload.
    this.loader = loader;
    this.uploadUrl = uploadUrl;
  }

  // Starts the upload process.
  upload(): Promise<{ default: string }> {
    return this.loader.file.then(
      (file: File) =>
        new Promise((resolve, reject) => {
          const data = new FormData();
          data.append('file', file);

          request({
            url: this.uploadUrl,
            method: 'post',
            data: data,
            headers: {
              'Content-Type': 'multipart/form-data',
            },
          })
            .then((res: any) => {
              // HTTP 2xx 已由拦截器判定，直接处理成功响应
              resolve({
                default: res.url, // Assuming the backend returns the full URL in 'url' field, or construct it
              });
            })
            .catch((error: any) => {
              // 错误已由拦截器统一处理
              reject(error);
            });
        })
    );
  }

  // Aborts the upload process.
  abort(): void {
    // Implement abort logic if needed, but axios cancellation requires a cancel token
    // For simplicity, we can leave this empty or implement it later if strictly required
  }
}
