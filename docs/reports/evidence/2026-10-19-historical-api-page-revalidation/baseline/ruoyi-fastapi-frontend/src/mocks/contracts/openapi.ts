import type {
  CurrentUserModel,
  DeptModel,
  DeviceModel,
  DictDataModel,
  GetLoginUserInfoGetInfoGetResponse,
  GetSystemProjectListProjectListGetResponse,
  LoginLoginPostResponse,
  MenuModel,
  PageResponseModel,
  ProjectModel,
  ProjectTopologyModel,
  ProjectVersionModel,
  RoleModel,
  UserInfoModel,
} from '@/api/_generated/types.gen';

export type RequireOpenApiFields<T, K extends keyof T> = Omit<T, K> & {
  [P in K]-?: NonNullable<T[P]>;
};

export type MockOpenApiAccountUser = RequireOpenApiFields<
  UserInfoModel,
  'userId' | 'userName' | 'nickName' | 'status'
>;

export type MockOpenApiRole = RequireOpenApiFields<
  RoleModel,
  'roleId' | 'roleKey' | 'roleName' | 'status'
>;

export type MockOpenApiMenu = RequireOpenApiFields<
  MenuModel,
  'menuId' | 'parentId' | 'menuName' | 'menuType' | 'status'
>;

export type MockOpenApiDictData = RequireOpenApiFields<
  DictDataModel,
  'dictCode' | 'dictType' | 'dictValue' | 'dictLabel' | 'status'
>;

export type MockOpenApiDepartment = RequireOpenApiFields<
  DeptModel,
  'deptId' | 'parentId' | 'deptName' | 'status'
>;

export type MockOpenApiDevice = RequireOpenApiFields<DeviceModel, 'deviceId' | 'deviceName'>;

export type MockOpenApiProject = RequireOpenApiFields<
  ProjectModel,
  'projectId' | 'projectName' | 'createTime'
> & {
  status: string;
};

export type MockOpenApiProjectVersion = RequireOpenApiFields<
  ProjectVersionModel,
  'versionId' | 'projectId' | 'versionName' | 'status' | 'createTime'
> & {
  locked: boolean;
};

export type MockOpenApiTopology = Pick<
  RequireOpenApiFields<ProjectTopologyModel, 'projectId' | 'versionId'>,
  'projectId' | 'versionId'
> & {
  id: string;
  graph: ProjectTopologyModel['topologyData'];
  updateTime: string;
};

export type MockLoginResponse = LoginLoginPostResponse & {
  token: string;
  csrfToken?: string;
  csrf_token?: string;
};

export type MockCurrentUserResponse = GetLoginUserInfoGetInfoGetResponse & {
  user: NonNullable<CurrentUserModel['user']>;
  isDefaultModifyPwd: boolean;
  isPasswordExpired: boolean;
};

export type MockOpenApiPage<T> = Omit<PageResponseModel, 'items'> & {
  items: T[];
};

export type MockProjectListResponse = GetSystemProjectListProjectListGetResponse & {
  items: MockProjectResponse[];
};

export type MockProjectResponse = MockOpenApiProject & {
  projectCode: string;
  projectDesc: string;
  description: string;
  owner: string;
  createBy: string;
  updateBy: string;
};

export type MockProjectVersionResponse = MockOpenApiProjectVersion & {
  versionNumber: string;
  description: string;
  isLocked: '0' | '1';
  createBy: string;
  updateBy: string;
};

export type MockTopologyResponse = RequireOpenApiFields<
  ProjectTopologyModel,
  'projectId' | 'topologyData'
> & {
  topologyId: number;
  graph: ProjectTopologyModel['topologyData'];
};
