import type { MockDepartment } from '../types';
import { MOCK_DEPT_IDS, MOCK_STATUS } from '../_shared';

export const mockDepartments = [
  {
    deptId: MOCK_DEPT_IDS.root,
    parentId: 0,
    deptName: '若依科技',
    status: MOCK_STATUS.normal,
  },
  {
    deptId: MOCK_DEPT_IDS.platform,
    parentId: MOCK_DEPT_IDS.root,
    deptName: '平台研发部',
    status: MOCK_STATUS.normal,
  },
  {
    deptId: MOCK_DEPT_IDS.delivery,
    parentId: MOCK_DEPT_IDS.root,
    deptName: '交付演示部',
    status: MOCK_STATUS.normal,
  },
] satisfies MockDepartment[];
