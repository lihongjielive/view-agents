# 文章配图（docx）

来源：「生产级 Multi-Agent：把任务委派变成可恢复的执行协议」系列幻灯片（01/11–11/11）。

若目录为空，在仓库根执行：

```bash
python scripts/copy_docx_images.py
```

文件与主题见根目录 [README.md](../README.md) 表格。

## 补充图（fault_drill）

| 文件 | 说明 |
|------|------|
| `fault-drill-scenarios-flowcharts.pdf` | `scenarios.py` 三页流程图（调用总览 / 五场景 / 与图01关系） |
| `fault-drill-0x-*.mmd` | 同上图源（Mermaid，可用 mermaid-cli 重导出） |

重新生成 PDF：

```bash
python scripts/export_fault_drill_flowcharts.py
```