import google.generativeai as genai
import requests
import json
from settings import MySetts
import ai_cache  # 引入新创建的缓存模块
import streamlit as st
from pathlib import Path



# public interface
def st_ai_analysis_area(symbol, info, ai_provider, session_state):    
    """ AI Analysis Area, the only public interface for calling from client side,
    it will show a button to trigger AI analysis, and show the analysis result when clicked.
    
    Args:
        symbol (str): The stock/ETF symbol
        info (dict): Information about the symbol
        ai_provider (str): AI provider to use ('gemini' or 'alibabacloud')
        session_state: The session state from the calling app
    """
    if info:
        # Initialize session state to store analysis trigger state per symbol
        if 'show_ai_analysis' not in session_state:
            session_state.show_ai_analysis = {}

        # Show the button only if analysis has not been triggered for the current symbol
        if not session_state.show_ai_analysis.get(symbol, False):
            if st.button(f"Trigger AI analysis for {symbol}"):
                # When clicked, set the state for the symbol to True and rerun
                session_state.show_ai_analysis[symbol] = True
                st.rerun()

        # If the analysis has been triggered for the symbol, display it
        if session_state.show_ai_analysis.get(symbol, False):
            ai_container = st.container()
            with ai_container:
                ai_analysis = st.empty()
            show_ai_analysis(symbol, info, ai_analysis, ai_provider, session_state)
    else:
        # If no valid info is available, show a warning
        st.warning(f"Could not retrieve detailed information for {symbol} to generate analysis.")


@st.cache_data
def is_etf(info):
    """判断资产类型是否为ETF"""
    # 如果没有分析师评级，高度可能是ETF
    if not info.get("numberOfAnalystOpinions"):
        has_category = 'category' in info
        has_etf_in_name = 'longName' in info and 'ETF' in info['longName'].upper()
        return has_category or has_etf_in_name
    return False


def generate_local_analysis(symbol, info):
    """当API调用失败时生成本地替代分析"""
    is_etf_flag = is_etf(info)
    asset_type = "ETF" if is_etf_flag else "Stock"
    
    # 根据资产类型选择不同的关键信息
    if is_etf_flag:
        key_info = {
            "ETF名称": info.get("longName", "N/A"),
            "代码": info.get("symbol", "N/A"),
            "当前价格": info.get("currentPrice", "N/A"),
            "52周最高价": info.get("fiftyTwoWeekHigh", "N/A"),
            "52周最低价": info.get("fiftyTwoWeekLow", "N/A"),
            "市值": info.get("marketCap", "N/A"),
            "类别": info.get("category", "N/A"),
        }
    else:
        key_info = {
            "公司名称": info.get("longName", "N/A"),
            "代码": info.get("symbol", "N/A"),
            "当前价格": info.get("currentPrice", "N/A"),
            "目标价": info.get("targetMeanPrice", "N/A"),
            "52周最高价": info.get("fiftyTwoWeekHigh", "N/A"),
            "52周最低价": info.get("fiftyTwoWeekLow", "N/A"),
            "市盈率(TTM)": info.get("trailingPE", "N/A"),
            "预期市盈率": info.get("forwardPE", "N/A"),
            "市值": info.get("marketCap", "N/A"),
            "分析师评级": f"{info.get('recommendationKey', 'N/A')} (基于 {info.get('numberOfAnalystOpinions', 'N/A')} 个观点)",
        }

    # 创建简化的Markdown分析
    markdown_analysis = f"#{symbol} ({key_info.get('公司名称') or key_info.get('ETF名称')}) {asset_type}分析\n\n"
    markdown_analysis += "## 关键指标\n"
    for key, value in key_info.items():
        if key not in ["公司名称", "ETF名称", "代码"]:
            markdown_analysis += f"- **{key}:** {value}\n"
            
    # 添加基本解释
    markdown_analysis += "\n## 基本评估\n"
    
    if not is_etf_flag:
        # 股票分析
        if info.get("recommendationKey") == "buy":
            markdown_analysis += "- 分析师目前建议买入此Stock。\n"
        elif info.get("recommendationKey") == "hold":
            markdown_analysis += "- 分析师目前建议持有此Stock。\n"
        elif info.get("recommendationKey") == "sell":
            markdown_analysis += "- 分析师目前建议卖出此Stock。\n"
        
        if info.get("targetMeanPrice") and info.get("currentPrice"):
            try:
                target = float(info.get("targetMeanPrice"))
                current = float(info.get("currentPrice"))
                upside = ((target - current) / current) * 100
                if upside > 0:
                    markdown_analysis += f"- 根据分析师目标价格，相比当前价格有潜在 {upside:.1f}% 的上涨空间。\n"
                else:
                    markdown_analysis += f"- 根据分析师目标价格，相比当前价格有潜在 {-upside:.1f}% 的下跌空间。\n"
            except (ValueError, TypeError):
                pass
    else:
        # ETF分析
        markdown_analysis += "- 这是一个ETF产品，主要关注其跟踪的市场指数、行业或资产类别的表现。\n"
        if info.get('category'):
            markdown_analysis += f"- 此ETF属于{info.get('category')}类别。\n"
            
    markdown_analysis += "\n*注：这是在AI API请求失败或超时时本地生成的简化分析。*"
    
    return markdown_analysis


