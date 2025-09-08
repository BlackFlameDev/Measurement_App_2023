# Importing libraries

# GUI
import tkinter as tk
from tkinter import messagebox
import tkinter.ttk as ttk

# Data
import pandas as pd
import matplotlib.pyplot as plt
import json
import sqlite3

# System
import time
import requests
import threading
import datetime



app_info = """
    Program stworzony na potrzeby konkursu zorganizowanego przez 
    Powiatowy Ośrodek Doskonalenia Nauczycieli w Wodzisławiu Śląskim.
    
    Program pobiera dane z urządzenia firmy POL-EKO oraz magazynuje je w bazie danych. 
    Aplikacja ta umożliwia zapisanie zmagazynowanych danych do pliku Excel oraz ich podgląd w formie wykresu i tabeli.
    
    Autor: Dawid Kowalczyk
    Klasa: 4Ti
    Szkoła: Zespół Szkół Technicznych nr 1 im. Stanisława Staszica w Rybniku
"""

print(app_info)

# Rendering an app window
main = tk.Tk()
main.title("Aplikacja - Dawid Kowalczyk 4Ti")
main.geometry("800x500")


# Initializing database.
def database():
    conn = sqlite3.connect('data.db')

    create_table = """
                    CREATE TABLE IF NOT EXISTS Machine_Data (
                    IS_RUNNING TEXT, 
                    TEMPERATURE_VALUE REAL, 
                    TEMPERATURE_ERROR TEXT, 
                    DATETIME TEXT)
                   """
    conn.execute(create_table)

    conn.close()


# Exporting SQLite data to Excel spreadsheet
def export():

    date = datetime.datetime.now().strftime("%y-%m-%d")
    conn = sqlite3.connect('data.db')
    query = "SELECT * FROM Machine_Data"
    df = pd.read_sql(query, conn)
    excelwriter = pd.ExcelWriter('data_' + date + '.xlsx')

    df.to_excel(excelwriter)

    excelwriter.close()
    conn.close()

    print("Wyeksportowano dane do pliku Excel")


# Displaying measurement history
def view_history():
    for item in datatree.get_children():
        datatree.delete(item)  # Clear the table, so the records won't be written as new ones

    conn = sqlite3.connect('data.db')
    cur = conn.cursor()
    cur.execute("SELECT * FROM Machine_Data")
    rows = cur.fetchall()
    for row in rows:
        datatree.insert("", tk.END, values=row)
    conn.close()


# Connect with device and fetch data
def fetch():
    while True:
        current_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            host = host_entry.get()

            # Executing GET request to server.
            request = requests.get('http://' + host + ':56000/api/v1/school/status')
            jsondatatext = request.text
            data = json.loads(jsondatatext)

            runningdata = data['IS_RUNNING']
            tempjson = data['TEMPERATURE_MAIN']['value']
            temperror = data['TEMPERATURE_MAIN']['error']
            temp = tempjson / 100
            
            if runningdata is True:
                running = tk.StringVar(value="TAK")
                running_value.config(textvariable=running, disabledforeground="black")
            else:
                running = tk.StringVar(value="NIE")
                running_value.config(textvariable=running, disabledforeground="black")

            temperature = tk.StringVar(value=temp)
            temp_value.config(textvariable=temperature, disabledforeground="black")
            connection = tk.StringVar(value="POŁĄCZONO")
            connection_value.config(textvariable=connection, disabledforeground="green")

            print(runningdata, temp, temperror, current_date)
        except:
            running = tk.StringVar(value="NIE")
            temperature = tk.StringVar(value="-273")
            running_value.config(textvariable=running, disabledforeground="red")
            temp_value.config(textvariable=temperature, disabledforeground="red")
            connection = tk.StringVar(value="BRAK KOMUNIKACJI")
            connection_value.config(textvariable=connection, disabledforeground="red")

            print(False, -273, True, current_date)
        time.sleep(3)


