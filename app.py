import os
from flask import Flask, render_template_string, request
import discord

app = Flask(__name__)

TARGET_GUILD_ID = 1358768252012073071

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <title>Учет наказаний</title>
    <style>
        body { background-color: #313338; color: #dbdee1; font-family: sans-serif; padding: 20px; }
        .message-box { background: #2b2d31; padding: 10px 15px; margin-bottom: 10px; border-radius: 8px; max-width: 800px; }
        .content { font-size: 15px; margin-bottom: 8px; word-break: break-all; }
        .reactions { display: flex; gap: 6px; flex-wrap: wrap; }
        .reaction { background: #1e1f22; padding: 4px 8px; border-radius: 6px; font-size: 13px; display: flex; align-items: center; gap: 4px; border: 1px solid #35363c; }
        input, button { padding: 10px; font-size: 14px; border-radius: 5px; border: none; margin-right: 5px; }
        input { width: 350px; background: #1e1f22; color: #fff; }
        button { background: #5865f2; color: white; cursor: pointer; }
        button:hover { background: #4752c4; }
        .error { color: #f23f43; margin-top: 10px; }
    </style>
</head>
<body>
    <h2>Просмотр канала «учет наказаний»</h2>
    <form method="POST">
        <input type="text" name="token" placeholder="Введи свой Discord Token" value="{{ token or '' }}" required>
        <button type="submit">Загрузить</button>
    </form>
    {% if error %}
        <div class="error">{{ error }}</div>
    {% endif %}
    <hr style="border-color: #3f4147; margin: 20px 0;">
    {% if messages %}
        <div>
            {% for msg in messages %}
                <div class="message-box">
                    <div class="content">{{ msg.content }}</div>
                    {% if msg.reactions %}
                        <div class="reactions">
                            {% for emoji, count in msg.reactions.items() %}
                                <div class="reaction"><span>{{ emoji }}</span> <span>{{ count }}</span></div>
                            {% endfor %}
                        </div>
                    {% endif %}
                </div>
            {% endfor %}
        </div>
    {% endif %}
</body>
</html>
"""


@app.route("/", methods=["GET", "POST"])
def index():
  messages_data = []
  error = None
  token = ""

  if request.method == "POST":
    token = request.form.get("token")
    client = discord.Client()

    @client.event
    async def on_ready():
      nonlocal messages_data, error
      try:
        guild = client.get_guild(TARGET_GUILD_ID)
        if not guild:
          # Попытка подгрузить, если кэш пустой
          guild = await client.fetch_guild(TARGET_GUILD_ID)

        if guild:
          target_channel = None
          for channel in guild.text_channels:
            if "учет-наказаний" in channel.name:
              target_channel = channel
              break

          if target_channel:
            async for message in target_channel.history(limit=100):
              reactions_dict = {}
              for reaction in message.reactions:
                emoji = (
                    str(reaction.emoji)
                    if hasattr(reaction.emoji, "__str__")
                    else reaction.emoji.name
                )
                reactions_dict[emoji] = reaction.count

              messages_data.append({
                  "content": message.content,
                  "reactions": reactions_dict,
              })
          else:
            error = (
                "Канал с названнием 'учет-наказаний' не найден на этом сервере!"
            )
        else:
          error = "Сервер с указанным ID не найден или аккаунт на него не зашел."
      except Exception as e:
        error = f"Ошибка доступа: {e}"
      finally:
        await client.close()

    try:
      client.run(token)
    except Exception as e:
      error = f"Не удалось авторизоваться: {e}"

  return render_template_string(
      HTML_TEMPLATE, messages=messages_data, error=error, token=token
  )


if __name__ == "__main__":
  port = int(os.environ.get("PORT", 5000))
  app.run(host="0.0.0.0", port=port)
