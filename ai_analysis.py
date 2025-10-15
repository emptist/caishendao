# No Chinese in Code!!!

import google.generativeai as genai
import requests
import json
from settings import MySetts
import ai_cache
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
            if st.button(f"AI analysis for {symbol}"):
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
    if not info.get("numberOfAnalystOpinions"):
        has_category = 'category' in info
        has_etf_in_name = 'longName' in info and 'ETF' in info['longName'].upper()
        return has_category or has_etf_in_name
    return False


def generate_local_analysis(symbol, info):
    is_etf_flag = is_etf(info)
    asset_type = "ETF" if is_etf_flag else "Stock"
    
    if is_etf_flag:
        key_info = {
            "ETF Name": info.get("longName", "N/A"),
            "Symbol": info.get("symbol", "N/A"),
            "Current Price": info.get("currentPrice", "N/A"),
            "52 Week High": info.get("fiftyTwoWeekHigh", "N/A"),
            "52 Week Low": info.get("fiftyTwoWeekLow", "N/A"),
            "Market Cap": info.get("marketCap", "N/A"),
            "Category": info.get("category", "N/A"),
        }
    else:
        key_info = {
            "Company Name": info.get("longName", "N/A"),
            "Symbol": info.get("symbol", "N/A"),
            "Current Price": info.get("currentPrice", "N/A"),
            "Target Price": info.get("targetMeanPrice", "N/A"),
            "52 Week High": info.get("fiftyTwoWeekHigh", "N/A"),
            "52 Week Low": info.get("fiftyTwoWeekLow", "N/A"),
            "PE Ratio(TTM)": info.get("trailingPE", "N/A"),
            "Forward PE": info.get("forwardPE", "N/A"),
            "Market Cap": info.get("marketCap", "N/A"),
            "Analyst Rating": f"{info.get('recommendationKey', 'N/A')} (based on {info.get('numberOfAnalystOpinions', 'N/A')} opinions)",
        }

    # Create simplified markdown analysis
    markdown_analysis = f"#{symbol} ({key_info.get('Company Name') or key_info.get('ETF Name')}) {asset_type} Analysis\n\n"
    markdown_analysis += "## Key Metrics\n"
    for key, value in key_info.items():
        if key not in ["Company Name", "ETF Name", "Symbol"]:
            markdown_analysis += f"- **{key}:** {value}\n"
            
    markdown_analysis += "\n## Basic Assessment\n"
    
    if not is_etf_flag:
        if info.get("recommendationKey") == "buy":
            markdown_analysis += "- Analysts currently recommend buying this Stock.\n"
        elif info.get("recommendationKey") == "hold":
            markdown_analysis += "- Analysts currently recommend holding this Stock.\n"
        elif info.get("recommendationKey") == "sell":
            markdown_analysis += "- Analysts currently recommend selling this Stock.\n"
        
        if info.get("targetMeanPrice") and info.get("currentPrice"):
            try:
                target = float(info.get("targetMeanPrice"))
                current = float(info.get("currentPrice"))
                upside = ((target - current) / current) * 100
                if upside > 0:
                    markdown_analysis += f"- Based on analyst target price, there's potential {upside:.1f}% upside from current price.\n"
                else:
                    markdown_analysis += f"- Based on analyst target price, there's potential {-upside:.1f}% downside from current price.\n"
            except (ValueError, TypeError):
                pass
    else:
        # ETF analysis
        markdown_analysis += "- This is an ETF product, primarily focusing on the performance of its tracked market index, industry, or asset class.\n"
        if info.get('category'):
            markdown_analysis += f"- This ETF belongs to the {info.get('category')} category.\n"
            
    markdown_analysis += "\n*Note: This is a simplified local analysis generated when AI API requests fail or timeout.*"
    
    return markdown_analysis


