# 数据库迁移最佳实践指南

本文档记录了关于 Alembic 数据库迁移的常见问题、最佳实践和解决方案。

---

## 问题 1：alembic/versions 文件夹里都是什么？有什么用？

### 回答

`ruoyi-fastapi-backend/alembic/versions` 文件夹里存放的是**数据库迁移脚本**（migration scripts），这是 Alembic 数据库版本管理工具的核心部分。

#### 这些文件是什么？

每个文件代表一次数据库结构的变更，包含：
- **升级操作**（upgrade）：如何将数据库从旧版本升级到新版本
- **降级操作**（downgrade）：如何回滚到之前的版本

#### 主要作用

1. **版本控制**：像 Git 管理代码一样管理数据库结构变更
2. **自动化部署**：在不同环境（开发/测试/生产）中自动同步数据库结构
3. **团队协作**：多人开发时避免数据库结构冲突
4. **可追溯性**：记录每次数据库变更的历史

#### 文件命名规则

```
{revision}_{slug}.py
```

例如：
- `20260127_audit_log_table.py` - 2026年1月27日创建的审计日志表迁移
- `20260127_performance_indexes.py` - 性能索引优化迁移
- `20260123_120000_init_schema.py` - 初始化数据库架构

#### 典型使用场景

```bash
# 生成新的迁移脚本（检测模型变更）
alembic revision --autogenerate -m "add user email field"

# 升级到最新版本
alembic upgrade head

# 回滚一个版本
alembic downgrade -1

# 查看当前版本
alembic current

# 查看迁移历史
alembic history
```

---

## 问题 2：为什么有这么多日期开头的文件？到底怎么用？

### 回答

#### 为什么这么多日期开头的文件？

项目配置了**自动日期命名**，看 `alembic.ini` 里这行：

```ini
file_template = %%(year)d%%(month).2d%%(day).2d_%%(hour).2d%%(minute).2d%%(second).2d_%%(slug)s
```

这意味着每次生成迁移文件时，会自动加上**创建时间戳**，格式是：`YYYYMMDD_HHMMSS_描述`

**好处**：
- 一眼看出迁移的创建顺序
- 避免多人开发时文件名冲突
- 便于追溯历史变更

#### 实际使用方法

##### 1. 日常开发 - 修改数据库结构

```bash
cd ruoyi-fastapi-backend

# 1. 修改你的 ORM 模型（entity/do/*.py）
# 例如：给 User 模型加个 email 字段

# 2. 自动生成迁移脚本
alembic revision --autogenerate -m "add_user_email"
# 会生成：20260127_153045_add_user_email.py

# 3. 检查生成的文件（重要！）
# 打开文件确认 upgrade() 和 downgrade() 逻辑正确

# 4. 应用到数据库
alembic upgrade head
```

##### 2. 查看当前状态

```bash
# 查看当前数据库版本
alembic current

# 查看所有迁移历史
alembic history --verbose

# 查看待执行的迁移
alembic history --indicate-current
```

##### 3. 部署到生产环境

```bash
# 在生产服务器上
cd ruoyi-fastapi-backend
source venv/bin/activate

# 应用所有新迁移
alembic upgrade head

# 如果出问题，回滚一个版本
alembic downgrade -1
```

##### 4. 团队协作场景

```bash
# 同事提交了新的迁移文件，你拉取代码后：
git pull

# 应用新的迁移
alembic upgrade head
```

---

## 问题 3：开发模式下什么时候生成迁移文件？别人怎么知道要执行迁移？

### 回答

#### 什么时候生成迁移文件？

**触发时机（只有一个）**：当你修改了数据库表结构时，就需要生成迁移文件。

##### ✅ 需要生成迁移的情况

```python
# 场景 1：给表加字段
class User(Base):
    __tablename__ = "sys_user"
    user_id = Column(BigInteger, primary_key=True)
    user_name = Column(String(30))
    email = Column(String(50))      # ← 新加的字段
    phone = Column(String(11))      # ← 新加的字段

# 场景 2：创建新表
class AuditLog(Base):               # ← 全新的表
    __tablename__ = "sys_audit_log"
    log_id = Column(BigInteger, primary_key=True)
    # ...

# 场景 3：修改字段类型
class User(Base):
    user_name = Column(String(50))  # 原来是 String(30)，改成 50

# 场景 4：添加索引
class User(Base):
    email = Column(String(50), index=True)  # ← 加了索引

# 场景 5：删除字段
# 删除了 old_field 字段
```

