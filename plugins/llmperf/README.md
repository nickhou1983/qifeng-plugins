# LLMPerf Plugin

Benchmark LLM latency metrics including TTFT (Time To First Token), TTFR (Time To First Reasoning), and TPS (Tokens Per Second).

## Skills

| Skill | Description |
|-------|-------------|
| **ttft-ttfr-testing** | 测试大模型 TTFT / TTFR / TPS 性能，自动分析结果并给出优化建议 |

## Workflow

1. **确认配置** — 确认 `config.yaml` 中的 endpoint、model、streaming 等参数
2. **环境检查** — 确保 Python 依赖已安装、`.env` 中已设置 `LLM_API_KEY`
3. **执行测试** — 运行 `run_ttft_ttfr_test.py` 进行基准测试
4. **读取结果** — 测试结果自动保存为 JSON 到 `reports/` 目录
5. **分析报告** — 运行 `analyze_results.py` 生成 Markdown 分析报告
6. **优化建议** — 基于阈值自动给出 TTFT、TTFR、TPS、稳定性优化建议

## Prerequisites

- Python 3.10+
- 依赖包：`httpx`、`tiktoken`、`pyyaml`、`python-dotenv`
- 已部署的 LLM API endpoint（支持 Azure OpenAI Responses API 和 OpenAI Chat Completions API）
- 配置 `.env` 文件中的 `LLM_API_KEY`

## Installation

```bash
cd plugins/llmperf
cp .env.example .env
# 编辑 .env 填入你的 LLM API Key

# 安装依赖
pip install -r skills/ttft-ttfr-testing/requirements.txt
```

## Usage

### 运行基准测试

```bash
# 使用 config.yaml 默认配置
python skills/ttft-ttfr-testing/scripts/run_ttft_ttfr_test.py

# 指定 endpoint 和 model
python skills/ttft-ttfr-testing/scripts/run_ttft_ttfr_test.py \
  --endpoint "https://your-resource.openai.azure.com/openai/responses?api-version=2025-04-01-preview" \
  --model gpt-4o \
  --streaming \
  --runs 5

# 使用自定义 prompt
python skills/ttft-ttfr-testing/scripts/run_ttft_ttfr_test.py \
  --prompt "解释量子计算的基本原理" \
  --streaming --runs 3

# 仅输出 JSON（适合管道处理）
python skills/ttft-ttfr-testing/scripts/run_ttft_ttfr_test.py --json
```

### 分析测试结果

```bash
# 分析最新结果
python skills/ttft-ttfr-testing/scripts/analyze_results.py --latest

# 分析指定结果文件
python skills/ttft-ttfr-testing/scripts/analyze_results.py \
  --result-file reports/gpt-4o_high_20260314_120000.json
```

### 输出示例

**测试执行输出：**

```text
[1/3] 发送请求...
  ✓ 总延迟 2345ms | TTFT 312ms | TTFR 856ms | 输出 token 128 | TPS 62.9
[2/3] 发送请求...
  ✓ 总延迟 2198ms | TTFT 298ms | TTFR 801ms | 输出 token 135 | TPS 67.3
[3/3] 发送请求...
  ✓ 总延迟 2456ms | TTFT 345ms | TTFR 912ms | 输出 token 121 | TPS 57.4

========== 汇总 ==========
  请求数: 3 | 成功: 3 | 失败: 0
  TTFT  均值: 318ms | 标准差: 24ms
  TTFR  均值: 856ms | 标准差: 56ms
  TPS   均值: 62.5 tokens/s
```

## 指标阈值说明

| 指标 | 🟢 优秀 | 🟡 正常 | 🔴 需优化 |
|------|---------|---------|-----------|
| TTFT | < 500ms | 500–1500ms | > 1500ms |
| TTFR | < 1000ms | 1000–3000ms | > 3000ms |
| TPS | > 50 tokens/s | 20–50 tokens/s | < 20 tokens/s |
| CV（稳定性） | < 10% | 10–30% | > 30% |

## Limitations

- 测试结果受网络延迟、API 负载等外部因素影响，建议多次测试取平均值
- TTFR 仅在 streaming 模式且模型支持 reasoning 事件时可测量
- TPS 计算基于 tiktoken 估算的 token 数量，与提供商计费 token 数可能略有差异
- config.yaml 中的默认 endpoint 为示例值，需替换为实际可用的 API 地址

## License

MIT