@st.cache_resource
def get_gemini_model():
    """Get and cache Gemini model instance with fallback mechanism"""
    try:
        api_key = st.secrets["GEMINI_API_KEY"]
        genai.configure(api_key=api_key)
        
        # Define a model priority list based on actual available models shown in available_g_apis.md
        # Prioritize newer stable and fast versions
        model_candidates = [
            'gemini-2.5-flash',            # Latest fast model, suitable for most scenarios
            'gemini-2.5-pro',              # Latest professional model, more powerful
            'gemini-flash-latest',         # Latest fast model alias
            'gemini-pro-latest',           # Latest professional model alias
            'gemini-2.5-flash-lite',       # Lightweight fast model, faster response
            'gemini-2.0-flash',            # More stable fast model
            'gemini-2.0-pro-exp',          # More stable professional model
        ]
        
        # Try models in priority order
        for model_name in model_candidates:
            try:
                model = genai.GenerativeModel(model_name)
                return model, model_name  # Return model instance and model name
            except Exception:
                # Log failed model attempt but continue to next one
                pass
                
        # If all models fail, get available model list for debugging
        try:
            available_models = genai.list_models()
            model_names = [m.name for m in available_models if 'generateContent' in m.supported_generation_methods]
            if model_names:
                # Try to use the first available model that supports generateContent
                model = genai.GenerativeModel(model_names[0])
                return model, model_names[0]  # Return model instance and model name
        except Exception:
            pass
            
        return None, None  # Return None pair
    except (FileNotFoundError, KeyError):
        return None, None  # Return None pair
    except Exception as e:
        # Add more detailed error information if model initialization fails
        error_msg = f"Failed to initialize Gemini model: {e}"
        try:
            # Try to get available model list for more information
            available_models = genai.list_models()
            model_names = [m.name for m in available_models if 'generateContent' in m.supported_generation_methods]
            if model_names:
                error_msg += f"\n\nAvailable models: {', '.join(model_names)}"
        except Exception:
            pass
        
        st.error(error_msg)
        return None, None  # Return None pair


def get_gemini_analysis(symbol, info):
    """Use Google Gemini API for Stock/ETF analysis"""
    model, model_name = get_gemini_model()
    if model is None:
        error_msg = "GEMINI_API_KEY not found in st.secrets. Please add it to your secrets file.\n\n"
        return error_msg + "### Local Fallback Analysis\n" + generate_local_analysis(symbol, info)
    
    # Store model_name in session_state for later use
    if 'current_gemini_model' not in st.session_state:
        st.session_state.current_gemini_model = {}
    st.session_state.current_gemini_model[symbol] = model_name

    is_etf_flag = is_etf(info)
    # Build different prompts based on asset type
    if is_etf_flag:
        prompt = f"Analyze the following ETF: {symbol}. Below is a summary of its key data. Provide a concise analysis for a potential investor, including the ETF's investment objective, tracked market or industry performance, risk characteristics, and conclude with a suggested course of action (e.g., Buy, Hold, Watch). Format the output using Markdown.\\n\\n"
    else:
        prompt = f"Analyze the following stock: {symbol}. Below is a summary of its financial data. Provide a concise analysis for a potential investor. Highlight the most important positive and negative points and conclude with a suggested course of action (e.g., Buy, Hold, Sell, Watch). Format the output using Markdown.\\n\\n"

    # Add key information to prompt
    for key, value in info.items():
        prompt += f"- **{key}:** {value}\\n"

    try:
        response = model.generate_content(prompt, request_options={'timeout': 60})
        return response.text
    except Exception as e:
        error_msg = f"An error occurred while contacting the Gemini API: {e}\\n\\n"
        # Call ListModels to get available model list
        try:
            available_models = genai.list_models()
            error_msg += "### Available Gemini Models:\\n"
            for m in available_models:
                error_msg += f"- **{m.name}**: {m.supported_generation_methods}\\n"
        except Exception as list_error:
            error_msg += f"Failed to retrieve available models: {list_error}\\n\\n"
        
        error_msg += "\n### Local Fallback Analysis\n"
        return error_msg + generate_local_analysis(symbol, info)