# Saving current measurement as a SQLite database record
def insert():
    while True:
        current_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            host = host_entry.get()


            request = requests.get('http://' + host + ':56000/api/v1/school/status')
            jsondatatext = request.text
            data = json.loads(jsondatatext)

            runningdata = str(data['IS_RUNNING'])
            tempjson = data['TEMPERATURE_MAIN']['value']
            temperror = str(data['TEMPERATURE_MAIN']['error'])
            temp = tempjson / 100

            conn = sqlite3.connect('data.db')

            insert_query = """
            INSERT INTO Machine_Data 
            (IS_RUNNING, TEMPERATURE_VALUE, TEMPERATURE_ERROR, DATETIME) 
            VALUES 
            (?, ?, ?, ?)
            """
            insert_tuple = (runningdata, temp, temperror, current_date)
            cursor = conn.cursor()
            cursor.execute(insert_query, insert_tuple)
            conn.commit()

            conn.close()
        except:
            runningdata = str(False)
            temp = -273
            temperror = str(True)

            conn = sqlite3.connect('data.db')

            insert_query = """
            INSERT INTO Machine_Data 
            (IS_RUNNING, TEMPERATURE_VALUE, TEMPERATURE_ERROR, DATETIME) 
            VALUES 
            (?, ?, ?, ?)
            """
            insert_tuple = (runningdata, temp, temperror, current_date)
            cursor = conn.cursor()
            cursor.execute(insert_query, insert_tuple)
            conn.commit()

            conn.close()
        time.sleep(3)


# Generating and displaying temperature graph
def show_plot():
    conn = sqlite3.connect('data.db')
    cur = conn.cursor()
    cur.execute("SELECT TEMPERATURE_VALUE, DATETIME FROM Machine_Data")

    data = cur.fetchall()  # fetch data from database

    x = []
    y = []

    for row in data:
        x.append(row[1])
        y.append(row[0])

    plt.cla()
    plt.plot(x, y, '#ff3300', label='Temperatura')
    plt.ylim(bottom=-273, top=50)
    plt.tick_params(
        axis='x',
        which='both',
        bottom=False,
        top=False,
        labelbottom=False
    )
    plt.legend(loc='lower center')
    plt.tight_layout()
    plt.show()

    conn.close()


# User authentication
def login():
    username = "admin"
    password = ""
    if username_entry.get() == username and password_entry.get() == password:

        tk.messagebox.showinfo(title="Login", message="Zalogowano")


        username_entry.config(state="disabled")
        password_entry.config(state="disabled")
        host_entry.config(state="disabled")
        login_button.config(state="disabled")


        export_button.config(state="active")
        graph_button.config(state="active")
        table_button.config(state="active")

        print("Zalogowano")

        database() # initialize database connection

        # Threading
        t1 = threading.Thread(target=fetch)
        t1.daemon = True
        t1.start()
        t2 = threading.Thread(target=insert)
        t2.daemon = True
        t2.start()

    elif username_entry.get() == username and password_entry.get() != password:
        tk.messagebox.showerror(title="Login ERROR", message="Błąd logowania - niepoprawne hasło")
        print("Błąd logowania - niepoprawne hasło")
    elif username_entry.get() != username and password_entry.get() == password:
        tk.messagebox.showerror(title="Login ERROR", message="Błąd logowania - niepoprawny login")
        print("Błąd logowania - niepoprawny login")
    else:
        tk.messagebox.showerror(title="Login ERROR", message="Błąd logowania - niepoprawny login i hasło")
        print("Błąd logowania - niepoprawny login i hasło")


#================
# APP LAYOUT
#================

# Top frame - contains login and current measurement frames
topframe = tk.Frame()

# Login frame
loginframe = tk.Frame(topframe)

