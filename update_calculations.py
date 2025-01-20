import sqlite3

# Ruta a la base de datos
db_path = 'C:/Users/totol/venv/proyecto-flask/database/eficiencia.db'

def calculate_and_update():
    with sqlite3.connect(db_path, timeout=10) as conn:
        cursor = conn.cursor()

        # Recuperar todos los registros de la tabla Clientes
        cursor.execute('SELECT rowid, "Agua (m3)", "Gas (m3)", "Período (días)" FROM Clientes')
        registros = cursor.fetchall()

        for registro in registros:
            rowid, agua, gas, periodo_dias = registro

            # Manejar valores con coma como separador decimal
            if isinstance(agua, str):
                agua = agua.replace(',', '.')
            if isinstance(gas, str):
                gas = gas.replace(',', '.')

            # Convertir agua y gas a float, y manejar valores nulos
            agua = float(agua) if agua else 0
            gas = float(gas) if gas else 0

            # Calcular m³ agua/periodo y m³ gas/periodo
            agua_por_periodo = agua / periodo_dias if agua and periodo_dias else None
            gas_por_periodo = gas / periodo_dias if gas and periodo_dias else None

            # Calcular m³ agua/día y m³ gas/día
            agua_por_dia = agua / periodo_dias if agua and periodo_dias else None
            gas_por_dia = gas / periodo_dias if gas and periodo_dias else None

            # Calcular m³ agua/mes y m³ gas/mes (30 días promedio)
            agua_por_mes = agua_por_dia * 30 if agua_por_dia else None
            gas_por_mes = gas_por_dia * 30 if gas_por_dia else None

            # Calcular Eficiencia Energética
            if gas > 0:
                energia_agua = agua * 997 * 4186 * 40  # J
                energia_gas = gas * 38128000  # J
                eficiencia = (energia_agua / energia_gas) * 100
            else:
                eficiencia = None

            # Calcular Emisiones de CO₂
            emisiones_co2 = gas * 2.75 if gas else None

            # Calcular Valor m³ ACS (ejemplo: tarifa fija de 6.69 por m³)
            valor_acs = agua * 6.69 if agua else None

            # Calcular Equivalencia en Árboles
            equivalencia_arboles = emisiones_co2 / 21 if emisiones_co2 else None

            # Actualizar los cálculos en la base de datos
            cursor.execute('''
                UPDATE Clientes
                SET "m3 agua/periodo" = ?,
                    "m3 gas/periodo" = ?,
                    "m3 agua/día" = ?,
                    "m3 gas/día" = ?,
                    "m3 agua/mes" = ?,
                    "m3 gas/mes" = ?,
                    "Eficiencia energética" = ?,
                    "Emisión Co2 (Kg)" = ?,
                    "Valor m3 ACS" = ?,
                    "Equivalencia arboles" = ?
                WHERE rowid = ?
            ''', (agua_por_periodo, gas_por_periodo, agua_por_dia, gas_por_dia,
                  agua_por_mes, gas_por_mes, eficiencia, emisiones_co2, valor_acs, equivalencia_arboles, rowid))

        conn.commit()

if __name__ == "__main__":
    calculate_and_update()
    print("Cálculos actualizados correctamente en la base de datos.")