def get_qianwen_analysis(symbol, info):
    """Use Alibaba Cloud Tongyi Qianwen API for Stock/ETF analysis"""
    try:
        alibabacloud_api_key = st.secrets["QIANWEN_API_KEY"]
    except (FileNotFoundError, KeyError):
        error_msg = "QIANWEN_API_KEY not found in st.secrets. Please add it to your secrets file.\n\n"
        return error_msg + "### Local Fallback Analysis\n" + generate_local_analysis(symbol, info)
    
    try:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {alibabacloud_api_key}"
        }
        
        asset_type = "ETF" if is_etf(info) else "Stock"
        # Build prompt
        prompt = f"I need to analyze the investment value of {asset_type} {symbol}({info.get('longName', 'N/A')}).\n\n"
        prompt += "Here are the key data points:\n"
        for key, value in info.items():
            prompt += f"{key}: {value}\n"
        
        prompt += f"\nPlease provide an {asset_type} analysis report based on the above data and your knowledge. The report should include but not be limited to:\n"
        prompt += "1. Brief overview\n"
        prompt += "2. Key indicators analysis\n"
        prompt += "3. Strengths and weaknesses analysis\n"
        prompt += "4. Investment recommendations\n"
        prompt += "5. Risk warnings\n"
        prompt += "Please use your preferred professional language, maintaining a professional, in-depth, and concise style."
        
        # Build request body
        payload = {
            "model": "qwen-turbo",
            "input": {"prompt": prompt},
            "parameters": {"result_format": "text", "temperature": 0.7}
        }
        
        # Send request
        api_base = getattr(MySetts, 'alibabacloud_api_base', 'https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation')
        response = requests.post(api_base, headers=headers, data=json.dumps(payload), timeout=60)
        
        # Process response
        if response.status_code == 200:
            result = response.json()
            if "output" in result and "text" in result["output"]:
                return result["output"]["text"]
            else:
                error_msg = f"Alibaba Cloud Tongyi Qianwen API returned abnormal format: {result}\\n\\n"
                return error_msg + "### Local Fallback Analysis\n" + generate_local_analysis(symbol, info)
        else:
            error_msg = f"Alibaba Cloud Tongyi Qianwen API request failed: HTTP {response.status_code}, {response.text}\\n\\n"
            return error_msg + "### Local Fallback Analysis\n" + generate_local_analysis(symbol, info)
        
    except Exception as e:
        error_msg = f"Alibaba Cloud Tongyi Qianwen API call exception: {str(e)}\\n\\n"
        return error_msg + "### Local Fallback Analysis\n" + generate_local_analysis(symbol, info)


@st.cache_data(ttl=36000)  # Cache for 10 hours to avoid frequent API calls
def get_ai_analysis(symbol, info, ai_provider):
    """Select AI provider for Stock/ETF analysis based on configuration - only responsible for getting new analysis results"""
    # Call API to get analysis results (no caching logic included anymore)
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
        error_msg = f"AI analysis failed: {str(e)}\\n\\n"
        return error_msg + "### Local Fallback Analysis\n" + generate_local_analysis(symbol, info)


def get_local_fallback_response(user_question, current_analysis_symbol, language='en'):
    """Generate unified local fallback response"""
    # Default to English response
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
    """Use Google Gemini API to answer user's follow-up questions"""
    model, model_name = get_gemini_model()
    if model is None:
        error_msg = "GEMINI_API_KEY not found in st.secrets. Please add it to your secrets file.\n\n"
        return error_msg + get_local_fallback_response(user_question, current_analysis_symbol, 'en')
    
    # Ensure model_name is stored in session_state
    if 'current_gemini_model' not in st.session_state:
        st.session_state.current_gemini_model = {}
    st.session_state.current_gemini_model[current_analysis_symbol] = model_name
    
    # Build prompt to answer user's question
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
        # Call ListModels to get available model list
        try:
            available_models = genai.list_models()
            error_msg += "### Available Gemini Models:\n"
            for m in available_models:
                error_msg += f"- **{m.name}**: {m.supported_generation_methods}\n"
        except Exception as list_error:
            error_msg += f"Failed to retrieve available models: {list_error}\n\n"
        
        return error_msg + get_local_fallback_response(user_question, current_analysis_symbol, 'en')


