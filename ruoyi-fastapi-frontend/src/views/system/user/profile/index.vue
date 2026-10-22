<template>
  <div class="app-container">
    <el-row :gutter="20">
      <el-col :span="6" :xs="24">
        <el-card class="box-card">
          <template v-slot:header>
            <div class="flow-root">
              <span>个人信息</span>
            </div>
          </template>
          <div>
            <div class="text-center">
              <userAvatar />
            </div>
            <dl class="profile-details">
              <div>
                <dt><svg-icon icon-class="user" />用户名称</dt>
                <dd>{{ state.user.userName }}</dd>
              </div>
              <div>
                <dt><svg-icon icon-class="phone" />手机号码</dt>
                <dd>{{ state.user.phonenumber }}</dd>
              </div>
              <div>
                <dt><svg-icon icon-class="email" />用户邮箱</dt>
                <dd>{{ state.user.email }}</dd>
              </div>
              <div>
                <dt><svg-icon icon-class="tree" />所属部门</dt>
                <dd v-if="state.user.dept">
                  {{ state.user.dept.deptName }}{{ state.postGroup ? ' / ' + state.postGroup : '' }}
                </dd>
              </div>
              <div>
                <dt><svg-icon icon-class="peoples" />所属角色</dt>
                <dd>{{ state.roleGroup }}</dd>
              </div>
              <div>
                <dt><svg-icon icon-class="date" />创建日期</dt>
                <dd>{{ parseTime(state.user.createTime) }}</dd>
              </div>
            </dl>
          </div>
        </el-card>
      </el-col>
      <el-col :span="18" :xs="24">
        <el-card>
          <template v-slot:header>
            <div class="flow-root">
              <span>基本资料</span>
            </div>
          </template>
          <el-tabs v-model="activeTab">
            <el-tab-pane label="基本资料" name="userinfo">
              <userInfo :user="state.user" />
            </el-tab-pane>
            <el-tab-pane label="修改密码" name="resetPwd">
              <resetPwd />
            </el-tab-pane>
          </el-tabs>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup name="Profile">
import userAvatar from './userAvatar';
import userInfo from './userInfo';
import resetPwd from './resetPwd';
import { getUserProfile } from '@/api/system/user';

const activeTab = ref('userinfo');
const state = reactive({
  user: {},
  roleGroup: '',
  postGroup: '',
});

function getUser() {
  getUserProfile().then((response) => {
    state.user = response.data;
    state.roleGroup = response.roleGroup;
    state.postGroup = response.postGroup;
  });
}

getUser();
</script>

<style scoped>
.profile-details {
  display: grid;
  gap: 16px;
  margin: 20px 0 0;
}

.profile-details dt {
  display: flex;
  align-items: center;
  gap: 6px;
}

.profile-details dd {
  margin: 4px 0 0;
  overflow-wrap: anywhere;
}
</style>
