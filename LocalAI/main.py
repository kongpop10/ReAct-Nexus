import gradio as gr
import requests

def get_response_from_api(message):
    url = "http://localhost:8080/v1/chat/completions"
    headers = {"Content-Type": "application/json"}
    payload = {
        "model": "LocalAI-functioncall-phi-4-v0.3",
        "messages": [{"role": "user", "content": message}],
        "temperature": 0.1
    }

    
    try:
        response = requests.post(url, json=payload, headers=headers).json()
        choices = response.get('choices', [])
        if choices:
            bot_message = choices[0].get('message', {}).get('content', "Sorry I don't understand")
        else:
            bot_message = "Sorry I don't understand"
    except Exception as e:
        print(f"An exception occurred: {e}")
        bot_message = "Sorry, I'm unable to reach the server right now."
    
    return bot_message

def chat_with_bot(message, chat_history):
    bot_message = get_response_from_api(message)
    chat_history.append((message, bot_message))
    return "", chat_history

with gr.Blocks() as demo:
    chatbot = gr.Chatbot()
    msg = gr.Textbox()
    clear = gr.ClearButton([msg, chatbot])

    msg.submit(chat_with_bot, [msg, chatbot], [msg, chatbot])

if __name__ == "__main__":
    demo.launch()