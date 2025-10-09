import streamlit as st
import datetime
import os
import stat
import streamlit as st
from pathlib import Path
from settings import MySetts

# Ensure .ai_ana_records directory exists and has proper permissions
def ensure_safe_directory(directory_path):
    """确保目录存在并设置适当的权限(0o700)"""
    if not os.path.exists(directory_path):
        os.makedirs(directory_path)
        # 设置目录权限为0o700 (只有所有者可读、写、执行)
        os.chmod(directory_path, stat.S_IRWXU)
    else:
        # 检查并更新现有目录的权限
        current_mode = os.stat(directory_path).st_mode
        if (current_mode & 0o777) != stat.S_IRWXU:
            os.chmod(directory_path, stat.S_IRWXU)


def check_cached_analysis_file(symbol, ai_provider, records_dir):
    """检查是否存在符合缓存时间条件的文件"""
    try:
        # 确保目录存在并具有适当的权限
        ensure_safe_directory(records_dir)
        # 获取缓存TTL
        cache_ttl_seconds = MySetts.ai_analysis_cache_ttl_seconds
        current_time = datetime.datetime.now()
        
        # 查找指定股票和AI提供商的所有分析记录(仅支持MD格式)
        all_files = list(records_dir.glob(f"{symbol}_{ai_provider}_*.md"))
        
        if not all_files:
            return None, None
        
        # 按时间戳排序，最新的在前
        all_files.sort(key=lambda x: x.name, reverse=True)
        
        # 检查文件是否在缓存时间内
        for filepath in all_files:
            try:
                # 从文件名提取时间戳
                file_name = filepath.name
                # 格式是: symbol_ai_provider_timestamp.md
                # 提取出 timestamp 部分 (去掉扩展名)
                base_name = file_name[:-3]  # 去掉.md扩展名
                # 提取格式: symbol_ai_provider_20250913_213909
                parts = base_name.split('_')
                if len(parts) >= 4:
                    # 合并日期和时间部分: 20250913_213909
                    timestamp_part = f"{parts[2]}_{parts[3]}"
                    try:
                        file_time = datetime.datetime.strptime(timestamp_part, "%Y%m%d_%H%M%S")
                        time_diff = (current_time - file_time).total_seconds()
                        
                        # 检查是否在缓存时间范围内
                        if time_diff <= cache_ttl_seconds:
                            session_id = base_name
                            return filepath, session_id
                    except ValueError:
                        continue
            except Exception as e:
                continue
        
        # 如果没有符合缓存时间的文件，返回None
        return None, None
    except Exception as e:
        return None, None


def load_cached_analysis(symbol, ai_provider, cache_ttl_seconds, records_dir):
    """从本地加载符合缓存时间要求的AI分析结果"""
    try:
        # 确保目录存在并具有适当的权限
        ensure_safe_directory(records_dir)
        # 查找指定股票和AI提供商的所有分析记录(仅支持MD格式)
        all_files = list(records_dir.glob(f"{symbol}_{ai_provider}_*.md"))
        
        if not all_files:
            return None
        
        # 按时间戳排序，最新的在前
        all_files.sort(key=lambda x: x.name, reverse=True)
        
        # 检查最新的记录是否在缓存时间内
        current_time = datetime.datetime.now()
        
        for filepath in all_files:
            try:
                # 从文件名中提取时间戳
                file_name = filepath.name
                # 格式是: symbol_ai_provider_timestamp.md
                # 提取出 timestamp 部分 (去掉扩展名)
                base_name = file_name[:-3]  # 去掉.md扩展名
                # 提取格式: symbol_ai_provider_20250913_213909
                parts = base_name.split('_')
                if len(parts) >= 4:
                    # 合并日期和时间部分: 20250913_213909
                    timestamp_part = f"{parts[2]}_{parts[3]}"
                    try:
                        # 尝试解析文件名中的时间戳
                        file_time = datetime.datetime.strptime(timestamp_part, "%Y%m%d_%H%M%S")
                    except ValueError:
                        # 如果无法解析时间戳，则跳过此文件
                        continue
                else:
                    continue
                
                # 检查是否在缓存时间内
                time_diff = (current_time - file_time).total_seconds()
                
                if time_diff <= cache_ttl_seconds:
                    # 在缓存时间内，读取并返回分析结果
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                    # 提取详细分析部分
                    analysis_start = content.find("## 详细分析")
                    if analysis_start != -1:
                        analysis_end = content.find("## 对话历史", analysis_start)
                        if analysis_end != -1:
                            analysis = content[analysis_start:analysis_end].strip()
                        else:
                            analysis = content[analysis_start:].strip()
                    else:
                        analysis = content.strip()
                    return analysis
            except Exception as e:
                continue
        
        # 如果没有符合条件的文件，返回None
        return None
    except Exception as e:
        return None


