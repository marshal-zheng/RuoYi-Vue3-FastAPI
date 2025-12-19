// @ts-nocheck
import { fakerZH_CN as faker } from '@faker-js/faker'

export interface MockUser {
  userId: number
  deptId: number
  userName: string
  nickName: string
  email: string
  phonenumber: string
  sex: '0' | '1' | '2'
  avatar: string
  status: '0' | '1'
  delFlag: '0'
  loginIp: string
  loginDate: string
  createBy: string
  createTime: string
  updateBy: string | null
  updateTime: string | null
  remark: string
}

export interface MockAccountConfig {
  username: string
  password: string
  roles?: string[]
  permissions?: string[]
  name?: string
  introduction?: string
  avatar?: string
  userOverrides?: Partial<MockUser>
}

export interface MockAccountInfo {
  roles: string[]
  introduction: string
  avatar: string
  name: string
  user: MockUser
  permissions: string[]
}

export interface AccountCollections {
  credentials: Record<string, { password: string; token: string }>
  accountsByToken: Record<string, MockAccountInfo>
}

let userSeed = 1

function nextUserId() {
  return userSeed++
}

function formatDateTime(date: Date): string {
  const pad = (value: number) => value.toString().padStart(2, '0')
  const year = date.getFullYear()
  const month = pad(date.getMonth() + 1)
  const day = pad(date.getDate())
  const hours = pad(date.getHours())
  const minutes = pad(date.getMinutes())
  const seconds = pad(date.getSeconds())
  return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`
}

function randomPhone(): string {
  return faker.phone.number('1##########')
}

function randomDateTime(): string {
  return formatDateTime(faker.date.recent({ days: 30 }))
}

export function resetUserSeed() {
  userSeed = 1
}

export function createUser(overrides: Partial<MockUser> = {}): MockUser {
  const nickName = overrides.nickName ?? faker.person.fullName()
  const userName =
    overrides.userName ??
    faker.internet
      .userName({ firstName: nickName })
      .replace(/[^a-zA-Z0-9]/g, '')
      .toLowerCase()

  return {
    userId: overrides.userId ?? nextUserId(),
    deptId: overrides.deptId ?? faker.number.int({ min: 100, max: 199 }),
    userName,
    nickName,
    email: overrides.email ?? faker.internet.email({ firstName: nickName }),
    phonenumber: overrides.phonenumber ?? randomPhone(),
    sex: overrides.sex ?? faker.helpers.arrayElement(['0', '1', '2']),
    avatar: overrides.avatar ?? '',
    status: overrides.status ?? faker.helpers.arrayElement(['0', '1']),
    delFlag: '0',
    loginIp: overrides.loginIp ?? faker.internet.ipv4(),
    loginDate: overrides.loginDate ?? randomDateTime(),
    createBy: overrides.createBy ?? faker.helpers.arrayElement(['admin', 'system']),
    createTime: overrides.createTime ?? randomDateTime(),
    updateBy:
      overrides.updateBy ??
      (faker.datatype.boolean()
        ? faker.helpers.arrayElement(['admin', 'editor'])
        : null),
    updateTime:
      overrides.updateTime ??
      (faker.datatype.boolean() ? randomDateTime() : null),
    remark: overrides.remark ?? faker.lorem.sentence({ min: 4, max: 12 }),
  }
}

export function createUserList(
  count: number,
  overrides?: (index: number) => Partial<MockUser>
): MockUser[] {
  resetUserSeed()
  return Array.from({ length: count }, (_, idx) => {
    const userOverrides = overrides ? overrides(idx) : {}
    return createUser({
      userId: userOverrides?.userId ?? nextUserId(),
      ...userOverrides
    })
  })
}

export function buildAccountCollections(
  configs: MockAccountConfig[]
): AccountCollections {
  const now = Date.now()
  const credentials: AccountCollections['credentials'] = {}
  const accountsByToken: AccountCollections['accountsByToken'] = {}

  configs.forEach((config, index) => {
    const baseUser = createUser({
      userName: config.username,
      nickName: config.name ?? faker.person.fullName(),
      userId: config.userOverrides?.userId ?? nextUserId(),
      ...config.userOverrides
    })

    const accountInfo: MockAccountInfo = {
      roles: config.roles ?? ['user'],
      introduction:
        config.introduction ?? `Mock account for ${baseUser.nickName}`,
      avatar:
        config.avatar ??
        faker.image.avatarGitHub() ??
        `https://api.dicebear.com/7.x/initials/svg?seed=${encodeURIComponent(
          baseUser.nickName
        )}`,
      name: config.name ?? baseUser.nickName,
      user: baseUser,
      permissions: config.permissions ?? []
    }

    const token = `mock-token-${config.username}-${now}-${index}`

    credentials[config.username] = {
      password: config.password,
      token
    }

    accountsByToken[token] = accountInfo
  })

  return {
    credentials,
    accountsByToken
  }
}
