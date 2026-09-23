# 真实页面验收中的数据契约修复

日期：2026-09-22。主线程在真实业务页面发现并明确授权收敛修复。修复者为 input/generator 实施代理，这部分需要其他代理交叉复核。没有修改认证、安全配置或伪造字典选项，没有发起新的登录。

## 参数字典并发

`ConfigList` 的 `useDict('sys_yes_no')` 与 `DictSelect` 的 `getDicts('sys_yes_no')` 会同时读取同一 URL。Hook 局部 pending map 无法覆盖直接 API 消费者，真实 `@zxio/http` 默认重复请求取消器使前一个请求失败，Hook 的 ref 保持空数组。字典管理页面真实数据仍有是/Y、否/N，不是 seed 缺失。

`src/api/system/dict/data.ts:30` 在 API 边界只共用正在进行的请求，成功/失败均删除 pending，后续加载仍获取最新数据。`data.test.ts` 使用真实 HTTP client/adapter，先复现 Hook 与 selector 并发时空选项，再证实修复后两方共享结果，失败可重试，不做固定选项 fallback。

## 菜单集合

菜单 list 与 treeselect 是 `{ items }` 集合契约。`src/api/system/menu.ts` 增加明确返回类型；`MenuList.vue`、`MenuDrawer.vue` 与 `tool/gen/genInfoForm.vue` 从 items 建树。原抽屉把整个集合对象赋给 children 导致不可迭代异常，列表则把集合对象交 handleTree 得到空列表。

## 角色用户 join 行

`UserRepository.paginate_{allocated,unallocated}_by_role` 查询 `select(UserDO, DeptDO)`，PageUtil 返回每行 `[user, dept]`，部门可为 null。`RoleService` 原先将数组按 `**row` 展开，真实服务500日志为 `argument after ** must be a mapping, not list`。两方法现明确构造 `UserInfoModel(**row[0], dept=row[1])`，保留分页和部门数据，不加猜测多格式回退。

## 验证

- `vitest run src/api/system/dict/data.test.ts src/utils/dict.test.ts tests/unit/components/MenuCollection.test.ts`：3文件6项通过。
- `venv/bin/pytest tests/unit/services/test_role_service.py modules/system/tests/test_role_read_queries.py -q --no-cov`：14项通过，含两种 allocation 的真实 join 形状、null dept、分页保留。
- `node scripts/check-ui-standards.mjs --strict --format=summary`：496文件0违规。
- 浏览器最终重验另存 browser 目录。认证 transient401 在依赖冻结后的18次主题明暗弹框开关中未复现；没有证据确认根因，未修改 auth。早期 HMR/会话轮换仅为待验证假设，不能写成已证实原因。
