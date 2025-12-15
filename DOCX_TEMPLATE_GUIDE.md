## WPS Word 模板占位符与数据映射（docxtpl）

### 1. 模板绘制要点
- 先在 WPS Word 画出表格（合并/拆分、列宽、竖排文字都在 Word 里完成），不要在 Python 里“画”。
- 竖排文字：选中“以太网”单元格 → 右键“文字方向” → 竖向。
- 保留字段明细的那一整行作为循环模板行（序号/信息名称/字节数/.../备注）。

### 2. 顶部/左侧占位符
直接在对应单元格填入：
- 表题：`表 {{ appendix }}.{{ table_index }} {{ bus_type }}通信协议格式`
- 设备：`{{ protocol_name }}` 或 `{{ device }}`（按需要）
- 发送方：`{{ sender }}`；接收方：`{{ receiver }}`
- 传输频率：`{{ frequency }}`
- 传输速率/bps：`{{ baud_rate }}`
- 传输方式：`{{ method }}`（会用内置映射把 udp_unicast 等翻译成中文）
- 端口号/发送时长：标题 `{{ duration_or_port_label }}`，值 `{{ duration_or_port_value }}`
- 帧长度/Byte：`{{ frame_len }}`
- 错误处理：`{{ error_handle }}`（会用内置映射把 errorHandling 代码翻译成中文）
- 左侧竖排协议/总线类型：`{{ bus_type }}`（protocolLabel/protocolType/busType 兜底）

### 3. 循环行占位符（字段明细）
- 在“序号”单元格写 `{% for item in items %}`，在同一行“备注”单元格写 `{% endfor %}`。
- 行内各列放：
  - 序号：`{{ item.idx }}`
  - 信息名称：`{{ item.name }}`
  - 字节数：`{{ item.bytes }}`
  - 字节序号：`{{ item.byte_range }}`
  - 值域及含义：`{{ item.meaning }}`
  - 量纲：`{{ item.unit }}`
  - 数据类型：`{{ item.dtype }}`
  - 比例尺：`{{ item.scale }}`
  - 备注：`{{ item.remark }}`

### 4. 附注行
- “附注”右侧单元格：`{{ notes }}`

### 5. Python 渲染示例（与现有数据结构匹配）
```python
from utils.word_util import extract_protocols_from_topology, METHOD_LABEL_MAP, ERROR_HANDLING_LABEL_MAP
from docxtpl import DocxTemplate

def build_doc_context(topology):
    devices = extract_protocols_from_topology(topology)
    ctx = {"appendices": []}
    for dev_idx, dev in enumerate(devices):
        appendix = chr(ord('A') + dev_idx)
        protocols_ctx = []
        for idx, proto in enumerate(dev["protocols"], 1):
            header = proto.get("header", {}) or {}
            port = header.get("port") or header.get("portNo") or header.get("portNumber") or ""
            method = header.get("methodLabel") or header.get("method") or ""
            method = METHOD_LABEL_MAP.get(method, method)
            err = header.get("errorHandling") or header.get("errorHandle") or ""
            err = ERROR_HANDLING_LABEL_MAP.get(err, err)
            protocols_ctx.append({
                "appendix": appendix,
                "table_index": idx,
                "protocol_name": proto.get("name") or proto.get("protocolName") or "协议",
                "bus_type": header.get("protocolLabel") or header.get("protocolTypeLabel") or header.get("protocolType")
                             or header.get("busTypeLabel") or header.get("busType") or "",
                "sender": proto.get("sender") or header.get("sender") or "",
                "receiver": proto.get("receiver") or header.get("receiver") or "",
                "frequency": header.get("frequency") or "",
                "baud_rate": header.get("baudRate") or header.get("speed") or "",
                "method": method,
                "duration_or_port_label": "端口号" if port else "发送时长/ms",
                "duration_or_port_value": port or header.get("duration") or header.get("sendDuration") or "",
                "frame_len": header.get("frameLength") or "",
                "error_handle": err,
                "items": [
                    {
                        "idx": i + 1,
                        "name": f.get("name") or f.get("fieldName") or "",
                        "bytes": f.get("byteCount") or "",
                        "byte_range": f.get("byteSequence") or f.get("byteIndex") or f.get("byteNo") or "",
                        "meaning": "<br>".join(str(v) for v in f.get("valueRange", []) if v not in (None, ""))
                                   if isinstance(f.get("valueRange"), list)
                                   else (f.get("valueRange") or f.get("valueMeaning") or ""),
                        "unit": f.get("unitLabel") or f.get("unit") or f.get("dimension") or "",
                        "dtype": f.get("dataType") or "",
                        "scale": f.get("scale") or f.get("ratio") or "",
                        "remark": f.get("remark") or f.get("note") or "",
                    }
                    for i, f in enumerate(proto.get("fields") or [])
                ],
                "notes": header.get("notes") or "",
            })
        ctx["appendices"].append({"device_name": dev["deviceName"], "protocols": protocols_ctx})
    return ctx

# 渲染
doc = DocxTemplate("template.docx")
context = build_doc_context(topology_data)  # topology_data 来自已有接口
doc.render(context)
doc.save("output.docx")
```

### 6. 模板内循环示例（表格行内）
```
| {% for item in items %} | {{ item.idx }} | {{ item.name }} | ... | {{ item.remark }} | {% endfor %} |
```

### 7. 变量来源说明
- 数据来源：`extract_protocols_from_topology`（`utils/word_util.py`）产出的 `protocols`。
- 映射规则：同文件中 `generate_protocol_table_html/generate_protocol_excel` 的取值逻辑（method 和 errorHandling 已有中文映射）。
