ftelegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters
import sqlite3
import hashlib
import os
import random
import logging
# Токен бота
TOKEN = '7652690224:AAFjEQQk14n0i26Lw9a_ddiWCIk0FXSWxQ0'

# Логирование
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',

)

class User:
    def __init__(self, username, password):
        self.username = username
        self.password = self.hash_password(password)

    def hash_password(self, password):
        return hashlib.sha256(password.encode()).hexdigest()

    def check_password(self, password):
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS users
            (username TEXT PRIMARY KEY, password TEXT)
        ''')
        self.conn.commit()

    def add_user(self, username, password):
        user = User(username, password)
        self.cursor.execute('INSERT INTO users VALUES (?, ?)', (user.username, user.password))
        self.conn.commit()

    def check_user(self, username, password):
        self.cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
        user_data = self.cursor.fetchone()
        if user_data:
            user = User(user_data[0], user_data[1])
            return user.check_password(password)
        return False

class Game:
    def __init__(self, name, code):
        self.name = name
        self.code = code

class GameManager:
    def __init__(self, db_name):
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS games
            (name TEXT PRIMARY KEY, code TEXT)
        ''')
        self.conn.commit()

    def add_game(self, name, code):
        game = Game(name, code)
        self.cursor.execute('INSERT INTO games VALUES (?, ?)', (game.name, game.code))
        self.conn.commit()

    def get_game(self, name):
        self.cursor.execute('SELECT * FROM games WHERE name = ?', (name,))
        game_data = self.cursor.fetchone()
        if game_data:
            return Game(game_data[0], game_data[1])
        return None

user_manager = UserManager('users.db')
game_manager = GameManager('games.db')

def game1():
    number = random.randint(1, 10)
    attempts = 0
    while True:
        print("Угадай число: ")
        attempts += 1
        guess = input()
        if int(guess) == number:
            print("Поздравляем, вы угадали!")
            break
        elif int(guess) < number:
            print("Загаданное число больше!")
        else:
            print("Загаданное число меньше!")
    print("Вы угадали число за", attempts, "попыток!")

def game2():
    words = ["яблоко", "банан", "апельсин"]
    word = random.choice(words)
    attempts = 0
    while True:
        print("Угадай слово: ")
        attempts += 1
        guess = input()
        if guess == word:
            print("Поздравляем, вы угадали!")
            break
        else:
            print("Неправильно, попробуйте еще раз!")
    print("Вы угадали слово за", attempts, "попыток!")

def game3():
    choices = ["камень", "ножницы", "бумага"]
    computer_choice = random.choice(choices)
    print("Выберите камень, ножницы или бумага: ")
    user_choice = input()
    if user_choice == computer_choice:
        print("Ничья!")
    elif (user_choice == "камень" and computer_choice == "ножницы") or (user_choice == "ножницы" and computer_choice == "бумага") or (user_choice == "бумага" and computer_choice == "камень"):
        print("Вы выиграли!")
    else:
        print("Компьютер выиграл!")

def game4():
    board = ["1", "2", "3", "4", "5", "6", "7", "8", "9"]
    player_turn = "X"
    while True:
        print(" " + board[0] + " | " + board[1] + " | " + board[2])
        print("---+---+---")
        print(" " + board[3] + " | " + board[4] + " | " + board[5])
        print("---+---+---")
        print(" " + board[6] + " | " + board[7] + " | " + board[8])
        print("Игрок " + player_turn + ", введите номер клетки: ")
        move = input()
        if board[int(move) - 1] == "X" or board[int(move) - 1] == "O":
            print("Клетка уже занята, попробуйте еще раз!")
        else:
            board[int(move) - 1] = player_turn
            if (board[0] == board[1] == board[2] == player_turn) or (board[3] == board[4] == board[5] == player_turn) or (board[6] == board[7] == board[8] == player_turn) or (board[0] == board[3] == board[6] == player_turn) or (board[1] == board[4] == board[7] == player_turn) or (board[2] == board[5] == board[8] == player_turn):
                print("Игрок " + player_turn + " выиграл!")
                break
            player_turn = "O" if player_turn == "X" else "X"

def game5():
    word = "подводная лодка"
    attempts = 0
    while True:
        print("Угадай слово: ")
        attempts += 1
        guess = input()
        if guess == word:
            print("Поздравляем, вы угадали!")
            break
        else:
            print("Неправильно, попробуйте еще раз!")
    print("Вы угадали слово за", attempts, "попыток!")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Привет! 👋\n\n'
                                   'Доступные команды:\n'
                                   '/register - регистрация\n'
                                   '/login - вход\n'
                                   '/games - список игр\n'
                                   '/add_game - добавить игру')

async def register(update: Update, context: ContextTypes.DEFAULT_TYPE):
    username = update.message.text.split()[1]
    password = update.message.text.split()[2]
    user_manager.add_user(username, password)
    await update.message.reply_text('Вы зарегистрированы! 🎉')

async def login(update: Update, context: ContextTypes.DEFAULT_TYPE):
    username = update.message.text.split()[1]
    password = update.message.text.split()[2]
    if user_manager.check_user(username, password):
        await update.message.reply_text('Вы авторизованы! 🎉')
    else:
        await update.message.reply_text('Неправильный логин или пароль! 😔')

async def games(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Список игр:\n'
                                   '/game1 - Угадай число\n'
                                async def game2_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    game2()
    await update.message.reply_text("Игра завершена!")

async def game3_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    game3()
    await update.message.reply_text("Игра завершена!")

async def game4_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    game4()
    await update.message.reply_text("Игра завершена!")

async def game5_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    game5()
    await update.message.reply_text("Игра завершена!")

async def add_game(update: UpdaX
