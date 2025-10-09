# Trading tools

## 安全注意事项

### API密钥配置
本项目使用AI服务需要配置API密钥，但**不应该将密钥提交到版本控制系统**。以下是安全配置方法：

#### 方法1：使用 Streamlit Secrets（推荐）
1. 项目中已提供 `.streamlit/secrets_example.toml` 示例文件
2. 复制此文件并重命名为 `.streamlit/secrets.toml`
3. 用您的实际API密钥替换示例文件中的占位符
4. 系统会自动将 `.streamlit/secrets.toml` 排除在版本控制之外（已在 .gitignore 中配置）

#### 方法2：使用环境变量（适用于CI/CD或服务器部署）
如果您在服务器或CI/CD环境中运行，可以使用环境变量：
1. 设置环境变量，格式为：`STREAMLIT_<SECRET_NAME>`
2. 例如，对于 `[gemini]` 部分的 `api_key`，环境变量应为 `STREAMLIT_GEMINI_API_KEY`
3. Streamlit会自动识别这些环境变量

#### 方法3：部署到Streamlit Cloud时的配置
当部署到 Streamlit Cloud (https://share.streamlit.io) 时，按照以下步骤配置密钥：
1. 登录到您的 Streamlit Cloud 账户
2. 选择您要部署的应用程序或创建一个新应用
3. 在应用程序页面中，点击右上角的 **⋮** 按钮，选择 **Settings**
4. 在左侧导航栏中选择 **Secrets** 选项卡
5. 在文本框中，按照与 `secrets.toml` 文件相同的格式输入您的密钥
   例如：
   ```toml
   [gemini]
   api_key = "您的Gemini API密钥"
   
   [qianwen]
   api_key = "您的千问API密钥"
   ```
6. 点击 **Save** 保存您的密钥配置
7. Streamlit Cloud会安全地存储这些密钥，并在应用程序运行时使其可用

Streamlit Cloud的密钥存储是安全的，不会将您的密钥暴露给公众或提交到代码仓库中。

#### 注意事项
- 不要将包含实际API密钥的文件提交到GitHub或其他版本控制系统
- 定期轮换API密钥以提高安全性
- 为API密钥设置最小必要权限
- 仅向绝对必要的团队成员提供API密钥访问权限

### 数据安全
- AI分析记录存储在 `.ai_ana_records/` 目录中
- 系统会自动设置该目录权限为 0o700（仅所有者可读写执行）
- 避免在公共环境中共享这些分析记录文件

### 使用前准备
1. 安装依赖：`pip install -r requirements.txt`
2. 在 `.streamlit/secrets.toml` 中配置所需API密钥
3. 确保您有正确的文件系统权限来创建和修改项目文件

## 注意事项
代码已较原始README编写时有较大改动。

