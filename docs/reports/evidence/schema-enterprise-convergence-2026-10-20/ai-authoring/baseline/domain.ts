export interface PostValues { postName: string; postCode: string; postSort: number; status: '0' | '1'; remark: string; }
export interface PostDto extends PostValues { postId?: number }
export interface ServerIssue { field: string; message: string }
export interface PostApi { write(dto: PostDto, signal: AbortSignal): Promise<{ ok: true } | { ok: false; errors: readonly ServerIssue[] }>; }