@st.cache_resource
def get_gemini_model():
    """获取并缓存Gemini模型实例，包含模型回退机制"""
    try:
        api_key = st.secrets["GEMINI_API_KEY"]
        genai.configure(api_key=api_key)
        
        # 定义一个模型优先级列表，根据available_g_apis.md中显示的实际可用模型排序
        # 优先选择较新的稳定版本和快速版本
        model_candidates = [
            'gemini-2.5-flash',            # 最新的快速模型，适合大多数场景
            'gemini-2.5-pro',              # 最新的专业模型，功能更强大
            'gemini-flash-latest',         # 最新的快速模型别名
            'gemini-pro-latest',           # 最新的专业模型别名
            'gemini-2.5-flash-lite',       # 轻量版快速模型，响应更快
            'gemini-2.0-flash',            # 较稳定的快速模型
            'gemini-2.0-pro-exp',          # 较稳定的专业模型
        ]
        
        # 尝试按优先级使用模型
        for model_name in model_candidates:
            try:
                return genai.GenerativeModel(model_name)
            except Exception:
                # 记录尝试失败的模型，但继续尝试下一个
                pass
                
        # 如果所有模型都失败，获取可用模型列表以便调试
        try:
            available_models = genai.list_models()
            model_names = [m.name for m in available_models if 'generateContent' in m.supported_generation_methods]
            if model_names:
                # 尝试使用第一个可用的支持generateContent的模型
                return genai.GenerativeModel(model_names[0])
        except Exception:
            pass
            
        return None
    except (FileNotFoundError, KeyError):
        return None
    except Exception as e:
        # 如果模型初始化失败，添加更详细的错误信息
        error_msg = f"Failed to initialize Gemini model: {e}"
        try:
            # 尝试获取可用模型列表以提供更多信息
            available_models = genai.list_models()
            model_names = [m.name for m in available_models if 'generateContent' in m.supported_generation_methods]
            if model_names:
                error_msg += f"\n\n可用的模型: {', '.join(model_names)}"
        except Exception:
            pass
        
        st.error(error_msg)
        return None


def get_gemini_analysis(symbol, info):
    """使用Google Gemini API进行Stock/ETF分析"""
    model = get_gemini_model()
    if model is None:
        error_msg = "GEMINI_API_KEY not found in st.secrets. Please add it to your secrets file.\n\n"
        return error_msg + "### Local Fallback Analysis\n" + generate_local_analysis(symbol, info)

    is_etf_flag = is_etf(info)
    # 根据资产类型构建不同的提示词
    if is_etf_flag:
        prompt = f"Analyze the following ETF: {symbol}. Below is a summary of its key data. Provide a concise analysis for a potential investor, including the ETF's investment objective, tracked market or industry performance, risk characteristics, and conclude with a suggested course of action (e.g., Buy, Hold, Watch). Format the output using Markdown.\\n\\n"
    else:
        prompt = f"Analyze the following stock: {symbol}. Below is a summary of its financial data. Provide a concise analysis for a potential investor. Highlight the most important positive and negative points and conclude with a suggested course of action (e.g., Buy, Hold, Sell, Watch). Format the output using Markdown.\\n\\n"

    # 添加关键信息到提示词
    for key, value in info.items():
        prompt += f"- **{key}:** {value}\\n"

    try:
        response = model.generate_content(prompt, request_options={'timeout': 60})
        return response.text
    except Exception as e:
        error_msg = f"An error occurred while contacting the Gemini API: {e}\n\n"
        # 调用ListModels获取可用模型列表
        try:
            available_models = genai.list_models()
            error_msg += "### Available Gemini Models:\n"
            for m in available_models:
                error_msg += f"- **{m.name}**: {m.supported_generation_methods}\n"
        except Exception as list_error:
            error_msg += f"Failed to retrieve available models: {list_error}\n\n"
        
        error_msg += "\n### Local Fallback Analysis\n"
        return error_msg + generate_local_analysis(symbol, info)