##### ❌ 不需要生成迁移的情况

```python
# 只改业务逻辑代码，不改数据库结构
# - 修改 service.py
# - 修改 controller.py
# - 修改 dao.py 的查询逻辑
# - 修改前端代码
# 这些都不需要生成迁移！
```

#### 别人怎么知道要执行迁移？

##### 方案 A：自动检测（推荐）

在项目启动时自动检查并提示：

```python
# ruoyi-fastapi-backend/app.py
from alembic.config import Config
from alembic import command
from alembic.script import ScriptDirectory
from alembic.runtime.migration import MigrationContext

def check_migrations():
    """检查是否有待执行的迁移"""
    alembic_cfg = Config("alembic.ini")
    script = ScriptDirectory.from_config(alembic_cfg)
    
    # 获取当前数据库版本
    with engine.begin() as connection:
        context = MigrationContext.configure(connection)
        current_rev = context.get_current_revision()
    
    # 获取最新版本
    head_rev = script.get_current_head()
    
    if current_rev != head_rev:
        print("⚠️  警告：数据库需要迁移！")
        print(f"   当前版本: {current_rev or '未初始化'}")
        print(f"   最新版本: {head_rev}")
        print("   请执行: alembic upgrade head")
        return False
    
    print("✅ 数据库版本已是最新")
    return True

# 在应用启动时调用
if __name__ == "__main__":
    check_migrations()
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

##### 方案 B：Git Hook（自动化）

团队成员 `git pull` 后自动提示：

```bash
# .git/hooks/post-merge
#!/bin/bash

# 检查是否有新的迁移文件
if git diff-tree -r --name-only --no-commit-id ORIG_HEAD HEAD | grep -q "alembic/versions/"; then
    echo ""
    echo "🔔 检测到新的数据库迁移文件！"
    echo "📋 请执行以下命令更新数据库："
    echo ""
    echo "    cd ruoyi-fastapi-backend"
    echo "    alembic upgrade head"
    echo ""
fi
```

##### 方案 C：README 提示（最简单）

在项目 README 中明确说明：

```markdown
## 开发流程

### 拉取代码后必做的事

1. 拉取最新代码
   ```bash
   git pull origin main
   ```

2. **检查是否有数据库迁移**
   ```bash
   cd ruoyi-fastapi-backend
   alembic current  # 查看当前版本
   alembic history  # 查看历史
   ```

3. **如果有新迁移，执行它**
   ```bash
   alembic upgrade head
   ```

4. 启动项目
   ```bash
   python app.py
   ```
```

#### 完整的开发场景演示

##### 场景：开发者 A 添加用户邮箱功能

**第 1 步：开发者 A 修改代码**

```python
# module_admin/entity/do/user_do.py
class User(Base):
    __tablename__ = "sys_user"
    user_id = Column(BigInteger, primary_key=True)
    user_name = Column(String(30))
    email = Column(String(50))      # ← 新加的
```

**第 2 步：开发者 A 生成迁移**

```bash
cd ruoyi-fastapi-backend

# 生成迁移文件
alembic revision --autogenerate -m "add_user_email"
# 生成：alembic/versions/abc123_add_user_email.py

# 查看生成的文件（确认正确）
cat alembic/versions/abc123_add_user_email.py

# 应用到本地数据库
alembic upgrade head

# 测试功能正常
python app.py
```

**第 3 步：开发者 A 提交代码**

```bash
git add module_admin/entity/do/user_do.py
git add alembic/versions/abc123_add_user_email.py  # ← 迁移文件也要提交！
git commit -m "feat: add user email field"
git push origin feature/user-email
```

**第 4 步：开发者 B 拉取代码**

```bash
# 开发者 B 第二天上班
git pull origin main

# 看到提示（如果配置了 Git Hook）
# 🔔 检测到新的数据库迁移文件！
# 📋 请执行: alembic upgrade head

