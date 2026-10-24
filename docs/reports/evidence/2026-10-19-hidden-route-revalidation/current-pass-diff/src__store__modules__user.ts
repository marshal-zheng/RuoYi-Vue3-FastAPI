--- before/src/store/modules/user.ts
+++ after/src/store/modules/user.ts
@@ -1,5 +1,6 @@
 import { login, logout, getInfo } from '@/api/login';
 import { defineStore } from 'pinia';
+import { AbortError } from '@zxio/http';
 import {
   clearSecurityTokens,
   getSecuritySessionVersion,
@@ -106,33 +107,25 @@
       }
     },
     // 获取用户信息
-    getInfo() {
-      return new Promise((resolve, reject) => {
-        getInfo()
-          .then((res) => {
-            const user = res.user;
-            let avatar = user.avatar || '';
-            if (!isHttp(avatar)) {
-              avatar = isEmpty(avatar) ? defAva : import.meta.env.VITE_APP_BASE_API + avatar;
-            }
-            if (res.roles && res.roles.length > 0) {
-              // 验证返回的roles是否是一个非空数组
-              this.roles = res.roles;
-              this.permissions = res.permissions;
-            } else {
-              this.roles = ['ROLE_DEFAULT'];
-            }
-            this.id = user.userId;
-            this.name = user.userName;
-            this.nickName = user.nickName;
-            this.avatar = avatar;
-            setQuerySession(this.id, this.roles, this.permissions);
-            resolve(res);
-          })
-          .catch((error) => {
-            reject(error);
-          });
-      });
+    async getInfo() {
+      const sessionVersion = getSecuritySessionVersion();
+      const res = await getInfo();
+      if (sessionVersion !== getSecuritySessionVersion()) {
+        throw new AbortError({ message: '会话已切换，忽略旧的用户信息' });
+      }
+      const user = res.user;
+      let avatar = user.avatar || '';
+      if (!isHttp(avatar)) {
+        avatar = isEmpty(avatar) ? defAva : import.meta.env.VITE_APP_BASE_API + avatar;
+      }
+      this.roles = res.roles?.length ? res.roles : ['ROLE_DEFAULT'];
+      this.permissions = res.roles?.length ? res.permissions : [];
+      this.id = user.userId;
+      this.name = user.userName;
+      this.nickName = user.nickName;
+      this.avatar = avatar;
+      setQuerySession(this.id, this.roles, this.permissions);
+      return res;
     },
     // 退出系统
     logOut(options: LogoutOptions = {}) {
