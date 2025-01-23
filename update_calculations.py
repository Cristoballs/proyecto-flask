import sqlite3

# Ruta a la base de datos
db_path = 'C:/proyecto-flask/database/eficiencia.db'

def calculate_and_update():
    with sqlite3.connect(db_path, timeout=10) as conn:
        cursor = conn.cursor()

        # Recuperar todos los registros de la tabla Clientes
        cursor.execute('SELECT rowid, "Agua (m3)", "Gas (m3)", "Período (días)" FROM Clientes')
        registros = cursor.fetchall()

        for registro in registros:
            rowid, agua, gas, periodo_dias = registro

            # Manejar valores nulos y cadenas con comas
            if isinstance(agua, str):
                agua = agua.replace(',', '.')
            if isinstance(gas, str):
                gas = gas.replace(',', '.')

            agua = float(agua) if agua else 0
            gas = float(gas) if gas else 0
            periodo_dias = int(periodo_dias) if periodo_dias else 0

            # Calcular métricas principales
            agua_por_periodo = agua / periodo_dias if periodo_dias > 0 else 0
            gas_por_periodo = gas / periodo_dias if periodo_dias > 0 else 0
            agua_por_dia = agua / periodo_dias if periodo_dias > 0 else 0
            gas_por_dia = gas / periodo_dias if periodo_dias > 0 else 0
            agua_por_mes = agua_por_dia * 30 if agua_por_dia > 0 else 0
            gas_por_mes = gas_por_dia * 30 if gas_por_dia > 0 else 0

            # Eficiencia Energética
            if gas > 0:
                energia_agua = agua * 997 * 4186 * 40  # J
                energia_gas = gas * 38128000  # J
                eficiencia = (energia_agua / energia_gas) * 100
            else:
                eficiencia = 0

            # Emisiones de CO₂ (usando fórmula gas/mes / 20)
            emisiones_co2 = gas_por_mes / 20 if gas_por_mes > 0 else 0

            # Valor ACS
            valor_acs = agua * 6.69 if agua > 0 else 0

            # Equivalencia en Árboles
            equivalencia_arboles = emisiones_co2 / 21 if emisiones_co2 > 0 else 0

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