def get_qianwen_analysis(symbol, info):
    """使用阿里云通义千问API进行Stock/ETF分析"""
    try:
        alibabacloud_api_key = st.secrets["QIANWEN_API_KEY"]
    except (FileNotFoundError, KeyError):
        error_msg = "QIANWEN_API_KEY not found in st.secrets. Please add it to your secrets file.\n\n"
        return error_msg + "### 本地替代分析\n" + generate_local_analysis(symbol, info)
    
    try:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {alibabacloud_api_key}"
        }
        
        asset_type = "ETF" if is_etf(info) else "Stock"
        # 构建提示词
        prompt = f"我需要分析{asset_type} {symbol}({info.get('longName', 'N/A')})的投资价值。\n\n"
        prompt += "以下是关键数据：\n"
        for key, value in info.items():
            prompt += f"{key}: {value}\n"
        
        prompt += f"\n请基于以上数据，以及盡你所知，为我提供一份{asset_type}分析报告，建議包含但不限制於以下內容：\n"
        prompt += "1. 简要概述\n"
        prompt += "2. 关键指标分析\n"
        prompt += "3. 優劣勢分析\n"
        prompt += "4. 投资建议\n"
        prompt += "5. 风险提示\n"
        prompt += "分析语言请使用你擅長的語言，保持专业、深入、简洁的风格。"
        
        # 构建请求体
        payload = {
            "model": "qwen-turbo",
            "input": {"prompt": prompt},
            "parameters": {"result_format": "text", "temperature": 0.7}
        }
        
        # 发送请求
        api_base = getattr(MySetts, 'alibabacloud_api_base', 'https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation')
        response = requests.post(api_base, headers=headers, data=json.dumps(payload), timeout=60)
        
        # 处理响应
        if response.status_code == 200:
            result = response.json()
            if "output" in result and "text" in result["output"]:
                return result["output"]["text"]
            else:
                error_msg = f"阿里云通义千问API返回格式异常: {result}\n\n"
                return error_msg + "### 本地替代分析\n" + generate_local_analysis(symbol, info)
        else:
            error_msg = f"阿里云通义千问API请求失败: HTTP {response.status_code}, {response.text}\n\n"
            return error_msg + "### 本地替代分析\n" + generate_local_analysis(symbol, info)
        
    except Exception as e:
        error_msg = f"阿里云通义千问API调用异常: {str(e)}\n\n"
        return error_msg + "### 本地替代分析\n" + generate_local_analysis(symbol, info)


@st.cache_data(ttl=36000)  # 缓存10小时，避免频繁调用API
def get_ai_analysis(symbol, info, ai_provider):
    """根据配置选择AI提供商进行Stock/ETF分析 - 只负责获取新的分析结果"""
    # 调用API获取分析结果（不再包含缓存逻辑）
    try:
        if ai_provider == 'alibabacloud':
            if "QIANWEN_API_KEY" not in st.secrets or not st.secrets["QIANWEN_API_KEY"]:
                return "Error: QIANWEN_API_KEY not found in st.secrets. Please add it to your secrets file to use the alibabacloud provider."
            analysis = get_qianwen_analysis(symbol, info)
        elif ai_provider == 'gemini':
            # The gemini function already checks for the key, so we can just call it.
            analysis = get_gemini_analysis(symbol, info)
        else:
            analysis = f"Error: Unknown AI provider '{ai_provider}'."
        
        return analysis
    except Exception as e:
        error_msg = f"AI分析失败: {str(e)}\n\n"
        return error_msg + "### 本地替代分析\n" + generate_local_analysis(symbol, info)


