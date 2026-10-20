/** Existing selector choices, shared with schema consumers. */
export const defaultProtocolOptions = [
  { label: 'TCP', value: 'TCP' },
  { label: 'UDP', value: 'UDP' },
];
export const defaultCanModeOptions = [
  { label: 'A 模式', value: 'A' },
  { label: 'B 模式', value: 'B' },
];
export const defaultParityOptions = [
  { label: '无校验(None)', value: 'None' },
  { label: '奇校验(Odd)', value: 'Odd' },
  { label: '偶校验(Even)', value: 'Even' },
  { label: '标记(Mark)', value: 'Mark' },
  { label: '空格(Space)', value: 'Space' },
];
export const defaultStopBitsOptions = [
  { label: '1', value: 1 },
  { label: '1.5', value: 1.5 },
  { label: '2', value: 2 },
];
export const defaultDataBitsOptions = [
  { label: '5', value: 5 },
  { label: '6', value: 6 },
  { label: '7', value: 7 },
  { label: '8', value: 8 },
];
export const defaultSerialBaudRates = [
  { label: '9600 bps', value: 9600 },
  { label: '19200 bps', value: 19200 },
  { label: '38400 bps', value: 38400 },
  { label: '57600 bps', value: 57600 },
  { label: '115200 bps', value: 115200 },
  { label: '230400 bps', value: 230400 },
  { label: '460800 bps', value: 460800 },
  { label: '921600 bps', value: 921600 },
];
export const defaultCanBaudRates = [
  { label: '5 Kbps', value: 5000 },
  { label: '10 Kbps', value: 10000 },
  { label: '20 Kbps', value: 20000 },
  { label: '50 Kbps', value: 50000 },
  { label: '100 Kbps', value: 100000 },
  { label: '125 Kbps', value: 125000 },
  { label: '250 Kbps', value: 250000 },
  { label: '500 Kbps', value: 500000 },
  { label: '800 Kbps', value: 800000 },
  { label: '1 Mbps', value: 1000000 },
];
