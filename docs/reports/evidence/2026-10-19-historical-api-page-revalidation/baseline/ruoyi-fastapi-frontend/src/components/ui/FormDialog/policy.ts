export type FormColumns = 1 | 2 | 3;

// Product layout policy; control height and vertical rhythm belong to ZXUI density.
export const formLayoutPolicy = {
  dialogSize: { 1: 'md', 2: 'lg', 3: 'xl' },
  labelWidth: '100px',
  columnGap: '20px',
  minColumnWidth: '280px',
} as const;
