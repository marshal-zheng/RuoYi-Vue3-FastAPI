import { defaultSerialBaudRates, defaultCanBaudRates, defaultDataBitsOptions, defaultStopBitsOptions, defaultParityOptions, defaultCanModeOptions, defaultProtocolOptions } from './selector/options';
/** Shared domain policy for the existing port page and schema authoring. */
export const portParamsPolicies = {
  RS422: { defaults: { baudRate: 115200, dataBits: 8, stopBits: 1, parity: 'None' }, triggers: { baudRate: 'change', dataBits: 'change', stopBits: 'change', parity: 'change' } },
  CAN: { defaults: { baudRate: 250000, canMode: 'A' }, triggers: { baudRate: 'change', canMode: 'change' } },
  LAN: { defaults: { ipAddress: '192.168.1.100', port: 8080, protocol: 'TCP' }, triggers: { ipAddress: 'blur', port: 'blur', protocol: 'change' } },
  '1553B': { defaults: { busAddress: 0, rtAddress: 0, subAddress: 0 }, triggers: { busAddress: 'blur', rtAddress: 'blur', subAddress: 'blur' } },
} as const;
export function getPortParamsPolicy(interfaceType: string) {
  return portParamsPolicies[interfaceType === 'RS485' ? 'RS422' : interfaceType as keyof typeof portParamsPolicies];
}
export function pickPortParams(interfaceType: string, values: Record<string, unknown>) {
  return Object.fromEntries(Object.keys(getPortParamsPolicy(interfaceType)?.defaults ?? {}).map(key => [key, values[key]]));
}
export function initializePortParams(interfaceType: string, existing?: Record<string, unknown> | null) {
  const defaults = getPortParamsPolicy(interfaceType)?.defaults ?? {};
  return { ...defaults, ...Object.fromEntries(Object.entries(pickPortParams(interfaceType, existing ?? {})).filter(([, value]) => value !== undefined)) };
}
export function validateIpAddress(value: unknown): string | undefined {
  if (!value) return '请输入 IP 地址';
  if (typeof value !== 'string' || !/^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$/.test(value)) return '请输入正确的 IP 地址格式';
  return undefined;
}
export interface PortTabControl { validate(): Promise<unknown>; getFormData(): unknown }
/** Reads and validates only the active editor. Other persisted config is retained. */
export async function submitCurrentPortTab(portInfo: Record<string, unknown>, tab: string, controls: { params?: PortTabControl; message?: PortTabControl }): Promise<Record<string, unknown> | false | undefined> {
  const control = tab === 'params' ? controls.params : tab === 'message' ? controls.message : undefined;
  if (!control) return undefined;
  if (!await control.validate()) return false;
  return { ...portInfo, [tab === 'params' ? 'params' : 'messageConfig']: control.getFormData() };
}

export function getPortParamOptions(type: string, field: string) {
  if (field === 'baudRate') return type === 'CAN' ? defaultCanBaudRates : defaultSerialBaudRates;
  return ({ dataBits: defaultDataBitsOptions, stopBits: defaultStopBitsOptions, parity: defaultParityOptions, canMode: defaultCanModeOptions, protocol: defaultProtocolOptions } as Record<string, { label: string; value: string | number }[]>)[field] ?? [];
}
