<template>
  <el-dialog
    v-model="visible"
    title="导入报文字段"
    width="600px"
    @close="onClose"
  >
    <div class="import-file-dialog">
      <div class="tips">
        <el-alert
          title="导入说明"
          type="info"
          :closable="false"
          show-icon
        >
          <template #default>
            <div class="tip-content">
              <p>1. 支持导入 Excel(.xlsx, .xls) 或 CSV(.csv) 格式文件</p>
              <p>2. 请按照模板格式整理数据，确保字段名称、数据类型等信息完整</p>
              <p>3. 导入的数据将追加到现有字段列表中</p>
            </div>
          </template>
        </el-alert>
      </div>

      <div class="template-download">
        <el-button type="primary" link icon="Download" @click="downloadTemplate">
          下载导入模板
        </el-button>
      </div>

      <el-upload
        ref="uploadRef"
        class="upload-container"
        drag
        :auto-upload="false"
        :limit="1"
        :accept="acceptTypes"
        :on-change="handleFileChange"
        :on-exceed="handleExceed"
        :file-list="fileList"
      >
        <el-icon class="el-icon--upload">
          <upload-filled />
        </el-icon>
        <div class="el-upload__text">
          将文件拖到此处，或<em>点击上传</em>
        </div>
        <template #tip>
          <div class="el-upload__tip">
            只能上传 xlsx/xls/csv 文件，且不超过 10MB
          </div>
        </template>
      </el-upload>

      <div v-if="fileInfo" class="file-info">
        <el-icon><Document /></el-icon>
        <span class="file-name">{{ fileInfo.name }}</span>
        <span class="file-size">{{ formatFileSize(fileInfo.size) }}</span>
      </div>
    </div>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="closeDialog">取消</el-button>
        <el-button type="primary" :loading="uploading" @click="submitImport">
          确定导入
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup name="ImportFileDialog">
import { ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { UploadFilled, Document } from '@element-plus/icons-vue'
import * as XLSX from 'xlsx'

const props = defineProps({
  modelValue: { type: Boolean, default: false }
})

const emit = defineEmits(['update:modelValue', 'import', 'close'])

const visible = ref(props.modelValue)
watch(() => props.modelValue, (v) => visible.value = v)
watch(visible, (v) => emit('update:modelValue', v))

const uploadRef = ref()
const fileList = ref([])
const fileInfo = ref(null)
const uploading = ref(false)
const acceptTypes = '.xlsx,.xls,.csv'

// 文件变化处理
function handleFileChange(file) {
  const isValidType = /\.(xlsx|xls|csv)$/.test(file.name.toLowerCase())
  const isLt10M = file.size / 1024 / 1024 < 10

  if (!isValidType) {
    ElMessage.error('只能上传 xlsx/xls/csv 格式的文件！')
    fileList.value = []
    fileInfo.value = null
    return false
  }

  if (!isLt10M) {
    ElMessage.error('文件大小不能超过 10MB！')
    fileList.value = []
    fileInfo.value = null
    return false
  }

  fileInfo.value = file.raw || file
  return true
}

// 文件超出限制
function handleExceed() {
  ElMessage.warning('只能上传一个文件，请删除后重新上传')
}

// 格式化文件大小
function formatFileSize(bytes) {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i]
}