def get_local_fallback_response(user_question, current_analysis_symbol, language='zh'):
    """生成统一的本地替代回答"""
    if language == 'zh':
        local_response = """
### 本地替代回答
由于AI服务暂时不可用，这里是针对您问题的一些相关信息和建议：
        """
        
        if not user_question or user_question.strip().lower() in ['ok', 'ok, please', '好的', '好的，请', '继续', '请继续']:
            local_response += "\n您似乎是在请求继续我们的分析。以下是关于这个股票/ETF的一些额外信息和建议：\n"
            local_response += "\n1. 价格趋势分析：查看最近的价格走势可能帮助您判断短期市场情绪\n"
            local_response += "2. 基本面分析：关注公司财务状况、行业地位和未来发展前景\n"
            local_response += "3. 风险评估：考虑市场风险、行业风险和公司特定风险\n"
            local_response += "\n如果您对特定方面有兴趣，请提出更具体的问题，我将尽力为您提供帮助。"
        elif user_question.strip().lower().startswith(('what', '什么', 'how', '如何', 'why', '为什么', '建议')):
            local_response += f"\n您提出了关于'{current_analysis_symbol}'的问题。由于AI服务暂时不可用，\n"
            local_response += "建议您关注以下几个方面以获取更多信息：\n"
            local_response += "\n1. 查看最新的市场新闻和公告\n"
            local_response += "2. 分析财务报表和关键指标\n"
            local_response += "3. 研究行业趋势和竞争格局\n"
            local_response += "4. 了解宏观经济环境对该行业的影响\n"
            local_response += "\n您可以尝试提出更具体的问题，或者稍后再试以获取AI分析。"
        else:
            local_response += "\n感谢您的提问。由于AI服务暂时不可用，这里是一些通用建议：\n"
            local_response += "\n1. 重新检查您的问题是否清晰明确\n"
            local_response += "2. 确认您提供的股票/ETF信息是否完整\n"
            local_response += "3. 稍后再试或尝试使用其他AI提供商\n"
            local_response += "\n如需更详细的分析，请确保您的AI API密钥已正确配置。"
    else:
        # English response
        local_response = """
### Local Fallback Response
Due to AI service limitations, here are some relevant insights and suggestions:
        """
        
        if not user_question or user_question.strip().lower() in ['ok', 'ok, please', '好的', '好的，请', '继续', '请继续']:
            local_response += "\nIt seems you're requesting to continue our analysis. Here are some additional insights about this stock/ETF:\n"
            local_response += "\n1. Price trend analysis: Reviewing recent price movements can help gauge short-term market sentiment\n"
            local_response += "2. Fundamental analysis: Examine financial health, industry position, and future growth prospects\n"
            local_response += "3. Risk assessment: Consider market risk, industry risk, and company-specific risks\n"
            local_response += "\nIf you're interested in specific aspects, please ask more detailed questions and I'll do my best to help."
        else:
            local_response += f"\nYou've asked about '{current_analysis_symbol}'. With the current limitations,\n"
            local_response += "I recommend focusing on these areas for more information:\n"
            local_response += "\n1. Check the latest market news and announcements\n"
            local_response += "2. Analyze financial statements and key metrics\n"
            local_response += "3. Research industry trends and competitive landscape\n"
            local_response += "4. Understand macroeconomic environment impact on this industry\n"
            local_response += "\nYou can try asking more specific questions or try again later for AI analysis."
    
    return local_response



def get_gemini_response(user_question, current_analysis, current_analysis_symbol, current_analysis_info):
    """使用Google Gemini API回答用户的后续问题"""
    model = get_gemini_model()
    if model is None:
        error_msg = "GEMINI_API_KEY not found in st.secrets. Please add it to your secrets file.\n\n"
        return error_msg + get_local_fallback_response(user_question, current_analysis_symbol, 'en')
    
    # 构建回答用户问题的提示词
    prompt = f"You are a financial assistant. Based on the following analysis of {current_analysis_symbol} and additional information, please answer the user's question.\n\n"
    prompt += f"Current Analysis:\n{current_analysis}\n\n"
    prompt += f"Additional Information:\n"
    for key, value in current_analysis_info.items():
        prompt += f"- **{key}:** {value}\n"
    prompt += f"\n\nUser Question: {user_question}\n\n"
    prompt += "Please provide a clear, concise, and informative answer in Markdown format."  
    
    try:
        response = model.generate_content(prompt, request_options={'timeout': 60})
        return response.text
    except Exception as e:
        error_msg = f"An error occurred while contacting the Gemini API: {e}\n\n"
        # 调用ListModels获取可用模型列表
        try:
            available_models = genai.list_models()
            error_msg += "### Available Gemini Models:\n"
            for m in available_models:
                error_msg += f"- **{m.name}**: {m.supported_generation_methods}\n"
        except Exception as list_error:
            error_msg += f"Failed to retrieve available models: {list_error}\n\n"
        
        return error_msg + get_local_fallback_response(user_question, current_analysis_symbol, 'en')