def get_qianwen_response(user_question, current_analysis, current_analysis_symbol, current_analysis_info):
    """Use Alibaba Cloud Tongyi Qianwen API to answer user's follow-up questions"""
    try:
        # Get Alibaba Cloud Tongyi Qianwen API key from st.secrets
        api_key = st.secrets["QIANWEN_API_KEY"]
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        
        # Build prompt to answer user's question
        prompt = f"You are a financial assistant. Based on the following analysis of {current_analysis_symbol} and additional information, please answer the user's question.\n\n"
        prompt += f"Current Analysis:\n{current_analysis}\n\n"
        prompt += f"Additional Information:\n"
        for key, value in current_analysis_info.items():
            prompt += f"- **{key}:** {value}\n"
        prompt += f"\n\nUser Question: {user_question}\n\n"
        prompt += "Please provide a clear, concise, and informative answer in Markdown format."
        
        # Build request body
        payload = {
            "model": "qwen-turbo",
            "input": {"prompt": prompt},
            "parameters": {"result_format": "text", "temperature": 0.7}
        }
        
        # Send request
        api_base = getattr(MySetts, 'alibabacloud_api_base', 'https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation')
        response = requests.post(api_base, headers=headers, data=json.dumps(payload), timeout=60)
        
        # Process response
        if response.status_code == 200:
            result = response.json()
            if "output" in result and "text" in result["output"]:
                return result["output"]["text"]
            else:
                error_msg = f"Alibaba Cloud Tongyi Qianwen API returned abnormal format: {result}\n\n"
                return error_msg + "### Local Fallback Response\n" + "Sorry, detailed answers cannot be provided at the moment."
        else:
            error_msg = f"Alibaba Cloud Tongyi Qianwen API request failed: HTTP {response.status_code}, {response.text}\n\n"
            return error_msg + "### Local Fallback Response\n" + "Sorry, detailed answers cannot be provided at the moment."
        
    except Exception as e:
        error_msg = f"Error occurred when calling Tongyi Qianwen API: {e}\n\n"
        return error_msg + "### Local Fallback Response\n" + "Sorry, detailed answers cannot be provided at the moment."



def get_ai_response(user_question, current_analysis, current_analysis_provider, current_analysis_symbol, current_analysis_info):
    """Get AI response to user's follow-up questions"""
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
        error_msg = f"AI response failed: {str(e)}\n\n"
        return error_msg + get_local_fallback_response(user_question, current_analysis_symbol)



