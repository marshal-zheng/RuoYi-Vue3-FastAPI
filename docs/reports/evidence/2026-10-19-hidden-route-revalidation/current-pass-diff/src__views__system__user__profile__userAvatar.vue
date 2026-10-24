--- before/src/views/system/user/profile/userAvatar.vue
+++ after/src/views/system/user/profile/userAvatar.vue
@@ -1,6 +1,6 @@
 <template>
   <div class="user-info-head" @click="editCropper()">
-    <img :src="options.img" title="点击上传头像" class="img-circle img-lg" />
+    <img :src="options.img" title="点击上传头像" class="user-info-avatar" />
     <ZxDialog
       dialog-size="lg"
       :draggable="false"
@@ -178,7 +178,16 @@
 .user-info-head {
   position: relative;
   display: inline-block;
+  width: 120px;
   height: 120px;
+}
+
+.user-info-avatar {
+  display: block;
+  width: 100%;
+  height: 100%;
+  object-fit: cover;
+  border-radius: 50%;
 }
 
 .user-info-head:hover:after {
