# Autor: Cristóbal Cabrera
# Proyecto: Eficiencia Energética App
# Fecha: Enero 2025

from flask import Flask, render_template, request, redirect, url_for
import sqlite3
from datetime import datetime
from update_calculations import calculate_and_update

app = Flask(__name__)
DB_PATH = 'C:/Users/totol/venv/proyecto-flask/database/eficiencia.db'

# Función para calcular el período en días
def calculate_period(start_date, end_date):
    start = datetime.strptime(start_date, "%d-%m-%Y")
    end = datetime.strptime(end_date, "%d-%m-%Y")
    return (end - start).days

# Ruta principal con formulario para agregar lecturas
@app.route('/', methods=['GET', 'POST'])
def add_reading():
    with sqlite3.connect(DB_PATH, timeout=10) as conn:
        cursor = conn.cursor()

        if request.method == 'POST':
            cliente = request.form['cliente']
            fecha_fin_raw = request.form['fecha_fin']  # Fecha en formato YYYY-MM-DD
            agua_nueva = request.form['agua'].replace(',', '.')
            gas_nuevo = request.form['gas'].replace(',', '.')

            # Convertir a float después de manejar separadores decimales
            agua_nueva = float(agua_nueva)
            gas_nuevo = float(gas_nuevo)

            # Convertir fecha_fin al formato esperado
            fecha_fin = datetime.strptime(fecha_fin_raw, "%Y-%m-%d").strftime("%d-%m-%Y")

            # Obtener la última fecha, consumos acumulados y calculados para el cliente
            cursor.execute('SELECT "Fecha fin periodo", "Agua (m3)", "Gas (m3)", "Período (días)" FROM Clientes WHERE CLIENTE = ? ORDER BY rowid DESC LIMIT 1', (cliente,))
            last_record = cursor.fetchone()

            if last_record:
                fecha_inicio = last_record[0]
                # Manejo del acumulativo
                agua_acumulada = (
                    float(last_record[1].replace(',', '.')) if isinstance(last_record[1], str) else last_record[1]
                ) + agua_nueva

                gas_acumulado = (
                    float(last_record[2].replace(',', '.')) if isinstance(last_record[2], str) else last_record[2]
                ) + gas_nuevo
                periodo_dias_total = last_record[3] + calculate_period(fecha_inicio, fecha_fin)
            else:
                # Si no hay registros previos, el nuevo consumo es el total
                fecha_inicio = fecha_fin
                agua_acumulada = agua_nueva
                gas_acumulado = gas_nuevo
                periodo_dias_total = calculate_period(fecha_inicio, fecha_fin)

            # Insertar nueva lectura con consumos acumulativos
            cursor.execute('''INSERT INTO Clientes (CLIENTE, "Fecha inicio periodo", "Fecha fin periodo", "Agua (m3)", "Gas (m3)", "Período (días)")
                              VALUES (?, ?, ?, ?, ?, ?)''',
                           (cliente, fecha_inicio, fecha_fin, agua_acumulada, gas_acumulado, periodo_dias_total))
            conn.commit()

            # Actualizar cálculos para todos los registros
            calculate_and_update()

            return render_template('success.html', message="Datos agregados y cálculos actualizados correctamente.")

        # Obtener lista de clientes para el selector
        cursor.execute("SELECT DISTINCT CLIENTE FROM Clientes")
        clientes = [row[0] for row in cursor.fetchall()]

    return render_template('form.html', clientes=clientes)

# Ruta para obtener datos dinámicamente cuando se selecciona un cliente
@app.route('/get_client_data/<cliente>', methods=['GET'])
def get_client_data(cliente):
    with sqlite3.connect(DB_PATH, timeout=10) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT "Fecha fin periodo", "Agua (m3)", "Gas (m3)" FROM Clientes WHERE CLIENTE = ? ORDER BY rowid DESC LIMIT 1', (cliente,))
        last_record = cursor.fetchone()

        if last_record:
            return {
                "fecha_inicio": last_record[0],
                "last_agua": last_record[1],
                "last_gas": last_record[2]
            }
        else:
            return {"error": "No se encontraron datos para este cliente."}, 404

# Ruta para actualizar los cálculos 
@app.route('/update_calculations', methods=['GET'])
def update_calculations():
    calculate_and_update()  # Ejecuta los cálculos
    return render_template('success.html', message="Cálculos actualizados correctamente.")

@app.route('/view_data', methods=['GET'])
def view_data():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Consulta para obtener registros
    cursor.execute('''
        SELECT rowid, CLIENTE, "Fecha inicio periodo", "Fecha fin periodo",
               "Agua (m3)", "Gas (m3)", "Período (días)", 
               "Eficiencia energética", "Emisión Co2 (Kg)", 
               "Valor m3 ACS", "Equivalencia arboles"
        FROM Clientes
        ORDER BY rowid DESC
    ''')
    registros = cursor.fetchall()
    conn.close()

    # Función para manejar conversiones a float
    def safe_float(value):
        if isinstance(value, str):
            value = value.replace(',', '.')  # Reemplazar comas por puntos
        try:
            return float(value) if value else 0
        except ValueError:
            return 0

    # Procesar registros para garantizar tipos seguros
    registros_limpios = [
        [
            registro[0],  # rowid
            registro[1],  # Cliente
            registro[2],  # Fecha inicio
            registro[3],  # Fecha fin
            safe_float(registro[4]),  # Agua (m³)
            safe_float(registro[5]),  # Gas (m³)
            int(registro[6]) if registro[6] else 0,  # Período (días)
            safe_float(registro[7]),  # Eficiencia energética
            safe_float(registro[8]),  # Emisión CO₂
            safe_float(registro[9]),  # Valor ACS
            safe_float(registro[10])  # Equivalencia árboles
        ]
        for registro in registros
    ]

    return render_template('view_data.html', registros=registros_limpios)

# Ruta para eliminar una fila
@app.route('/delete/<int:rowid>', methods=['POST'])
def delete_row(rowid):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM Clientes WHERE rowid = ?", (rowid,))
        conn.commit()
    return redirect(url_for('view_data'))

if __name__ == '__main__':
    app.run(debug=True)