# 开发者 B 执行迁移
cd ruoyi-fastapi-backend
alembic upgrade head
# 输出：
# INFO  [alembic.runtime.migration] Running upgrade -> abc123, add_user_email

# 启动项目，一切正常
python app.py
```

#### 常见问题

**Q1：我忘记执行迁移会怎样？**

```python
# 启动项目时会报错
sqlalchemy.exc.OperationalError: (pymysql.err.OperationalError) 
(1054, "Unknown column 'email' in 'field list'")
```

**解决**：执行 `alembic upgrade head`

**Q2：两个人同时改了数据库怎么办？**

```bash
# 开发者 A 生成：abc123_add_email.py
# 开发者 B 生成：def456_add_phone.py

# 合并时会有两个迁移文件
# 方案 1：保留两个文件（推荐）
alembic/versions/
├── abc123_add_email.py
└── def456_add_phone.py

# Alembic 会按顺序执行两个

# 方案 2：合并成一个文件
# 手动合并后删除其中一个
```

**Q3：怎么知道当前数据库版本？**

```bash
# 查看当前版本
alembic current
# 输出：abc123 (head)

# 查看历史
alembic history --verbose

# 查看待执行的迁移
alembic history --indicate-current
```

---

## 问题 4：AI 开发时会生成很多迁移文件，怎么处理？

### 问题现象

在使用 AI 辅助开发时，一个功能的开发过程中可能会生成多个迁移文件：

```
alembic/versions/
├── 20260127_101523_add_user_email.py
├── 20260127_102034_add_user_phone.py
├── 20260127_103145_fix_email_type.py
├── 20260127_104256_add_user_avatar.py
├── 20260127_105367_add_user_bio.py
└── 20260127_110478_fix_phone_length.py
```

**问题**：
- 文件太多，看不懂
- 生产环境要执行 6 次
- 回滚复杂
- 代码审查困难

### 解决方案：Squash Migrations（压缩迁移）

#### 核心原则

**开发阶段可以有多个临时迁移文件，但合并到主分支前必须压缩成一个。**

#### 业界实践案例

##### Airbnb 的做法

```
开发分支（feature/user-profile）：
├── abc123_add_email.py          # AI 生成的
├── def456_add_phone.py          # AI 又生成的
├── ghi789_fix_email_length.py  # 修 bug 又生成的
└── jkl012_add_avatar.py         # 又加功能又生成的

合并前压缩成：
└── v1.2.0_user_profile_enhancement.py  # 只有一个！
```

##### Django 官方推荐

Django 有个命令专门做这个：`python manage.py squashmigrations`

Alembic 虽然没有自动命令，但思路一样。

#### 具体操作方法

##### 方法 1：手动合并（推荐，最可控）

```bash
# 场景：AI 帮你开发用户功能，生成了 4 个迁移文件

# 1. 查看当前迁移
ls alembic/versions/
# abc123_add_email.py
# def456_add_phone.py
# ghi789_fix_email_length.py
# jkl012_add_avatar.py

# 2. 回滚到功能开始前
alembic downgrade <开始前的版本>

# 3. 删除这 4 个临时文件
rm alembic/versions/abc123_add_email.py
rm alembic/versions/def456_add_phone.py
rm alembic/versions/ghi789_fix_email_length.py
rm alembic/versions/jkl012_add_avatar.py

# 4. 重新生成一个完整的迁移
alembic revision --autogenerate -m "user_profile_enhancement"
# 生成：xyz999_user_profile_enhancement.py

# 5. 应用新迁移
alembic upgrade head

# 6. 测试功能正常
python app.py

# 7. 提交到 Git
git add alembic/versions/xyz999_user_profile_enhancement.py
git commit -m "feat: user profile enhancement"
```

##### 方法 2：手动合并内容（适合复杂场景）

```python
# 1. 创建一个新的迁移文件
alembic revision -m "user_profile_enhancement" --rev-id="v1.2.0"

# 2. 打开新文件，手动复制 4 个文件的 upgrade() 内容
def upgrade():
    # 从 abc123_add_email.py 复制
    op.add_column('sys_user', sa.Column('email', sa.String(50)))
    
    # 从 def456_add_phone.py 复制
    op.add_column('sys_user', sa.Column('phone', sa.String(11)))
    
    # 从 ghi789_fix_email_length.py 复制
    op.alter_column('sys_user', 'email', type_=sa.String(100))
    
    # 从 jkl012_add_avatar.py 复制
    op.add_column('sys_user', sa.Column('avatar', sa.String(255)))

