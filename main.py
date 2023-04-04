import os
import logging
import openai
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, filters, MessageHandler


history = {}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text='Привет, я бот использующий ChatGPT, задай мне любой вопрос и я постараюсь ответить на него.'
    )


async def ask_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    question = update.message.text
    chat_id = update.effective_chat.id

    try:
        history[chat_id].append({
            'role': 'user',
            'content': question,
        })
    except KeyError:
        history[chat_id] = [{
            'role': 'user',
            'content': question,
        }]

    wait_msg = await context.bot.send_message(
        chat_id=chat_id,
        text='...',
    )

    completion = await openai.ChatCompletion.acreate(
        model='gpt-3.5-turbo',
        messages=history[chat_id]
    )

    history[chat_id].append(completion.choices[0].message)

    if len(history[chat_id]) > 20:
        history[chat_id].pop(0)
        history[chat_id].pop(0)

    await context.bot.edit_message_text(
        chat_id=chat_id,
        message_id=wait_msg.message_id,
        text=completion.choices[0].message.content,
    )


if __name__ == '__main__':
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )

    load_dotenv('.env')

    openai.api_key = os.getenv('OPENAI_TOKEN')

    app = ApplicationBuilder().token(os.getenv('BOT_TOKEN')).build()

    start_handler = CommandHandler('start', start)
    ask_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), ask_question)

    app.add_handler(start_handler)
    app.add_handler(ask_handler)

    app.run_polling()