def save_analysis_to_disk(symbol, analysis, ai_provider, records_dir):
    """将AI分析结果保存到本地磁盘(Markdown格式)"""
    try:
        # 确保目录存在并具有适当的权限
        ensure_safe_directory(records_dir)
        # 生成带时间戳的文件名和会话ID
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        session_id = f"{symbol}_{ai_provider}_{timestamp}"
        filename = f"{session_id}.md"
        filepath = records_dir / filename
        
        # 准备要保存的Markdown内容
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        md_content = f"""# AI分析报告: {symbol}

## 基本信息
- **股票代码**: {symbol}
- **AI提供商**: {ai_provider}
- **生成时间**: {now}

## 详细分析

{analysis}

---

## 对话历史
"""
        
        # 保存到Markdown文件
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(md_content)
            
        return session_id
    except Exception as e:
        # 记录错误但不影响程序运行
        st.error(f"保存AI分析到本地失败: {str(e)}")
        return None


def update_existing_analysis_file(filepath, symbol, analysis, ai_provider):
    """更新现有分析文件内容，保留对话历史"""
    try:
        # 读取现有文件内容
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查是否包含对话历史部分
        chat_history_start = content.find("\n## 对话历史\n")
        chat_history = content[chat_history_start:] if chat_history_start != -1 else ""
        
        # 创建新的文件内容（更新分析，保留对话历史）
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        new_content = f"# AI分析报告: {symbol}\n"
        new_content += "\n## 基本信息\n"
        new_content += f"- **股票代码**: {symbol}\n"
        new_content += f"- **AI提供商**: {ai_provider}\n"
        new_content += f"- **生成时间**: {current_time}\n"
        new_content += "\n## 详细分析\n\n"
        new_content += f"{analysis}\n"
        new_content += chat_history  # 添加原有的对话历史
        
        # 写回文件
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
    except Exception as e:
        st.error(f"更新分析文件失败: {str(e)}")


def save_chat_history_to_disk(symbol, user_question, ai_response, session_state):
    """将聊天历史保存到对应的Markdown分析文件中"""
    try:
        # 确保目录存在并具有适当的权限
        records_dir = Path("./.ai_ana_records")
        ensure_safe_directory(records_dir)
        # 获取当前会话ID
        if 'current_analysis_session_id' not in session_state or \
           symbol not in session_state.current_analysis_session_id:
            return
            
        session_id = session_state.current_analysis_session_id[symbol]
        records_dir = Path("./.ai_ana_records")
        filepath = records_dir / f"{session_id}.md"
        
        # 检查文件是否存在
        if not filepath.exists():
            return
            
        # 读取现有内容
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # 获取当前时间
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 添加新的对话历史
        new_chat = f"""
### 用户提问 ({now})
{user_question}

### AI回答
{ai_response}
"""
        
        # 保存更新后的内容
        with open(filepath, 'a', encoding='utf-8') as f:
            f.write(new_chat)
            
    except Exception as e:
        # 记录错误但不影响程序运行
        st.warning(f"保存聊天历史到本地失败: {str(e)}")