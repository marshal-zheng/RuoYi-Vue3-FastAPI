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
              if (res.code === 200) {
                resolve({
                  default: res.url, // Assuming the backend returns the full URL in 'url' field, or construct it
                });
              } else {
                reject(res.msg || 'Upload failed');
              }
            })
            .catch((error: any) => {
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
