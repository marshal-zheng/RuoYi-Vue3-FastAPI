import request from '@/utils/request';

interface UploadFileLoader {
  file: Promise<File | null>;
}

export default class MyUploadAdapter {
  constructor(
    private loader: UploadFileLoader,
    private uploadUrl: string
  ) {}

  async upload(): Promise<{ default: string }> {
    const file = await this.loader.file;
    if (!file) throw new Error('No file is available for upload');
    const data = new FormData();
    data.append('file', file);
    const result = await request<{ url: string }>({
      url: this.uploadUrl,
      method: 'post',
      data,
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return { default: result.url };
  }

  abort(): void {}
}
