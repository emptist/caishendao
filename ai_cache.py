import streamlit as st
import datetime
import os
import stat
import streamlit as st
from pathlib import Path
from settings import MySetts

# Ensure .ai_ana_records directory exists and has proper permissions
def ensure_safe_directory(directory_path):
    """Ensure directory exists and set appropriate permissions (0o700)"""
    if not os.path.exists(directory_path):
        os.makedirs(directory_path)
        # Set directory permissions to 0o700 (owner only read, write, execute)
        os.chmod(directory_path, stat.S_IRWXU)
    else:
        # Check and update permissions for existing directory
        current_mode = os.stat(directory_path).st_mode
        if (current_mode & 0o777) != stat.S_IRWXU:
            os.chmod(directory_path, stat.S_IRWXU)


def check_cached_analysis_file(symbol, ai_provider, records_dir):
    """Check if there are cached analysis files that meet time requirements"""
    try:
        # Ensure directory exists and has appropriate permissions
        ensure_safe_directory(records_dir)
        # Get cache TTL
        cache_ttl_seconds = MySetts.ai_analysis_cache_ttl_seconds
        current_time = datetime.datetime.now()
        
        # Find all analysis records for the specified stock and AI provider (MD format only)
        all_files = list(records_dir.glob(f"{symbol}_{ai_provider}_*.md"))
        
        if not all_files:
            return None, None
        
        # Sort by timestamp, newest first
        all_files.sort(key=lambda x: x.name, reverse=True)
        
        # Check if file is within cache time
        for filepath in all_files:
            try:
                # Extract timestamp from filename
                file_name = filepath.name
                # Format is: symbol_ai_provider_timestamp.md
                # Extract timestamp part (remove extension)
                base_name = file_name[:-3]  # Remove .md extension
                # Extract format: symbol_ai_provider_20250913_213909
                parts = base_name.split('_')
                if len(parts) >= 4:
                    # Combine date and time parts: 20250913_213909
                    timestamp_part = f"{parts[2]}_{parts[3]}"
                    try:
                        file_time = datetime.datetime.strptime(timestamp_part, "%Y%m%d_%H%M%S")
                        time_diff = (current_time - file_time).total_seconds()
                        
                        # Check if within cache time range
                        if time_diff <= cache_ttl_seconds:
                            session_id = base_name
                            return filepath, session_id
                    except ValueError:
                        continue
            except Exception as e:
                continue
        
        # If no files match cache time requirements, return None
        return None, None
    except Exception as e:
        return None, None


def load_cached_analysis(symbol, ai_provider, cache_ttl_seconds, records_dir):
    """Load AI analysis results from local cache that meet time requirements"""
    try:
        # Ensure directory exists and has appropriate permissions
        ensure_safe_directory(records_dir)
        # Find all analysis records for the specified stock and AI provider (MD format only)
        all_files = list(records_dir.glob(f"{symbol}_{ai_provider}_*.md"))
        
        if not all_files:
            return None
        
        # Sort by timestamp, newest first
        all_files.sort(key=lambda x: x.name, reverse=True)
        
        # Check if the newest record is within cache time
        current_time = datetime.datetime.now()
        
        for filepath in all_files:
            try:
                # Extract timestamp from filename
                file_name = filepath.name
                # Format is: symbol_ai_provider_timestamp.md
                # Extract timestamp part (remove extension)
                base_name = file_name[:-3]  # Remove .md extension
                # Extract format: symbol_ai_provider_20250913_213909
                parts = base_name.split('_')
                if len(parts) >= 4:
                    # Combine date and time parts: 20250913_213909
                    timestamp_part = f"{parts[2]}_{parts[3]}"
                    try:
                        # Try to parse timestamp from filename
                        file_time = datetime.datetime.strptime(timestamp_part, "%Y%m%d_%H%M%S")
                    except ValueError:
                        # If timestamp parsing fails, skip this file
                        continue
                else:
                    continue
                
                # Check if within cache time
                time_diff = (current_time - file_time).total_seconds()
                
                if time_diff <= cache_ttl_seconds:
                    # Within cache time, read and return analysis results
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                    # Extract detailed analysis section
                    analysis_start = content.find("## Detailed Analysis")
                    if analysis_start != -1:
                        analysis_end = content.find("## Conversation History", analysis_start)
                        if analysis_end != -1:
                            analysis = content[analysis_start:analysis_end].strip()
                        else:
                            analysis = content[analysis_start:].strip()
                    else:
                        analysis = content.strip()
                    return analysis
            except Exception as e:
                continue
        
        # If no files meet criteria, return None
        return None
    except Exception as e:
        return None


