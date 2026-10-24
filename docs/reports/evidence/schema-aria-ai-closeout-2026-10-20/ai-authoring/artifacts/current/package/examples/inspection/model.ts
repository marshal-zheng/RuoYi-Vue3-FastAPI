import type { Values } from '@zxio/schema-form'

export interface Measurement {
  id: string
  name: string
  reading: number | null
}
export interface Attachment {
  id: string
  name: string
  url: string
}
export interface Inspection {
  title: string
  equipmentId: number | null
  result: 'normal' | 'abnormal'
  explanation: string
  tags: string[]
  measurements: Measurement[]
  attachments: Attachment[]
}
export interface InspectionDto {
  recordId: string
  deviceId: number
  payload: Omit<Inspection, 'equipmentId'>
}

export function draft(record = 'A'): Values {
  if (record === 'new')
    return {
      title: '',
      equipmentId: null,
      result: 'normal',
      explanation: '',
      tags: [],
      measurements: [{ id: 'temperature', name: '温度', reading: null }],
      attachments: [],
    }
  return {
    title: `日常巡检 ${record}`,
    equipmentId: record === 'A' ? 0 : 2,
    result: 'normal',
    explanation: '',
    tags: ['日检'],
    measurements: [{ id: 'temperature', name: '温度', reading: 0 }],
    attachments: [],
  }
}
export function decode(values: Values): Inspection {
  if (typeof values.title !== 'string' || !values.title.trim())
    throw new Error('请输入记录名称')
  if (
    typeof values.equipmentId !== 'number' ||
    !Number.isFinite(values.equipmentId)
  )
    throw new Error('请选择设备')
  if (!['normal', 'abnormal'].includes(String(values.result)))
    throw new Error('请选择检查结果')
  if (typeof values.explanation !== 'string') throw new Error('说明格式错误')
  if (values.result === 'abnormal' && !values.explanation.trim())
    throw new Error('异常结果必须填写说明')
  if (
    !Array.isArray(values.tags) ||
    !values.tags.every((tag) => typeof tag === 'string')
  )
    throw new Error('标签格式错误')
  if (!Array.isArray(values.measurements) || !values.measurements.length)
    throw new Error('至少填写一项检查项')
  const ids = new Set<string>()
  for (const item of values.measurements) {
    if (
      !item ||
      Array.isArray(item) ||
      typeof item !== 'object' ||
      typeof item.id !== 'string' ||
      !item.id ||
      ids.has(item.id) ||
      typeof item.name !== 'string' ||
      !item.name.trim() ||
      typeof item.reading !== 'number' ||
      !Number.isFinite(item.reading)
    )
      throw new Error('检查项名称与读数必填，行标识必须唯一')
    ids.add(item.id)
  }
  if (
    !Array.isArray(values.attachments) ||
    !values.attachments.every(
      (file) =>
        file &&
        !Array.isArray(file) &&
        typeof file === 'object' &&
        typeof file.id === 'string' &&
        typeof file.name === 'string' &&
        typeof file.url === 'string'
    )
  )
    throw new Error('附件必须上传完成')
  return values as unknown as Inspection
}
export function toDto(values: Values, recordId: string): InspectionDto {
  const { equipmentId, ...payload } = decode(values)
  return { recordId, deviceId: equipmentId!, payload }
}
