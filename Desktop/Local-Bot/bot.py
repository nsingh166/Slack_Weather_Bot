import os
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

slack_bot_token = os.getenv("SLACK_BOT_TOKEN")
slack_app_token = os.getenv("SLACK_APP_TOKEN")

app = App(token=slack_bot_token)

client = OpenAI(
    base_url=os.getenv("OPENAI_BASE_URL"),
    api_key=os.getenv("OPENAI_API_KEY"),
)

thread_memory = {}

@app.event("app_mention")
def handle_mention_events(body, say):
    print("MENTION EVENT RECEIVED")

    event = body["event"]
    thread_ts = event.get("thread_ts") or event["ts"]

    user_message = event.get("text", "").strip()

    thread_memory[thread_ts] = [
        {"role": "user", "content": user_message}
    ]

    response = client.chat.completions.create(
        model="llama3.2:latest",
        messages=thread_memory[thread_ts]
    )

    reply_text = response.choices[0].message.content

    thread_memory[thread_ts].append(
        {"role": "assistant", "content": reply_text}
    )

    say(
        text=reply_text,
        thread_ts=thread_ts
    )

@app.event("message")
def handle_thread_messages(body, say):
    print("THREAD MESSAGE RECEIVED")

    event = body["event"]

    if event.get("bot_id"):
        return

    if event.get("channel_type") != "channel":
        return

    if "thread_ts" not in event:
        return

    thread_ts = event["thread_ts"]
    user_message = event.get("text", "").strip()

    if thread_ts not in thread_memory:
        return

    thread_memory[thread_ts].append(
        {"role": "user", "content": user_message}
    )

    response = client.chat.completions.create(
        model="llama3.2:latest",
        messages=thread_memory[thread_ts]
    )

    reply_text = response.choices[0].message.content

    thread_memory[thread_ts].append(
        {"role": "assistant", "content": reply_text}
    )

    say(
        text=reply_text,
        thread_ts=thread_ts
    )

if __name__ == "__main__":
    handler = SocketModeHandler(app, slack_app_token)
    handler.start()
