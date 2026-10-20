/** Domain policies shared by the RS422 table and schema-form integration. */
export const RS422_TYPE_BYTES: Readonly<Record<string, number>> = Object.freeze({
  UINT8: 1,
  INT8: 1,
  UINT16: 2,
  INT16: 2,
  UINT32: 4,
  INT32: 4,
  FLOAT: 4,
  DOUBLE: 8,
  BOOL: 1,
});

interface Rs422Row {
  dataType: string;
  byteCount: string | number;
  valueRange?: string;
  byteSequence?: string;
}
export function positiveByteCount(value: string | number): number | null {
  const number = Number(value);
  const integer = Math.floor(number);
  return Number.isFinite(number) && integer > 0 ? integer : null;
}

/** One pass; fixed types, then existing STRING count, then quoted range. */
export function normalizeRs422Fields<T extends Rs422Row>(rows: readonly T[]) {
  let total = 0;
  const fields = rows.map((source) => {
    const field = { ...source, byteSequence: '' };
    const type = source.dataType?.toUpperCase();
    let length: number | null = RS422_TYPE_BYTES[type] ?? null;
    if (type === 'STRING') {
      length = positiveByteCount(source.byteCount);
      if (length === null) {
        const match = source.valueRange?.match(/"([^"]+)"/);
        length = match?.[1]?.length ?? null;
      }
    }
    if (length !== null) field.byteCount = length;
    else length = positiveByteCount(source.byteCount);
    if (length === null) {
      field.byteCount = '';
      return field;
    }
    const end = total + length - 1;
    field.byteSequence = total === end ? String(total) : `${total}-${end}`;
    total = end + 1;
    return field;
  });
  return { fields, total };
}

export function rs422Locks(options: {
  deviceMode?: boolean;
  senderEditable?: boolean;
  receiverEditable?: boolean;
}) {
  return {
    senderLocked: !!options.deviceMode || options.senderEditable === false,
    receiverLocked: !!options.deviceMode || options.receiverEditable === false,
  };
}

export function resolveRs422Label(
  dictionary: readonly { value: unknown; label: string }[] | undefined,
  value: string,
  fallbackLabel = ''
) {
  if (!value) return '';
  return dictionary?.find((item) => item.value === value)?.label ?? (fallbackLabel || value);
}
