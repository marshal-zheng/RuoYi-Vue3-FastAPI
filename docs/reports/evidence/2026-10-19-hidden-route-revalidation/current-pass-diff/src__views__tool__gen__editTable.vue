--- before/src/views/tool/gen/editTable.vue
+++ after/src/views/tool/gen/editTable.vue
@@ -6,14 +6,15 @@
       </el-tab-pane>
       <el-tab-pane label="字段信息" name="columnInfo">
         <el-table ref="dragTable" :data="columns" row-key="columnId">
-          <el-table-column label="序号" type="index" min-width="5%" />
+          <el-table-column label="序号" type="index" min-width="60" />
           <el-table-column
             label="字段列名"
             prop="columnName"
-            min-width="10%"
+            min-width="150"
+            fixed="left"
             :show-overflow-tooltip="true"
           />
-          <el-table-column label="字段描述" min-width="10%">
+          <el-table-column label="字段描述" min-width="150">
             <template #default="scope">
               <zx-input v-model="scope.row.columnComment"></zx-input>
             </template>
@@ -21,10 +22,10 @@
           <el-table-column
             label="物理类型"
             prop="columnType"
-            min-width="10%"
+            min-width="150"
             :show-overflow-tooltip="true"
           />
-          <el-table-column label="Python类型" min-width="11%">
+          <el-table-column label="Python类型" min-width="130">
             <template #default="scope">
               <el-select v-model="scope.row.pythonType">
                 <el-option label="str" value="str" />
@@ -40,13 +41,13 @@
               </el-select>
             </template>
           </el-table-column>
-          <el-table-column label="Python属性" min-width="10%">
+          <el-table-column label="Python属性" min-width="150">
             <template #default="scope">
               <zx-input v-model="scope.row.pythonField"></zx-input>
             </template>
           </el-table-column>
 
-          <el-table-column label="插入" min-width="5%">
+          <el-table-column label="插入" min-width="60">
             <template #default="scope">
               <el-checkbox
                 true-label="1"
@@ -55,22 +56,22 @@
               ></el-checkbox>
             </template>
           </el-table-column>
-          <el-table-column label="编辑" min-width="5%">
+          <el-table-column label="编辑" min-width="60">
             <template #default="scope">
               <el-checkbox true-label="1" false-label="0" v-model="scope.row.isEdit"></el-checkbox>
             </template>
           </el-table-column>
-          <el-table-column label="列表" min-width="5%">
+          <el-table-column label="列表" min-width="60">
             <template #default="scope">
               <el-checkbox true-label="1" false-label="0" v-model="scope.row.isList"></el-checkbox>
             </template>
           </el-table-column>
-          <el-table-column label="查询" min-width="5%">
+          <el-table-column label="查询" min-width="60">
             <template #default="scope">
               <el-checkbox true-label="1" false-label="0" v-model="scope.row.isQuery"></el-checkbox>
             </template>
           </el-table-column>
-          <el-table-column label="查询方式" min-width="10%">
+          <el-table-column label="查询方式" min-width="150">
             <template #default="scope">
               <el-select v-model="scope.row.queryType">
                 <el-option label="=" value="EQ" />
@@ -84,7 +85,7 @@
               </el-select>
             </template>
           </el-table-column>
-          <el-table-column label="必填" min-width="5%">
+          <el-table-column label="必填" min-width="60">
             <template #default="scope">
               <el-checkbox
                 true-label="1"
@@ -93,7 +94,7 @@
               ></el-checkbox>
             </template>
           </el-table-column>
-          <el-table-column label="唯一" min-width="5%">
+          <el-table-column label="唯一" min-width="60">
             <template #default="scope">
               <el-checkbox
                 true-label="1"
@@ -102,7 +103,7 @@
               ></el-checkbox>
             </template>
           </el-table-column>
-          <el-table-column label="显示类型" min-width="12%">
+          <el-table-column label="显示类型" min-width="160">
             <template #default="scope">
               <el-select v-model="scope.row.htmlType">
                 <el-option label="文本框" value="input" />
@@ -117,7 +118,7 @@
               </el-select>
             </template>
           </el-table-column>
-          <el-table-column label="字典类型" min-width="12%">
+          <el-table-column label="字典类型" min-width="160">
             <template #default="scope">
               <DictTypeSelect
                 v-model="scope.row.dictType"
