from customtkinter import * 
from socket import * 
from PIL import Image 
from tkinter import filedialog 
from queue import Queue 
from pathlib import Path 
import threading, json, base64, io
from random import choices

HOST, PORT = '192.168.1.164', 12345 
TITLE, COLOR, MODE = ('LogiTalk', "#7d8a7e", 'dark') 
FOLDER = Path(__file__).resolve().parent 
messages = Queue() 
client_socket = socket(AF_INET, SOCK_STREAM) 
client_socket.connect((HOST, PORT)) # Спочатку запусти сервер 

# Змінні для ігрового автомата
coins = 100
spins = 0

def add_message(message, image=None): 
    label = CTkLabel(tbx, text=message, image=image, compound='top', wraplength=400) 
    label.image = image 
    label.pack(anchor='w', padx=10, pady=5) 

def send_data(data): 
    client_socket.sendall((json.dumps(data, ensure_ascii=False) + '\n').encode()) 

def send_msg(event=None): 
    message = entry.get().strip() 
    if message: 
        send_data({'type': 'text', 'text': message}) 
        entry.delete(0, 'end') 

def show_photo(author, data): 
    photo = Image.open(io.BytesIO(data)).convert('RGB') 
    photo.thumbnail((280, 200)) 
    image = CTkImage(photo, size=photo.size) 
    add_message(author + ': фото', image) 

def open_photo(path=None): 
    path = path or filedialog.askopenfilename(filetypes=[('Фото', '*.png *.jpg *.jpeg')]) 
    if not path: return 
    photo = Image.open(path).convert('RGB') 
    photo.thumbnail((640, 480)) 
    memory = io.BytesIO() 
    photo.save(memory, format='JPEG', quality=80) 
    photo_text = base64.b64encode(memory.getvalue()).decode() 
    send_data({'type': 'image', 'data': photo_text}) 

def handle_message(data): 
    if data['type'] == 'text': 
        add_message(data['username'] + ': ' + data['text']) 
    elif data['type'] == 'image': 
        show_photo(data['username'], base64.b64decode(data['data'])) 
    else: 
        add_message(data.get('text', '')) 

def receive_messages(): 
    try: 
        for line in client_socket.makefile('r', encoding='utf-8'): 
            messages.put(json.loads(line)) 
    except (OSError, ValueError): 
        pass 
    messages.put({'type': 'system', 'text': 'Сервер відключився. Перезапусти чат.'}) 

def check_messages(): 
    while not messages.empty(): 
        handle_message(messages.get()) 
    win.after(80, check_messages) 

def register(): 
    global username 
    username = name_entry.get().strip() 
    if not username: return 
    send_data({'type': 'join', 'username': username}) 
    registration.destroy() 
    chat.pack(fill='both', expand=True, padx=12, pady=12) 
    win.title(TITLE + ' — ' + username) 
    threading.Thread(target=receive_messages, daemon=True).start() 

# Логіка для ігрових спінів
def spin():
    global coins, spins
    if coins < 10:
        result.configure(text='Не вистачає монет. Натисни Бонус!')
        return
    
    coins -= 10
    reels = choices(['7', 'BAR', 'STAR'], k=3)
    if reels[0] == reels[1] == reels[2]:
        prize = 50
    elif reels[0] == reels[1] or reels[0] == reels[2] or reels[1] == reels[2]:
        prize = 10
    else:
        prize = 0
        
    coins += prize
    spins += 1
    
    combination = ' | '.join(reels)
    slots.configure(text=combination)
    wallet.configure(text=f'Монети: {coins} | Спіни: {spins}')
    result.configure(text=f'Виплата: {prize}. Вартість спіну: 10.')
    send_data({'type': 'text', 'text': f'[Спін] {combination}. Виплата: {prize}'})

def bonus():
    global coins
    coins += 20
    wallet.configure(text=f'Монети: {coins} | Спіни: {spins}')

set_appearance_mode(MODE) 
win = CTk() 
win.geometry('660x560') 
win.title(TITLE) 

registration = CTkFrame(win) 
registration.pack(expand=True) 
CTkLabel(registration, text=TITLE + ': введи ім’я').pack(padx=15, pady=10) 
name_entry = CTkEntry(registration, placeholder_text='Ім’я') 
name_entry.pack(padx=15, pady=10) 
CTkButton(registration, text='Увійти', command=register, fg_color=COLOR).pack(pady=10) 

chat = CTkFrame(win) 
title_label = CTkLabel(chat, text=TITLE, font=('Arial', 24, 'bold'), text_color=COLOR) 
title_label.pack(pady=8) 

# Панель гаманця та ігрового автомата
wallet = CTkLabel(chat, text='Монети: 100 | Спіни: 0')
wallet.pack()

slots = CTkLabel(chat, text='7 | BAR | STAR', font=('Arial', 27, 'bold'))
slots.pack()

result = CTkLabel(chat, text='3 однакові: 50 монет. 2 однакові: 10 монет. Різні: 0.')
result.pack()

tools = CTkFrame(chat)
tools.pack(pady=5)

CTkButton(tools, text='Крутити — 10 монет', command=spin, fg_color=COLOR).pack(side='left', padx=5)
CTkButton(tools, text='Бонус +20', command=bonus, fg_color=COLOR).pack(side='left', padx=5)

tbx = CTkScrollableFrame(chat) 
tbx.pack(fill='both', expand=True, padx=8) 

entry = CTkEntry(chat, placeholder_text='Повідомлення') 
entry.pack(fill='x', padx=8, pady=8) 
entry.bind('<Return>', send_msg) 

btn = CTkButton(chat, text='Надіслати', command=send_msg, fg_color=COLOR) 
btn.pack(side='left', padx=8, pady=8) 
CTkButton(chat, text='Фото', command=open_photo, fg_color=COLOR).pack(side='right', padx=8) 

if __name__ == '__main__': 
    check_messages() 
    win.mainloop()
