# IDEO Academic Literature Digest

这个程序为 UBC Visual Cognition Lab 的 **2026 online prediction-feedback Phase 1** 实验每周检索并筛选学术资料。它会在每周五上午 9:00（温哥华时间）运行，并通过 Gmail 把 3–5 篇最相关的论文发给你。

## 它会做什么

1. 使用 OpenAlex 检索最近 14 天发表或上线的论文与 preprint。
2. 合并多个检索式、根据 DOI/标题去重，并排除以前发过的论文。
3. 先用关键词和方法信息进行低成本预筛选。
4. 把最多 18 篇候选论文的公开元数据和摘要交给 OpenAI 评估。
5. 选择相关性最高且达到门槛的 3–5 篇，生成中文研究简报。
6. 通过 Gmail 给同一个 Gmail 地址发送 HTML + 纯文本邮件。
7. 更新 `data/seen.json`，防止以后重复推送。

程序不会下载或转发付费论文全文，也不会绕过出版社的访问限制。邮件会提供 DOI、OpenAlex 或合法开放获取页面。

## 当前实验相关性标准

`config/research_profile.yml` 中记录的是用于检索和筛选的 **working relevance profile**，不是替代实验 preregistration 的正式假设。它基于目前的 Phase 1 流程：

- 72 道 Yes/No 知识判断题，并记录 `SURE` / `GUESS`；
- 16 道限时 Yes/No 题；
- 将预设的 `MATCHED` / `DID NOT MATCH` 反馈描述为电脑预测系统的结果；
- post-survey、demographics、debrief、deception/suspicion check；
- 重点关注 sense of agency、ideomotor theory、action–effect learning、prediction feedback、confidence/metacognition、deception check，以及线上反应时实验的方法质量。

以后实验假设或流程变化时，只需编辑这个 YAML 文件，不需要修改 Python 代码。

## GitHub 设置（第一次约 10–15 分钟）

### 1. 创建仓库

在 GitHub 创建一个 **Private repository**，例如 `ideo-literature-digest`，然后把本项目的所有文件上传到仓库根目录。建议使用 private repository，因为配置文件包含尚在进行的实验设计背景。

### 2. 准备 OpenAI API key

在 OpenAI API 平台创建 API key，并确保 API 账户已配置可用额度。ChatGPT 订阅和 API 计费是不同的产品账户体系。

程序默认使用 `gpt-5.6-terra`，在质量和成本之间取得平衡。若希望降低费用，可在 GitHub Repository Variables 中设置：

```text
OPENAI_MODEL = gpt-5.6-luna
```

程序每周只进行一次批量 AI 评估，且最多输入 18 篇候选论文的摘要。

### 3. 创建 Gmail App Password

不要使用 Gmail 主密码。

1. 在 Google Account 中启用 **2-Step Verification**。
2. 打开 Google Account 的 **App passwords** 页面。
3. 创建一个用于本程序的 16 位 App Password。
4. 复制该 App Password；添加到 GitHub 时可以保留或去掉空格，程序会自动清理空格。

部分学校/公司管理的 Google Workspace、Advanced Protection 账户或只使用 security key 的账户可能不提供 App Password。这种情况下需要改用 Gmail OAuth，当前第一版暂未包含该模式。

### 4. 添加 GitHub Secrets

进入仓库：

`Settings → Secrets and variables → Actions → New repository secret`

添加以下三个必需 Secrets：

| Secret | 内容 |
| --- | --- |
| `OPENAI_API_KEY` | OpenAI API key |
| `EMAIL_ADDRESS` | 用来发送并接收简报的 Gmail 地址 |
| `GMAIL_APP_PASSWORD` | Gmail 16 位 App Password |

可选：

| Secret / Variable | 用途 |
| --- | --- |
| `OPENALEX_API_KEY` Secret | 提高 OpenAlex API 日限额；每周任务通常不需要 |
| `OPENAI_MODEL` Variable | 覆盖默认模型，例如 `gpt-5.6-luna` |

Secrets 不会出现在代码或邮件内容中。

### 5. 第一次手动测试

1. 打开仓库的 **Actions** 页面。
2. 选择 **Weekly IDEO literature digest**。
3. 点击 **Run workflow**。
4. 确认运行成功，并检查 Gmail 收件箱和 Spam。

之后 workflow 会按照以下本地时间自动执行：

```yaml
cron: "0 9 * * 5"
timezone: "America/Vancouver"
```

GitHub 的定时任务可能因平台负载稍有延迟。定时 workflow 必须存在于 default branch；如果使用 public repository 且 60 天没有活动，GitHub 可能自动暂停 schedule，因此本项目建议 private repository。

## 在电脑上测试（可选）

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
```

填写 `.env` 后，将其中的值加载到当前终端：

```bash
set -a
source .env
set +a
```

先生成报告但不发邮件：

```bash
ideo-digest --dry-run --lookback-days 90
```

正式发送：

```bash
ideo-digest
```

运行测试：

```bash
pytest
```

## 调整检索范围

编辑 `config/research_profile.yml`：

- `search_queries`：实际发送给 OpenAlex 的检索式；
- `priority_terms`：本地预筛选加分词；
- `exclude_terms`：明显无关领域的降分词；
- `lookback_days`：默认回看天数；
- `candidate_limit`：送给 OpenAI 的候选上限；
- `minimum_relevance_score`：进入邮件的 AI 评分门槛；
- `digest_min_items` / `digest_max_items`：目标论文数。

首次运行可以临时扩大搜索窗口：

```bash
ideo-digest --lookback-days 180
```

## 邮件中每篇论文包含

- 原始英文标题、作者、日期、期刊/来源和链接；
- 论文类型与和项目的相关性分数；
- 中文研究摘要；
- 为什么与 Phase 1 直接相关；
- 可以如何影响实验设计、post-survey 或分析；
- 根据摘要能够判断的限制与风险。

AI 只会看到公开论文元数据、摘要和 `research_profile.yml` 中的实验简介。**不要把参与者姓名、HSP ID、原始作答或任何可识别研究数据写入配置文件。**

OpenAI 请求设置为 `store=False`；程序本身只在仓库的 `data/seen.json` 中保存已发送论文的 ID、标题、链接和发送时间。

## 使用的官方文档

- [OpenAI Responses API – text generation](https://developers.openai.com/api/docs/guides/text)
- [OpenAI Structured Outputs](https://developers.openai.com/api/docs/guides/structured-outputs)
- [OpenAlex API reference](https://help.openalex.org/api/)
- [GitHub Actions scheduled workflows](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule)
- [Google Account App Passwords](https://support.google.com/accounts/answer/185833)