def downgrade():
    # 反向操作
    op.drop_column('sys_user', 'avatar')
    op.alter_column('sys_user', 'email', type_=sa.String(50))
    op.drop_column('sys_user', 'phone')
    op.drop_column('sys_user', 'email')

# 3. 删除旧的 4 个文件
# 4. 测试新迁移
```

#### AI 辅助开发的最佳实践

##### 推荐工作流

```bash
# 1. 开发阶段：让 AI 随便生成
# AI 生成了 5 个迁移文件？没关系，先不管

# 2. 本地测试：应用所有迁移
alembic upgrade head

# 3. 功能测试通过后：压缩迁移
# 方案 A：回滚 + 重新生成（简单）
alembic downgrade <起点>
rm alembic/versions/临时文件*.py
alembic revision --autogenerate -m "feature_name"

# 方案 B：手动合并（精确）
# 创建新文件，复制所有 upgrade() 内容

# 4. 提交到 Git：只提交最终的一个文件
git add alembic/versions/v1.2.0_feature_name.py
git commit -m "feat: feature name"
```

#### 实际案例对比

##### ❌ 不好的做法（AI 生成一堆）

```
alembic/versions/
├── 20260127_101523_add_user_email.py
├── 20260127_102034_add_user_phone.py
├── 20260127_103145_fix_email_type.py
├── 20260127_104256_add_user_avatar.py
├── 20260127_105367_add_user_bio.py
└── 20260127_110478_fix_phone_length.py

# 问题：
# - 文件太多，看不懂
# - 生产环境要执行 6 次
# - 回滚复杂
# - 代码审查困难
```

##### ✅ 好的做法（压缩后）

```
alembic/versions/
└── v1.2.0_user_profile_system.py

# 优点：
# - 一个文件，清晰明了
# - 生产环境执行一次
# - 回滚简单
# - 代码审查容易
```

#### 顶级开发者的习惯

##### Google 的做法

1. **功能分支**：随便生成多少迁移都行
2. **Code Review 前**：必须压缩成一个
3. **合并到 main**：只有一个干净的迁移文件

##### Stripe 的做法

1. 开发时用 `dev_` 前缀标记临时迁移
2. 发布前删除所有 `dev_` 开头的文件
3. 重新生成正式迁移

```bash
# 开发时
alembic revision -m "dev_test_email"
alembic revision -m "dev_test_phone"

# 发布前
rm alembic/versions/dev_*.py
alembic revision --autogenerate -m "v1.2.0_user_profile"
```

---

## 最佳实践总结

### 开发者职责

1. **修改 ORM 模型后**，立即生成迁移
2. **提交代码时**，必须包含迁移文件
3. **拉取代码后**，先执行 `alembic upgrade head`
4. **功能完成后**，压缩多个临时迁移为一个

### 团队约定

1. 在 README 中明确说明迁移流程
2. 配置 Git Hook 自动提示
3. 在 app.py 启动时检查版本
4. 定期清理合并迁移文件（发版时）

### 核心原则

- **谁改数据库，谁生成迁移**
- **迁移文件必须提交到 Git**
- **拉代码后必须执行迁移**
- **开发时随意，提交前压缩**

### 推荐的工作流

```bash
# 1. 开发阶段：让 AI 随便生成迁移
# 生成了多个文件？没关系

# 2. 本地测试：应用所有迁移
alembic upgrade head

# 3. 功能完成：压缩迁移
alembic downgrade <起点>
rm alembic/versions/临时*.py
alembic revision --autogenerate -m "v1.x.0_feature_name"

# 4. 提交代码：只提交最终文件
git add alembic/versions/v1.x.0_feature_name.py
git commit -m "feat: feature description"
```

---

## 相关文档

- [Alembic 官方文档](https://alembic.sqlalchemy.org/)
- [alembic/versions/README.md](../ruoyi-fastapi-backend/alembic/versions/README.md)
- [数据库迁移现代化设计](../.kiro/specs/database-migration-modernization/design.md)
