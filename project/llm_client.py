import json
from flask import current_app
from openai import OpenAI
import openai

# MediaTek Assistant API 的基礎 URL
ASSISTANT_API_BASE_URL = "https://prod.dvcbot.net/api/assts/v1"

def get_configured_client():
    """建立並回傳一個已設定好的 OpenAI 客戶端"""
    api_key = current_app.config.get('DVCBOT_API_KEY')
    if not api_key:
        raise ValueError("錯誤：找不到 DVCBOT_API_KEY，請檢查 .env 檔案。")
    
    return OpenAI(
        base_url=ASSISTANT_API_BASE_URL,
        api_key=api_key,
    )

def validate_grammar(sentence: str, grammar_rule: str) -> dict:
    """使用 MediaTek Assistant API 驗證文法"""
    try:
        client = get_configured_client()
        assistant_id = current_app.config.get('ASSISTANT_ID')
        if not assistant_id:
            raise ValueError("錯誤：找不到 ASSISTANT_ID，請檢查 .env 檔案。")

        user_prompt = f'文法規則: "{grammar_rule}"\n使用者句子: "{sentence}"'

        # Assistants API 工作流程
        thread = client.beta.threads.create()
        client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=user_prompt
        )
        run = client.beta.threads.runs.create_and_poll(
            thread_id=thread.id,
            assistant_id=assistant_id,
            timeout=30.0
        )

        if run.status == 'completed':
            messages = client.beta.threads.messages.list(thread_id=thread.id, order="desc")
            assistant_response = messages.data[0].content[0].text.value
            client.beta.threads.delete(thread_id=thread.id)
            
            try:
                result = json.loads(assistant_response)
                if 'correct' in result and 'explanation' in result:
                    return result
                else:
                    raise ValueError("JSON 格式不符預期")
            except (json.JSONDecodeError, ValueError) as e:
                print(f"錯誤：解析 LLM JSON 失敗 - {e}\n回傳內容: {assistant_response}")
                return {'correct': False, 'explanation': 'AI 回應格式錯誤，請稍後再試。'}
        else:
            error_message = f"執行失敗，狀態：{run.status}"
            if run.last_error:
                error_message += f", 錯誤: {run.last_error.message}"
            print(error_message)
            client.beta.threads.delete(thread_id=thread.id)
            return {'correct': False, 'explanation': 'AI 引擎處理失敗，請稍後再試。'}

    except openai.APIError as e:
        print(f"錯誤：API 錯誤: {e}")
        return {'correct': False, 'explanation': f'AI 伺服器錯誤: {e.message}'}
    except Exception as e:
        print(f"錯誤：發生未預期的錯誤: {e}")
        return {'correct': False, 'explanation': '系統發生未預期錯誤。'}