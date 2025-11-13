const BCRYPT_MAX_BYTES = 72;

/**
 * 截断可能超过bcrypt 72字节限制的密码，避免后端报错。
 * 保证对多字节字符友好：先转成Uint8Array再裁剪。
 */
export function clampBcryptPassword(password: string): string {
  if (!password) {
    return password;
  }
  const encoder = new TextEncoder();
  const decoder = new TextDecoder('utf-8', { fatal: false });
  const bytes = encoder.encode(password);
  if (bytes.length <= BCRYPT_MAX_BYTES) {
    return password;
  }
  const truncated = bytes.slice(0, BCRYPT_MAX_BYTES);
  return decoder.decode(truncated);
}
