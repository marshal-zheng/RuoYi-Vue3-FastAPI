export type ProtocolEditorField = {
  id: string;
  parentId: string | null;
  fieldName: string;
  byteCount: string | number;
  byteSequence: string;
  valueRange: string;
  unit: string;
  dataType: string;
  scale: string;
  remark: string;
  checked?: boolean;
};

export type ProtocolBaseConfig = {
  sender: string;
  receiver: string;
  frequency: string;
  frequencyLabel: string;
  speed: string;
  speedLabel: string;
  method: string;
  methodLabel: string;
  frameLength: string;
  errorHandle: string;
  errorHandleLabel: string;
  notes: string;
  fields: ProtocolEditorField[];
};

export type CANProtocolConfig = ProtocolBaseConfig & { canId: string };
export type RS422ProtocolConfig = ProtocolBaseConfig & { sendDuration: string };
export type EthernetProtocolConfig = ProtocolBaseConfig & { port: string };
export type Protocol1553BConfig = ProtocolBaseConfig & { subAddress: string };

export type ProtocolConfigTableRow = {
  protocolName: string;
  label1: string;
  value1: string;
  label2: string;
  value2: string;
};

const configText = (value: unknown): string =>
  typeof value === 'string' || typeof value === 'number' ? String(value) : '';

/** Native inputs emit text; dictionary editors emit a value and optional label. */
export const normalizeConfigEditorValue = (input: unknown): { value: string; label: string } => {
  if (input && typeof input === 'object') {
    if ('value' in input) {
      return {
        value: configText(input.value),
        label: 'label' in input ? configText(input.label) : '',
      };
    }
    if ('target' in input && input.target instanceof HTMLInputElement) {
      return { value: input.target.value, label: '' };
    }
  }
  return { value: configText(input), label: '' };
};
