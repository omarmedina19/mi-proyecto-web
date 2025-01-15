import sqlite3

# Conexión a la base de datos
conn = sqlite3.connect('social_app.db')
cursor = conn.cursor()

# Verificar las tablas existentes
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()

# Mostrar el resultado
print("Tablas en la base de datos:", tables)

conn.close()
