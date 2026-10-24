--- before/src/views/system/dict/data.vue
+++ after/src/views/system/dict/data.vue
@@ -129,6 +129,7 @@
             label="操作"
             align="center"
             width="160"
+            fixed="right"
             class-name="small-padding fixed-width"
           >
             <template #default="scope">
@@ -313,15 +314,19 @@
 );
 
 // Type changes (including rename invalidation) drive this request-mode list's filter once.
-watch(defaultDictType, (type) => {
-  if (!type) return;
-  initialState.value = {
-    ...initialState.value,
-    query: { ...initialState.value.query, dictType: type },
-  };
-  gridListRef.value?.updateState('query.dictType', type);
-  refreshList();
-});
+watch(
+  defaultDictType,
+  (type) => {
+    if (!type) return;
+    initialState.value = {
+      ...initialState.value,
+      query: { ...initialState.value.query, dictType: type },
+    };
+    gridListRef.value?.updateState('query.dictType', type);
+    refreshList();
+  },
+  { immediate: true }
+);
 
 /** 取消按钮 */
 function cancel() {
@@ -398,7 +403,10 @@
       dataDialog.setDisabled(false);
       return;
     }
-    const detail = await getData(id, { signal: read.signal, silentError: true });
+    const detail = await getData(id, {
+      signal: read.signal,
+      silentError: true,
+    });
     if (!read.isCurrent()) return;
     form.value = detail;
     dataDialog.setDisabled(false);