login_label = tk.Label(loginframe, text="Zaloguj się")  # Tytuł panelu logowania
username_label = tk.Label(loginframe, text='login')  # Etykieta pola nazwy użytkownika
username_entry = tk.Entry(loginframe)  # Pole nazwy użytkownika
password_entry = tk.Entry(loginframe, show="*")  # Pole hasła
password_label = tk.Label(loginframe, text="hasło")  # Etykieta pola hasła
host_label = tk.Label(loginframe, text="adres hosta")  # Etykieta pola adresu hosta
host_entry = tk.Entry(loginframe)  # Pole hosta
login_button = tk.Button(loginframe, text="Zaloguj", command=login)  # Przycisk logowania

# Current measurement frame
dataframe = tk.Frame(topframe)

data_label = tk.Label(dataframe, text="Dane urządzenia")
running_label = tk.Label(dataframe, text="Uruchomiony")
temp_label = tk.Label(dataframe, text="Temperatura")
connection_label = tk.Label(dataframe, text="Status połączenia")
running_value = tk.Entry(dataframe, state="disabled")
temp_value = tk.Entry(dataframe, state="disabled")
connection_value = tk.Entry(dataframe, state="disabled")

# Graph and data export buttons
export_button = tk.Button(dataframe, text="Eksportuj do pliku Excel", command=export, state="disabled")
graph_button = tk.Button(dataframe, text="Pokaż wykres", command=show_plot, state="disabled")
table_button = tk.Button(dataframe, text="Pokaż historię", command=view_history, state="disabled")

# Measurement history frame
tableframe = tk.Frame()
columns = ("IS_RUNNING", "TEMPERATURE_VALUE", "TEMPERATURE_ERROR", "DATE")  # tworzenie nazw kolumn
datatree = ttk.Treeview(tableframe, columns=columns, show="headings")  # tworzenie tabeli

verscroll = ttk.Scrollbar(tableframe, orient="vertical", command=datatree.yview)
verscroll.pack(side='right', fill='y')
datatree.configure(yscrollcommand=verscroll.set)

# Setting up measurement history table

# Headings
datatree.heading('IS_RUNNING', text="IS_RUNNING")
datatree.heading('TEMPERATURE_VALUE', text="TEMPERATURE_VALUE")
datatree.heading('TEMPERATURE_ERROR', text="TEMPERATURE_ERROR")
datatree.heading('DATE', text="DATE")

# Columns
datatree.column("#1", anchor=tk.CENTER, stretch=tk.NO, width=100)
datatree.column("#2", anchor=tk.CENTER, stretch=tk.NO, width=200)
datatree.column("#3", anchor=tk.CENTER, stretch=tk.NO, width=200)
datatree.column("#4", anchor=tk.CENTER, stretch=tk.NO, width=200)

datatree.bind('<Button-1>', 'break') # Prevent user from modifying the column width

# Rendering GUI frames

# Measurement History Frame
datatree.pack()

# Login Frame
login_label.grid(row=0, column=0, columnspan=2, pady=20)
host_label.grid(row=1, column=0)
host_entry.grid(row=1, column=1, pady=10)
username_label.grid(row=2, column=0)
username_entry.grid(row=2, column=1, pady=10)
password_label.grid(row=3, column=0)
password_entry.grid(row=3, column=1, pady=10)
login_button.grid(row=4, column=0, columnspan=2, pady=10)

# Current Measurement Frame
data_label.grid(column=0, row=0, columnspan=2, pady=20)
running_label.grid(row=1, column=0, pady=5, padx=5)
running_value.grid(row=1, column=1, pady=5)
temp_label.grid(row=2, column=0, pady=5, padx=5)
temp_value.grid(row=2, column=1, pady=5)
connection_label.grid(row=3, column=0, pady=5, padx=5)
connection_value.grid(row=3, column=1, pady=5)
export_button.grid(row=4, column=0, columnspan=2, pady=5)
graph_button.grid(row=5, column=0, pady=5)
table_button.grid(row=5, column=1, pady=5)

# Top Frame and Data History Frame.
loginframe.grid(row=0, column=0)
dataframe.grid(row=0, column=1, padx=20)
topframe.pack()
tableframe.pack()

main.resizable(False, False)  # Prevent user from resizing the window
main.mainloop()  # GUI Loop