// 下载模板
function downloadTemplate() {
  // 创建模板数据
  const templateData = [
    {
      '信息名称': '同步码1',
      '字节数': 1,
      '字节序号': '0',
      '值域及含义': '0xEB',
      '量纲': '',
      '数据类型': 'UINT8',
      '比例尺': '1',
      '父级ID': ''
    },
    {
      '信息名称': '同步码2',
      '字节数': 1,
      '字节序号': '1',
      '值域及含义': '0x90',
      '量纲': '',
      '数据类型': 'UINT8',
      '比例尺': '1',
      '父级ID': ''
    },
    {
      '信息名称': '报文字节数',
      '字节数': 2,
      '字节序号': '2~3',
      '值域及含义': '0x0100',
      '量纲': '',
      '数据类型': 'UINT16',
      '比例尺': '1',
      '父级ID': ''
    }
  ]

  // 创建工作簿
  const ws = XLSX.utils.json_to_sheet(templateData)
  const wb = XLSX.utils.book_new()
  XLSX.utils.book_append_sheet(wb, ws, '报文字段模板')

  // 设置列宽
  ws['!cols'] = [
    { wch: 20 }, // 信息名称
    { wch: 10 }, // 字节数
    { wch: 12 }, // 字节序号
    { wch: 25 }, // 值域及含义
    { wch: 10 }, // 量纲
    { wch: 12 }, // 数据类型
    { wch: 10 }, // 比例尺
    { wch: 15 }  // 父级ID
  ]

  // 导出文件
  XLSX.writeFile(wb, '报文字段导入模板.xlsx')
  ElMessage.success('模板下载成功')
}

// 解析Excel/CSV文件
async function parseFile(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    
    reader.onload = (e) => {
      try {
        const data = new Uint8Array(e.target.result)
        const workbook = XLSX.read(data, { type: 'array' })
        
        // 读取第一个sheet
        const firstSheetName = workbook.SheetNames[0]
        const worksheet = workbook.Sheets[firstSheetName]
        
        // 转换为JSON
        const jsonData = XLSX.utils.sheet_to_json(worksheet)
        
        if (!jsonData || jsonData.length === 0) {
          reject(new Error('文件内容为空'))
          return
        }
        
        // 转换数据格式
        const fields = jsonData.map((row, index) => {
          const id = Date.now() + index
          return {
            id: String(id),
            parentId: row['父级ID'] || null,
            fieldName: row['信息名称'] || '',
            byteCount: Number(row['字节数']) || 1,
            byteSequence: String(row['字节序号'] || ''),
            valueRange: String(row['值域及含义'] || ''),
            unit: String(row['量纲'] || ''),
            dataType: row['数据类型'] || 'UINT8',
            scale: String(row['比例尺'] || '1')
          }
        })
        
        resolve(fields)
      } catch (error) {
        reject(error)
      }
    }
    
    reader.onerror = () => {
      reject(new Error('文件读取失败'))
    }
    
    reader.readAsArrayBuffer(file)
  })
}

// 提交导入
async function submitImport() {
  if (!fileInfo.value) {
    ElMessage.warning('请先选择要导入的文件')
    return
  }

  uploading.value = true
  
  try {
    const fields = await parseFile(fileInfo.value)
    
    if (!fields || fields.length === 0) {
      ElMessage.warning('文件中没有有效的数据')
      return
    }

    emit('import', fields)
    ElMessage.success(`成功导入 ${fields.length} 个字段`)
    closeDialog()
  } catch (error) {
    console.error('导入失败:', error)
    ElMessage.error('导入失败: ' + (error.message || '文件解析错误'))
  } finally {
    uploading.value = false
  }
}

// 关闭对话框
function closeDialog() {
  visible.value = false
}

// 对话框关闭时的处理
function onClose() {
  fileList.value = []
  fileInfo.value = null
  uploading.value = false
  emit('close')
}
</script>

<style lang="scss" scoped>
.import-file-dialog {
  padding: 10px 0;
}

.tips {
  margin-bottom: 20px;

  .tip-content {
    p {
      margin: 5px 0;
      line-height: 1.6;
      color: #606266;
    }
  }
}

.template-download {
  margin-bottom: 20px;
  text-align: center;
}

.upload-container {
  :deep(.el-upload) {
    width: 100%;
  }

  :deep(.el-upload-dragger) {
    width: 100%;
    padding: 40px 20px;
  }
}

.file-info {
  margin-top: 20px;
  padding: 12px 15px;
  background-color: #f5f7fa;
  border-radius: 4px;
  display: flex;
  align-items: center;
  gap: 10px;

  .el-icon {
    font-size: 20px;
    color: #409eff;
  }

  .file-name {
    flex: 1;
    font-size: 14px;
    color: #303133;
    font-weight: 500;
  }

  .file-size {
    font-size: 12px;
    color: #909399;
  }
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}
</style>

