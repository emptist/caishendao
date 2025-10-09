import streamlit as st
import os

"""
API密钥配置测试脚本

此脚本用于测试您的API密钥是否正确配置，可以在本地运行或部署到Streamlit Cloud后运行。

使用方法：
1. 本地测试：运行 `streamlit run test_secrets.py`
2. 部署后测试：访问已部署的应用程序URL

如果所有测试都通过，说明您的密钥配置正确。
"""

def main():
    st.title("API密钥配置测试")
    
    # 显示基本信息
    st.markdown("此工具用于验证您的API密钥是否正确配置在Streamlit Secrets中。")
    
    # 定义要测试的密钥
    secrets_to_test = [
        ("gemini", "api_key", "Gemini API密钥"),
        ("qianwen", "api_key", "千问 API密钥")
    ]
    
    # 测试本地环境变量（用于调试）
    st.subheader("环境信息")
    
    # 检查是否在Streamlit Cloud环境中
    is_streamlit_cloud = "STREAMLIT_RUNTIME_ENV" in os.environ
    st.write(f"是否在Streamlit Cloud环境中: {'是' if is_streamlit_cloud else '否'}")
    
    if not is_streamlit_cloud:
        st.info("提示：您正在本地环境中运行此测试。在Streamlit Cloud上，密钥将通过Web界面配置。")
    
    # 测试所有定义的密钥
    st.subheader("密钥配置测试结果")
    
    all_secrets_found = True
    
    for section, key, description in secrets_to_test:
        try:
            # 尝试从Streamlit secrets中获取密钥
            secret_value = st.secrets[section][key]
            
            # 检查密钥是否为空
            if secret_value and secret_value != "您的" + description:
                st.success(f"✓ {description} 已正确配置")
                # 显示部分密钥（前4个字符和后4个字符）用于验证
                if len(secret_value) > 8:
                    masked_key = secret_value[:4] + "****" + secret_value[-4:]
                    st.text(f"密钥预览: {masked_key}")
            else:
                st.warning(f"⚠ {description} 已配置但可能使用了默认值，请替换为实际密钥")
                all_secrets_found = False
        except Exception as e:
            st.error(f"✗ 无法找到 {description}")
            st.text(f"错误信息: {str(e)}")
            all_secrets_found = False
    
    # 显示环境变量备选方式
    st.subheader("备选配置方式检查")
    
    for section, key, description in secrets_to_test:
        # 检查环境变量是否存在
        env_var_name = f"STREAMLIT_{section.upper()}_{key.upper()}"
        if env_var_name in os.environ:
            st.success(f"✓ 环境变量 {env_var_name} 已设置")
        else:
            st.info(f"环境变量 {env_var_name} 未设置")
    
    # 显示总结和下一步建议
    st.subheader("总结")
    
    if all_secrets_found:
        st.success("🎉 所有测试通过！您的API密钥配置正确。")
        
        if is_streamlit_cloud:
            st.markdown("### 部署到Streamlit Cloud的注意事项")
            st.markdown("1. 您的应用已正确配置API密钥")
            st.markdown("2. 密钥安全存储在Streamlit Cloud的Secrets管理中")
            st.markdown("3. 可以继续部署和使用您的应用程序")
        else:
            st.markdown("### 部署前的准备")
            st.markdown("1. 确保 `.streamlit/secrets.toml` 已添加到 `.gitignore`")
            st.markdown("2. 不要将包含实际密钥的文件提交到GitHub")
            st.markdown("3. 部署到Streamlit Cloud时，使用Web界面配置密钥")
    else:
        st.warning("⚠ 部分测试未通过，请检查您的密钥配置。")
        st.markdown("### 配置指南")
        st.markdown("1. 本地开发：复制 `.streamlit/secrets_example.toml` 并重命名为 `.streamlit/secrets.toml`，然后填写实际密钥")
        st.markdown("2. Streamlit Cloud：在应用程序设置的Secrets选项卡中配置密钥")
        st.markdown("3. 环境变量：设置格式为 `STREAMLIT_<SECRET_NAME>` 的环境变量")
    
    # 显示快速链接
    st.subheader("快速链接")
    st.markdown("- [Streamlit Cloud](https://share.streamlit.io)")
    st.markdown("- [Streamlit Secrets 文档](https://docs.streamlit.io/streamlit-community-cloud/deploy-your-app/secrets-management)")

if __name__ == "__main__":
    main()