def save_analysis_to_disk(symbol, analysis, ai_provider, records_dir):
    """Save AI analysis results to local disk (Markdown format)"""
    try:
        # Ensure directory exists and has appropriate permissions
        ensure_safe_directory(records_dir)
        # Generate timestamped filename and session ID
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        session_id = f"{symbol}_{ai_provider}_{timestamp}"
        filename = f"{session_id}.md"
        filepath = records_dir / filename
        
        # Prepare Markdown content to save
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        md_content = f"""# AI Analysis Report: {symbol}

## Basic Information
- **Symbol**: {symbol}
- **AI Provider**: {ai_provider}
- **Generated Time**: {now}

## Detailed Analysis

{analysis}

---

## Conversation History
"""
        
        # Save to Markdown file
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(md_content)
            
        return session_id
    except Exception as e:
        # Log error without affecting program execution
        st.error(f"Failed to save AI analysis locally: {str(e)}")
        return None


def update_existing_analysis_file(filepath, symbol, analysis, ai_provider):
    """Update existing analysis file content while preserving conversation history"""
    try:
        # Read existing file content
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check if file contains conversation history section
        chat_history_start = content.find("\n## Conversation History\n")
        chat_history = content[chat_history_start:] if chat_history_start != -1 else ""
        
        # Create new file content (update analysis, preserve conversation history)
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        new_content = f"# AI Analysis Report: {symbol}\n"
        new_content += "\n## Basic Information\n"
        new_content += f"- **Symbol**: {symbol}\n"
        new_content += f"- **AI Provider**: {ai_provider}\n"
        new_content += f"- **Generated Time**: {current_time}\n"
        new_content += "\n## Detailed Analysis\n\n"
        new_content += f"{analysis}\n"
        new_content += chat_history  # Add original conversation history
        
        # Write back to file
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
    except Exception as e:
        st.error(f"Failed to update analysis file: {str(e)}")


def save_chat_history_to_disk(symbol, user_question, ai_response, session_state):
    """Save chat history to the corresponding Markdown analysis file"""
    try:
        # Ensure directory exists and has appropriate permissions
        records_dir = Path("./.ai_ana_records")
        ensure_safe_directory(records_dir)
        # Get current session ID
        if 'current_analysis_session_id' not in session_state or \
           symbol not in session_state.current_analysis_session_id:
            return
            
        session_id = session_state.current_analysis_session_id[symbol]
        records_dir = Path("./.ai_ana_records")
        filepath = records_dir / f"{session_id}.md"
        
        # Check if file exists
        if not filepath.exists():
            return
            
        # Read existing content
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Get current time
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Create new chat entry
        new_chat = f"""
### User Question ({now})
{user_question}

### AI Answer
{ai_response}
"""
        
        # Check if conversation history section already exists
        if "## Conversation History" in content:
            # Split content into analysis and conversation parts
            analysis_part, history_part = content.split("## Conversation History")
            # Update content with existing analysis + conversation marker + existing history + new chat
            updated_content = analysis_part.strip() + "\n\n## Conversation History\n" + history_part.strip() + new_chat
        else:
            # No conversation history section yet, add it before appending new chat
            updated_content = content.strip() + "\n\n## Conversation History" + new_chat
        
        # Write updated content back to file
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(updated_content)
            
    except Exception as e:
        # Log error without affecting program execution
        st.warning(f"Failed to save chat history locally: {str(e)}")