def get_qianwen_response(user_question, current_analysis, current_analysis_symbol, current_analysis_info):
    """使用阿里云通义千问API回答用户的后续问题"""
    try:
        # 从st.secrets获取阿里云通义千问API密钥
        api_key = st.secrets["QIANWEN_API_KEY"]
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        
        # 构建回答用户问题的提示词
        prompt = f"你是一个金融助手。基于以下对{current_analysis_symbol}的分析和附加信息，请回答用户的问题。\n\n"
        prompt += f"当前分析：\n{current_analysis}\n\n"
        prompt += f"附加信息：\n"
        for key, value in current_analysis_info.items():
            prompt += f"- **{key}:** {value}\n"
        prompt += f"\n\n用户问题：{user_question}\n\n"
        prompt += "请提供一个清晰、简洁、信息丰富的回答，使用Markdown格式。"
        
        # 构建请求体
        payload = {
            "model": "qwen-turbo",
            "input": {"prompt": prompt},
            "parameters": {"result_format": "text", "temperature": 0.7}
        }
        
        # 发送请求
        api_base = getattr(MySetts, 'alibabacloud_api_base', 'https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation')
        response = requests.post(api_base, headers=headers, data=json.dumps(payload), timeout=60)
        
        # 处理响应
        if response.status_code == 200:
            result = response.json()
            if "output" in result and "text" in result["output"]:
                return result["output"]["text"]
            else:
                error_msg = f"阿里云通义千问API返回格式异常: {result}\n\n"
                return error_msg + "### 本地替代回答\n" + "抱歉，目前无法提供针对您问题的详细回答。"
        else:
            error_msg = f"阿里云通义千问API请求失败: HTTP {response.status_code}, {response.text}\n\n"
            return error_msg + "### 本地替代回答\n" + "抱歉，目前无法提供针对您问题的详细回答。"
        
    except Exception as e:
        error_msg = f"调用通义千问API时发生错误：{e}\n\n"
        return error_msg + "### 本地替代回答\n" + "抱歉，目前无法提供针对您问题的详细回答。"



def get_ai_response(user_question, current_analysis, current_analysis_provider, current_analysis_symbol, current_analysis_info):
    """获取AI对用户后续提问的回答"""
    try:
        if current_analysis_provider == 'alibabacloud':
            if "QIANWEN_API_KEY" not in st.secrets or not st.secrets["QIANWEN_API_KEY"]:
                return "Error: QIANWEN_API_KEY not found. Cannot get response from alibabacloud."
            return get_qianwen_response(user_question, current_analysis, current_analysis_symbol, current_analysis_info)
        elif current_analysis_provider == 'gemini':
            # The gemini function already checks for the key
            return get_gemini_response(user_question, current_analysis, current_analysis_symbol, current_analysis_info)
        else:
            return f"Error: Unknown AI provider '{current_analysis_provider}'."
    except Exception as e:
        error_msg = f"AI回答失败: {str(e)}\n\n"
        return error_msg + get_local_fallback_response(user_question, current_analysis_symbol)



