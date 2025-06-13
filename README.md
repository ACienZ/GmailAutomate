# Gmail自动化助手

## For English Version: [English README](README_EN.md)

--------------

本项目是一个Gmail自动化工具，用于自动读取收件箱中的未读邮件，从中筛选出学生的作业，下载附件并回复。

## 1. 环境设置

### 创建并激活Conda环境

```bash
conda create -n gmail_automate python=3.8
conda activate gmail_automate
```

### 安装依赖

```bash
pip install -r requirements.txt
```

## 2. Gmail API认证设置步骤

ref:

[Gmail API Python 快速入门](https://developers.google.com/workspace/gmail/api/quickstart/python?hl=zh-cn)

### 获取API凭证

注意下载凭证文件（credentials.json）
并将下载的凭证文件重命名为`client_secret.json`并存放在项目根目录

### 注意事项

- 需要在OAuth权限请求页面添加测试用户
- 参考:
  - [Access blocked: Project has not completed the Google verification process](https://stackoverflow.com/questions/75454425/access-blocked-project-has-not-completed-the-google-verification-process)
- 由于gmail api会从最新的邮件开始读取，故如果有学生重复提交相同文件名的附件，将会从9开始重命名重名附件。同一学生同一次作业重复提交超过9次，计数将会变负数。

## 3. 配置文件设置

1. 复制`config/config.example.yaml`为`config/configs.yaml`
2. 编辑`configs.yaml`文件，填入以下信息：
   - OpenAI或DeepSeek API密钥
   - 指定使用的模型和url
   - 作业设置（编号、保存路径、截止日期等）
   - 您的邮箱信息

## 4. 使用说明

### 运行程序

```bash
python main.py
```

程序会自动：

1. 读取未读邮件并初步筛选邮件

    - 具体过滤规则：
        - 如果是html邮件，则不是学生作业
        - 如果没有附件，则不是学生作业

2. 交给LLM分析邮件内容
3. 判断是否为学生的邮件，并跳过特别学生邮件，留给手动处理

    - 具体跳过的学生邮件：
        - gpt认为不是作业的邮件
        (gpt_answer["is_assignment"] != "true")
        - gpt认为包含其他问题的邮件
        (gpt_answer["whether_contain_other_questions"] == "true")
        - gpt认为不是当期作业的邮件
        (gpt_answer["assignment_number"] != config.AssignmentSettings.assignment_number)
        - gpt无法判断学生id或姓名的邮件
        (gpt_answer["student_id"] == "unknown" or gpt_answer["student_first_name"] == "unknown" or gpt_answer["student_last_name"] == "unknown")

4. 下载学生邮件的附件
5. 自动回复学生邮件

### 回复邮件功能

由于simplegmail没有回复功能，故使用Gmail API发送回复邮件。

参考：[How to reply to an email using Gmail API](https://stackoverflow.com/a/76676129)