def show_ai_analysis(symbol, info, ai_analysis, ai_provider, session_state):
    """Display AI analysis results and follow-up question functionality - optimized version"""
    # Initialize local records directory
    records_dir = Path("./.ai_ana_records")
    records_dir.mkdir(parents=True, exist_ok=True)
    
    # Get cache TTL (from settings.py)
    cache_ttl_seconds = MySetts.ai_analysis_cache_ttl_seconds
    
    # Check if there's a cached file that meets the criteria
    latest_file, session_id = ai_cache.check_cached_analysis_file(symbol, ai_provider, records_dir)
    
    # Initialize session state
    if 'current_analysis_session_id' not in session_state:
        session_state.current_analysis_session_id = {}
    
    # Set session ID immediately (if cache file found)
    if session_id:
        session_state.current_analysis_session_id[symbol] = session_id
    
    # Create chat history key name based on stock symbol (moved to front to ensure availability when restoring history)
    chat_history_key = f'chat_history_{symbol}'
    
    with ai_analysis.container():
        # Check if there's cached analysis
        if session_id and latest_file and latest_file.exists():
            # Directly read cached analysis results
            try:
                with open(latest_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # Extract AI analysis part
                    if "## Conversation History" in content:
                        analysis = content.split("## Conversation History")[0].strip()
                        
                        # Extract and restore conversation history
                        chat_history_content = content.split("## Conversation History")[1].strip()
                        if chat_history_content and chat_history_key not in session_state:
                            # Initialize chat history
                            session_state[chat_history_key] = []
                            
                            # Split user questions and AI answers
                            import re
                            # Pattern to match user questions and AI answers
                            matches = re.findall(r'### User Question \(.*?\)\n(.*?)\n\n### AI Answer\n(.*?)(?=\n### User Question|$)', chat_history_content, re.DOTALL)
                            
                            # Add matched conversations to session state
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
                # If reading cache fails, regenerate analysis
                with st.spinner(f"Generating AI analysis for {symbol} using {ai_provider} ..."):
                    analysis = get_ai_analysis(symbol, info, ai_provider)
        else:
            # Generate AI analysis report
            with st.spinner(f"Generating AI analysis for {symbol} using {ai_provider} ..."):
                analysis = get_ai_analysis(symbol, info, ai_provider)
                
                # If newly generated analysis, save to file
                analysis_session_id = ai_cache.save_analysis_to_disk(symbol, analysis, ai_provider, records_dir)
                session_state.current_analysis_session_id[symbol] = analysis_session_id
        
        st.markdown("---")
        # Get current model name and display in title
        model_info = ""
        if ai_provider == 'gemini' and 'current_gemini_model' in st.session_state and symbol in st.session_state.current_gemini_model:
            model_name = st.session_state.current_gemini_model[symbol]
            model_info = f"({model_name})"
        elif ai_provider == 'alibabacloud':
            model_info = "(qwen-turbo)"
            
        st.markdown(f"### AI-Powered Analysis{model_info}")
        st.markdown(analysis)
        
        # Store current analysis results in session state
        session_state.current_analysis = analysis
        session_state.current_analysis_symbol = symbol
        session_state.current_analysis_info = info
        session_state.current_analysis_provider = ai_provider
        
        if session_id:
            session_state.current_analysis_session_id[symbol] = session_id
        
        st.markdown("---")
        st.markdown("### Further Questions")
        
        if chat_history_key not in session_state:
            session_state[chat_history_key] = []
        
        MAX_CHAT_HISTORY = 20
        if len(session_state[chat_history_key]) > MAX_CHAT_HISTORY:
            session_state[chat_history_key] = session_state[chat_history_key][-MAX_CHAT_HISTORY:]
        
        if session_state[chat_history_key]:
            for message in session_state[chat_history_key]:
                if message['role'] == 'user':
                    with st.chat_message("user"):
                        st.markdown(message['content'])
                else:
                    with st.chat_message("assistant"):
                        st.markdown(message['content'])
            
        col_input, col_clear = st.columns([4, 1])
        with col_input:
            # Add a dynamic key to reset state when the symbol changes
            user_question = st.chat_input("Type your question...", key=f"chat_input_{symbol}")                
        with col_clear:
            st.button("Clear Chat History", key=f"clear_chat_btn_{symbol}", on_click=lambda key=chat_history_key: session_state.update({key: []}))
            
        if user_question:
            session_state[chat_history_key].append({
                'role': 'user',
                'content': user_question
            })
            
            with st.spinner(f"AI is thinking..."):
                ai_response = get_ai_response(
                    user_question,
                    session_state.current_analysis,
                    session_state.current_analysis_provider,
                    session_state.current_analysis_symbol,
                    session_state.current_analysis_info
                )
            
            session_state[chat_history_key].append({
                'role': 'assistant',
                'content': ai_response
            })
            
            ai_cache.save_chat_history_to_disk(symbol, user_question, ai_response, session_state)
            
            st.rerun()