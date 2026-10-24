import request from '@/utils/request';

interface MemoryInfo {
  total: string;
  used: string;
  free: string;
  usage: number;
}
export interface ServerInfo {
  cpu: { cpuNum: number; used: number; sys: number; free: number };
  mem: MemoryInfo;
  py: MemoryInfo & {
    name: string;
    version: string;
    startTime: string;
    runTime: string;
    home: string;
  };
  sys: {
    computerIp: string;
    computerName: string;
    osArch: string;
    osName: string;
    userDir: string;
  };
  sysFiles: {
    dirName: string;
    sysTypeName: string;
    typeName: string;
    total: string;
    used: string;
    free: string;
    usage: string;
  }[];
}

// 获取服务信息
export function getServer() {
  return request<ServerInfo>({
    url: '/monitor/server',
    method: 'get',
    feedback: { mode: 'silent' },
  });
}
