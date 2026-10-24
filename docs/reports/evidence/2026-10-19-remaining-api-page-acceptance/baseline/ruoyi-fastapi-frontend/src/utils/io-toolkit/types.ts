export interface DownloadOptions {
  filename?: string;
  contentType?: string;
  showLoading?: boolean;
  loadingText?: string;
}

export interface ImportError {
  row?: number;
  field?: string;
  message: string;
  value?: unknown;
}

export interface ImportResult<T = unknown> {
  status: 'success' | 'partial' | 'failed';
  totalCount: number;
  successCount: number;
  failedCount: number;
  data?: T;
  errors: ImportError[];
}

export interface FileValidationResult {
  valid: boolean;
  error?: string;
}

export interface FileValidationOptions {
  accept?: string[];
  maxSize?: number;
  minSize?: number;
}
