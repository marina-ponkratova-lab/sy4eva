import tkinter as tk
from tkinter import ttk, messagebox
import requests
import json
import os

# --- 1. Конфигурация и работа с данными (JSON) ---
DATA_DIR = "data"
DATA_FILE = os.path.join(DATA_DIR, "history.json")
API_URL = "https://api.exchangerate-api.com/v4/latest/EUR" # Базовая валюта для API

def ensure_data_dir_exists():
    """Создает каталог 'data', если его нет на диске."""
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
        with open(DATA_FILE, "w") as f:
            json.dump([], f)

def load_history():
    """Загружает историю конвертаций из файла JSON."""
    ensure_data_dir_exists()
    try:
        with open(DATA_FILE, "r") as file:
            return json.load(file)
    except (json.JSONDecodeError, FileNotFoundError):
        return []

def save_history(history_list):
    """Сохраняет историю в файл JSON."""
    ensure_data_dir_exists()
    with open(DATA_FILE, "w") as file:
        json.dump(history_list, file, indent=4)


# --- 2. Логика работы с API ---
def get_exchange_rates():
    """
    Получает актуальные курсы валют от API.
    Возвращает словарь с курсами или None в случае ошибки.
    """
    try:
        response = requests.get(API_URL)
        response.raise_for_status()
        data = response.json()
        # Проверяем, что запрос успешен (поле 'result')
        if data.get('result') == 'success':
            return data['rates']
        else:
            messagebox.showerror("Ошибка API", "Не удалось получить данные от сервера.")
            return None
    except requests.exceptions.RequestException as e:
        messagebox.showerror("Ошибка сети", f"Проверьте подключение к интернету:\n{str(e)}")
        return None


# --- 3. Логика GUI ---
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Currency Converter")
        self.geometry("700x500")
        self.resizable(False, False)
        self.configure(bg="#f0f8ff")
        
        # Загружаем историю и курсы валют при запуске
        self.history = load_history()
        self.rates = get_exchange_rates()
        
        self.create_widgets()
        self.update_history_display()

    def create_widgets(self):
        # --- Верхний фрейм: Параметры конвертации ---
        input_frame = tk.LabelFrame(self, text="Параметры конвертации", bg="#f0f8ff", padx=10, pady=10)
        input_frame.pack(pady=15, padx=20, fill="x")

        # Выбор валют
        currencies = ['EUR', 'USD', 'GBP', 'JPY', 'RUB', 'CNY', 'CHF']
        
        tk.Label(input_frame, text="Из:", bg="#f0f8ff").grid(row=0, column=0, padx=5)
        self.from_var = tk.StringVar(value="USD")
        from_menu = ttk.Combobox(input_frame, textvariable=self.from_var, values=currencies, state="readonly", width=5)
        from_menu.grid(row=0, column=1, padx=5)
        
        tk.Label(input_frame, text="В:", bg="#f0f8ff").grid(row=0, column=2, padx=5)
        self.to_var = tk.StringVar(value="EUR")
        to_menu = ttk.Combobox(input_frame, textvariable=self.to_var, values=currencies, state="readonly", width=5)
        to_menu.grid(row=0, column=3, padx=5)

        # Поле ввода суммы
        tk.Label(input_frame, text="Сумма:", bg="#f0f8ff").grid(row=0, column=4, padx=5)
        self.amount_entry = tk.Entry(input_frame, font=("Arial", 12), width=15)
        self.amount_entry.grid(row=0, column=5, padx=5)
        self.amount_entry.focus_set()

        # Кнопка конвертации
        btn_convert = tk.Button(
            input_frame,
            text="Конвертировать",
            command=self.convert_currency,
            bg="#4CAF50",
            fg="white",
            width=15,
            font=("Arial", 10)
        )
        btn_convert.grid(row=0, column=6, padx=20)

        # Результат
        self.result_label = tk.Label(
            input_frame,
            text="Результат появится здесь",
            font=("Arial", 14),
            bg="#e0f7fa",
            relief="solid",
            width=25,
            height=2
        )
        self.result_label.grid(row=1, column=0, columnspan=7, pady=15)


        # --- Нижний фрейм: История ---
        history_frame = tk.LabelFrame(self, text="История конвертаций", bg="#f0f8ff", padx=10, pady=10)
        history_frame.pack(pady=10, padx=20, fill="both", expand=True)
        
        self.history_tree = ttk.Treeview(
            history_frame,
            columns=("from", "to", "amount", "result"),
            show="headings"
        )
        
        # Настройка колонок
        self.history_tree.heading("from", text="Из")
        self.history_tree.heading("to", text="В")
        self.history_tree.heading("amount", text="Сумма")
        self.history_tree.heading("result", text="Результат")
        
        self.history_tree.column("from", width=80)
        self.history_tree.column("to", width=80)
        self.history_tree.column("amount", width=100)
        self.history_tree.column("result", width=100)
        
        self.history_tree.pack(fill="both", expand=True)
        
        btn_save_history = tk.Button(
            history_frame,
            text="Сохранить историю",
            command=lambda: save_history(self.history),
            bg="#FF9800",
            fg="white"
        )
        btn_save_history.pack(pady=5)


    def convert_currency(self):
        """Обрабатывает логику конвертации."""
        amount_str = self.amount_entry.get().strip()
        
        # Валидация ввода (Критерий 4: Сумма должна быть числом > 0)
        if not amount_str:
            messagebox.showwarning("Ошибка", "Поле суммы не должно быть пустым!")
            return
            
        try:
            amount = float(amount_str)
            if amount <= 0:
                raise ValueError
        except ValueError:
            messagebox.showwarning("Ошибка", "Сумма должна быть положительным числом!")
            return

        currency_from = self.from_var.get()
        currency_to = self.to_var.get()
        
        if not self.rates:
            messagebox.showerror("Ошибка данных", "Не удалось загрузить курсы валют. Проверьте интернет.")
            return

        # Логика конвертации через базовую валюту (EUR)
        try:
            # Переводим сумму в EUR (базовая валюта API)
            amount_in_base = amount / self.rates[currency_from]
            # Переводим из EUR в целевую валюту
            result_amount = amount_in_base * self.rates[currency_to]
            
            result_text = f"{amount:.2f} {currency_from} = {result_amount:.2f} {currency_to}"
            self.result_label.config(text=result_text)
            
            # Сохраняем в историю (в память)
            self.history.append({
                "from": currency_from,
                "to": currency_to,
                "amount": f"{amount:.2f}",
                "result": f"{result_amount:.2f}"
            })
            
            # Обновляем отображение истории в GUI
            self.update_history_display()
            
        except KeyError:
            messagebox.showerror("Ошибка данных", "Выбранная валюта не поддерживается.")


    def update_history_display(self):
        """Обновляет виджет Treeview с историей задач."""
        for i in self.history_tree.get_children():
            self.history_tree.delete(i)
            
        for entry in reversed(self.history): # Показываем последние сверху
            self.history_tree.insert("", "end", values=(
                entry["from"],
                entry["to"],
                entry["amount"],
                entry["result"]
            ))


# --- 4. Точка входа ---
if __name__ == '__main__':
    app = App()
    app.mainloop()
