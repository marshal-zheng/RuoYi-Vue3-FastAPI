import type { MockDictData } from '../types';
import { MOCK_STATUS } from '../_shared';

export const mockDicts = [
  {
    id: 1,
    dictType: 'sys_user_sex',
    dictValue: '0',
    dictLabel: '男',
    status: MOCK_STATUS.normal,
    remark: null,
    remarkText: '',
  },
  {
    id: 2,
    dictType: 'sys_user_sex',
    dictValue: '1',
    dictLabel: '女',
    status: MOCK_STATUS.normal,
    remark: null,
    remarkText: '',
  },
  {
    id: 3,
    dictType: 'sys_user_sex',
    dictValue: '2',
    dictLabel: '未知',
    status: MOCK_STATUS.normal,
    remark: null,
    remarkText: '',
  },
  {
    id: 4,
    dictType: 'sys_normal_disable',
    dictValue: '0',
    dictLabel: '正常',
    status: MOCK_STATUS.normal,
    remark: null,
    remarkText: '',
  },
  {
    id: 5,
    dictType: 'sys_normal_disable',
    dictValue: '1',
    dictLabel: '停用',
    status: MOCK_STATUS.normal,
    remark: null,
    remarkText: '',
  },
] satisfies MockDictData[];
