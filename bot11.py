import os
import random
import aiosqlite
from telethon import TelegramClient, events, Button

# ================== CONFIG ==================
API_ID = 38546962
API_HASH = 'b47dfef6640d197c2becc164f0916365'
BOT_TOKEN = "7652690224:AAFjEQQk14n0i26Lw9a_ddiWCIk0FXSWxQ0"

DB_PATH = "database.db"
GAMES_DIR = "games"

# ================== FILES ==================
os.makedirs(GAMES_DIR, exist_ok=True)

# ================== BOT ==================
client = TelegramClient("bot", API_ID, API_HASH).start(bot_token=BOT_TOKEN)

# ================== DB INIT ==================
async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
        CREATE TABLE IF NOT EXISTS users(
            telegram_id INTEGER PRIMARY KEY,
            nickname TEXT,
            points INTEGER DEFAULT 0
        )
        """)
        await db.execute("""
        CREATE TABLE IF NOT EXISTS games(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            name_key TEXT UNIQUE,
            author_id INTEGER,
            filename TEXT
        )
        """)
        await db.commit()

# ================== STATE ==================
user_state = {}  # user_id -> dict

# ================== GAME API ==================
class GameAPI:
    def __init__(self, user_id, event):
        self.user_id = user_id
        self.event = event
        self.future = None

    async def send(self, text):
        await self.event.respond(text)

    async def add_score(self, pts):
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                "UPDATE users SET points = points + ? WHERE telegram_id=?",
                (pts, self.user_id)
            )
            await db.commit()

    async def get_input(self, prompt=""):
        await self.send(prompt)
        self.future = client.loop.create_future()
        return await self.future

    def set_input(self, text):
        if self.future and not self.future.done():
            self.future.set_result(text)

# ================== BUILT-IN GAMES ==================
async def guess_number(game_api):
    n = random.randint(1, 5)
    answer = await game_api.get_input("🎯 Угадай число от 1 до 5:")
    if answer.strip() == str(n):
        await game_api.send("✅ Угадал! +5 очков")
        await game_api.add_score(5)
    else:
        await game_api.send(f"❌ Нет, было {n}")

async def coin_flip(game_api):
    score = 0
    await game_api.send(
        "🎲 Игра: Орел или Решка!\nВыбирай: Орел (О) или Решка (Р)\nЧтобы закончить игру — напиши СТОП."
    )

    while True:
        choice = await game_api.get_input("Твой выбор (О/Р), или 'СТОП' чтобы выйти:")
        choice = choice.strip().upper()

        if choice == "СТОП":
            await game_api.send(f"🏁 Игра окончена! Твой счёт: {score}")
            return

        if choice not in ("О", "Р"):
            await game_api.send("❌ Неверный ввод! Введи 'О' или 'Р'")
            continue

        flip = random.choice(["О", "Р"])
        await game_api.send(f"🎲 Выпало: {flip}")

        if choice == flip:
            await game_api.send("✅ Ты угадал!")
            score += 1
            await game_api.add_score(1)
        else:
            await game_api.send("❌ Не угадал!")

        await game_api.send(f"Текущий счёт: {score}\n---")

BUILT_IN = {
    "🎯 Угадай число": guess_number,
    "🎲 Орёл и Решка": coin_flip
}

# ================== MENU ==================
async def main_menu(event):
    user_state.pop(event.sender_id, None)
    await event.respond(
        "🎮 Главное меню",
        buttons=[
            [Button.text("🎮 Игры"), Button.text("➕ Добавить игру")],
            [Button.text("🔍 Поиск игр")],
            [Button.text("👤 Профиль"), Button.text("🏆 Рейтинг")],
            [Button.text("📘 Инструкция"), Button.text("📄 Шаблон игры")]
        ]
    )

# ================== START ==================
@client.on(events.NewMessage(pattern="/start"))
async def start_bot(event):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR IGNORE INTO users(telegram_id, nickname) VALUES (?,?)",
            (event.sender_id, event.sender.username or "anon")
        )
        await db.commit()
    await main_menu(event)

# ================== HANDLER ==================
@client.on(events.NewMessage)
async def handler(event):
    uid = event.sender_id
    text = event.raw_text.strip()

    # game input
    if uid in user_state and user_state[uid].get("game"):
        user_state[uid]["game"].set_input(text)
        return

    # HOME
    if text.lower() in ("🏠 домой", "домой"):
        await main_menu(event)
        return

    # HELP / INSTRUCTION
    if text in ("/help", "📘 Инструкция"):
        await event.respond(
            "📌 Инструкция по добавлению игры\n\n"
            "1️⃣ Python 3.8+\n"
            "2️⃣ async def start(game_api) — главная функция игры\n"
            "3️⃣ await game_api.send('текст') — отправка сообщения\n"
            "4️⃣ await game_api.get_input('текст') — получение ответа (скобки обязательны!)\n"
            "5️⃣ await game_api.add_score(очки) — добавление очков\n"
            "6️⃣ Запрещено: print(), input(), os, sys, subprocess\n"
            "7️⃣ Пример минимальной игры в шаблоне\n"
            "🏠 Домой"
        )
        return

    # TEMPLATE
    if text == "📄 Шаблон игры":
        template = '''import random

async def start(game_api):
    number = random.randint(1, 5)
    answer = await game_api.get_input("🎯 Угадай число от 1 до 5:")
    if answer.strip() == str(number):
        await game_api.send("✅ Ты угадал!")
        await game_api.add_score(5)
    else:
        await game_api.send(f"❌ Нет, было {number}")'''
        await event.respond(f"📄 Шаблон игры:\n\n{template}\n\n🏠 Домой")
        return

    # GAMES LIST
    if text == "🎮 Игры":
        buttons = [[Button.text(name)] for name in BUILT_IN]
        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute("SELECT name FROM games") as c:
                for (n,) in await c.fetchall():
                    buttons.append([Button.text(n)])
        buttons.append([Button.text("🏠 Домой")])
        await event.respond("Выбери игру:", buttons=buttons)
        return

    # ADD GAME
    if text == "➕ Добавить игру":
        user_state[uid] = {"mode": "name"}
        await event.respond(
            "📌 Инструкция:\n"
            "1️⃣ Python 3.8+\n"
            "2️⃣ async def start(game_api)\n"
            "3️⃣ await game_api.send()\n"
            "4️⃣ await game_api.get_input() — обязательно с ()\n"
            "5️⃣ await game_api.add_score(очки)\n"
            "⚠️ Запрещено: print(), input(), os, sys, subprocess\n\n"
            "Введи название игры:"
        )
        return

    # ADD GAME FLOW
    if uid in user_state:
        state = user_state[uid]

        if state["mode"] == "name":
            name = text.strip()
            key = name.lower()

            async with aiosqlite.connect(DB_PATH) as db:
                async with db.execute("SELECT 1 FROM games WHERE name_key=?", (key,)) as c:
                    if await c.fetchone():
                        await event.respond("❌ Игра с таким названием уже есть!")
                        user_state.pop(uid)
                        return

            state["name"] = name
            state["key"] = key
            state["mode"] = "code"
            await event.respond("Теперь пришли код игры:")
            return

        if state["mode"] == "code":
            code = text

            # ----------------- ПРОВЕРКА КОДА -----------------
            allowed_imports = ["random", "math"]
            for line in code.splitlines():
                line_strip = line.strip()

                # разрешаем get_input
                if "get_input(" in line_strip:
                    continue

                # запрещённые функции
                if any(bad in line_strip for bad in ("print(", "input(", "os.", "sys.", "subprocess.")):
                    await event.respond(f"❌ Запрещённая функция: {line_strip}")
                    user_state.pop(uid)
                    return

                # проверка импортов
                if line_strip.startswith("import ") or line_strip.startswith("from "):
                    if not any(mod in line_strip for mod in allowed_imports):
                        await event.respond(f"❌ Недопустимый импорт: {line_strip}")
                        user_state.pop(uid)
                        return

            ns = {}
            try:
                exec(code, ns)
                if "start" not in ns or not callable(ns["start"]):
                    raise Exception("Нет async def start(game_api)")
            except Exception as e:
                await event.respond(f"❌ Ошибка в коде:\n{e}")
                user_state.pop(uid)
                return

            filename = f"{GAMES_DIR}/{state['key']}.py"
            with open(filename, "w", encoding="utf-8") as f:
                f.write(code)

            async with aiosqlite.connect(DB_PATH) as db:
                await db.execute(
                    "INSERT INTO games(name,name_key,author_id,filename) VALUES(?,?,?,?)",
                    (state["name"], state["key"], uid, filename)
                )
                await db.commit()

            await event.respond(f"✅ Игра «{state['name']}» добавлена!\n🏠 Домой")
            user_state.pop(uid)
            return

    # SEARCH
    if text == "🔍 Поиск игр":
        user_state[uid] = {"mode": "search"}
        await event.respond("Введите часть названия:")
        return

    if uid in user_state and user_state[uid].get("mode") == "search":
        q = text.lower()
        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute(
                "SELECT name FROM games WHERE name_key LIKE ?",
                (f"%{q}%",)
            ) as c:
                res = await c.fetchall()
        if res:
            await event.respond(
                "Найдено:",
                buttons=[[Button.text(n)] for (n,) in res] + [[Button.text("🏠 Домой")]]
            )
        else:
            await event.respond("Ничего не найдено 😢\n🏠 Домой")
        user_state.pop(uid)
        return

    # PROFILE
    if text == "👤 Профиль":
        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute("SELECT points FROM users WHERE telegram_id=?", (uid,)) as c:
                p = (await c.fetchone())[0]
        await event.respond(f"👤 Профиль\nОчки: {p}\n🏠 Домой")
        return

    # RATING
    if text == "🏆 Рейтинг":
        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute(
                "SELECT nickname, points FROM users ORDER BY points DESC LIMIT 10"
            ) as c:
                rows = await c.fetchall()
        txt = "🏆 Топ:\n" + "\n".join(f"{i+1}. {n} — {p}" for i,(n,p) in enumerate(rows))
        await event.respond(txt + "\n🏠 Домой")
        return

    # START BUILT-IN GAME
    if text in BUILT_IN:
        api = GameAPI(uid, event)
        user_state[uid] = {"game": api}
        await BUILT_IN[text](api)
        user_state.pop(uid, None)
        return

    # START USER GAME
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT name, filename FROM games") as c:
            games = await c.fetchall()

    for name, file in games:
        if text == name:
            api = GameAPI(uid, event)
            user_state[uid] = {"game": api}
            try:
                ns = {}
                exec(open(file, encoding="utf-8").read(), ns)
                await ns["start"](api)
            except Exception as e:
                await event.respond(f"❌ Ошибка игры:\n{e}")
            user_state.pop(uid, None)
            return

# ================== RUN ==================
client.loop.run_until_complete(init_db())
print("✅ Бот запущен")
client.run_until_disconnected()