def show_ai_analysis(symbol, info, ai_analysis, ai_provider, session_state):
    """显示AI分析结果和跟进提问功能 - 优化版"""
    # 初始化本地记录目录
    records_dir = Path("./.ai_ana_records")
    records_dir.mkdir(parents=True, exist_ok=True)
    
    # 获取缓存TTL（从settings.py获取）
    cache_ttl_seconds = MySetts.ai_analysis_cache_ttl_seconds
    
    # 检查是否已有符合条件的文件
    latest_file, session_id = ai_cache.check_cached_analysis_file(symbol, ai_provider, records_dir)
    
    # 初始化会话状态
    if 'current_analysis_session_id' not in session_state:
        session_state.current_analysis_session_id = {}
    
    # 立即设置会话ID（如果找到缓存文件）
    if session_id:
        session_state.current_analysis_session_id[symbol] = session_id
    
    # 创建基于股票代码的聊天历史键名（移到前面，确保在恢复历史时可用）
    chat_history_key = f'chat_history_{symbol}'
    
    with ai_analysis.container():
        # 检查是否有缓存的分析
        if session_id and latest_file and latest_file.exists():
            # 直接读取缓存的分析结果
            try:
                with open(latest_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # 提取AI分析部分
                    if "## 对话历史" in content:
                        analysis = content.split("## 对话历史")[0].strip()
                        
                        # 提取并恢复对话历史
                        chat_history_content = content.split("## 对话历史")[1].strip()
                        if chat_history_content and chat_history_key not in session_state:
                            # 初始化聊天历史
                            session_state[chat_history_key] = []
                            
                            # 分割用户提问和AI回答部分
                            import re
                            # 匹配用户提问和AI回答的模式
                            matches = re.findall(r'### 用户提问 \(.*?\)\n(.*?)\n\n### AI回答\n(.*?)(?=\n### 用户提问|$)', chat_history_content, re.DOTALL)
                            
                            # 将匹配到的对话添加到会话状态
                            for user_question, ai_response in matches:
                                session_state[chat_history_key].append({
                                    'role': 'user',
                                    'content': user_question.strip()
                                })
                                session_state[chat_history_key].append({
                                    'role': 'assistant',
                                    'content': ai_response.strip()
                                })
                    else:
                        analysis = content.strip()
            except Exception as e:
                analysis = f"Error reading cached analysis: {str(e)}"
                # 如果读取缓存失败，重新生成分析
                with st.spinner(f"Generating AI analysis for {symbol} using {ai_provider} ..."):
                    analysis = get_ai_analysis(symbol, info, ai_provider)
        else:
            # 生成AI分析报告
            with st.spinner(f"Generating AI analysis for {symbol} using {ai_provider} ..."):
                analysis = get_ai_analysis(symbol, info, ai_provider)
                
                # 如果是新生成的分析，保存到文件
                analysis_session_id = ai_cache.save_analysis_to_disk(symbol, analysis, ai_provider, records_dir)
                session_state.current_analysis_session_id[symbol] = analysis_session_id
        
        st.markdown("---")
        st.markdown("### AI-Powered Analysis")
        st.markdown(analysis)
        
        # 存储当前分析结果到会话状态
        session_state.current_analysis = analysis
        session_state.current_analysis_symbol = symbol
        session_state.current_analysis_info = info
        session_state.current_analysis_provider = ai_provider
        
        # 设置当前会话ID
        if session_id:
            session_state.current_analysis_session_id[symbol] = session_id
        
        # 添加AI跟进提问功能
        st.markdown("---")
        st.markdown("### 进一步提问 (Further Questions)")
        
        # 初始化聊天历史
        if chat_history_key not in session_state:
            session_state[chat_history_key] = []
        
        # 限制聊天历史长度，只保留最近20条消息
        MAX_CHAT_HISTORY = 20
        if len(session_state[chat_history_key]) > MAX_CHAT_HISTORY:
            session_state[chat_history_key] = session_state[chat_history_key][-MAX_CHAT_HISTORY:]
        
        # 显示聊天历史消息（在输入框上方）
        if session_state[chat_history_key]:
            for message in session_state[chat_history_key]:
                if message['role'] == 'user':
                    with st.chat_message("user"):
                        st.markdown(message['content'])
                else:
                    with st.chat_message("assistant"):
                        st.markdown(message['content'])
            
        # 用户输入区域和清除按钮布局
        col_input, col_clear = st.columns([4, 1])
        with col_input:
            # Add a dynamic key to reset state when the symbol changes
            # 用户输入框 - 始终显示在底部
            #user_question = st.chat_input("输入您的问题... (Type your question...)")
            user_question = st.chat_input("输入您的问题... (Type your question...)", key=f"chat_input_{symbol}")                
        with col_clear:
            # 清除聊天历史按钮 - 放在输入框旁边
            st.button("清除聊天 (Clear Chat)", key=f"clear_chat_btn_{symbol}", on_click=lambda key=chat_history_key: session_state.update({key: []}))
            
        # 处理新的用户问题
        if user_question:
            # 将用户问题添加到聊天历史
            session_state[chat_history_key].append({
                'role': 'user',
                'content': user_question
            })
            
            # 调用AI获取回答
            with st.spinner(f"AI正在思考... (AI is thinking...)"):
                ai_response = get_ai_response(
                    user_question,
                    session_state.current_analysis,
                    session_state.current_analysis_provider,
                    session_state.current_analysis_symbol,
                    session_state.current_analysis_info
                )
            
            # 将AI回答添加到聊天历史
            session_state[chat_history_key].append({
                'role': 'assistant',
                'content': ai_response
            })
            
            # 保存聊天记录到本地磁盘
            ai_cache.save_chat_history_to_disk(symbol, user_question, ai_response, session_state)
            
            # 强制重新渲染以显示最新聊天
            st.rerun()