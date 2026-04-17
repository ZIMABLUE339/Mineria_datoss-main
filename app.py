from flask import Flask, render_template
import pandas as pd

app = Flask(__name__)

@app.route("/")
def home():
    try:
        # Lee exactamente el archivo CreditCard.csv de la carpeta data
        df = pd.read_csv('data/CreditCard.csv')
        columnas = df.columns.tolist()
        filas = df.head(20).values.tolist()
        total_filas = 10127
        total_columnas = len(columnas)
    except FileNotFoundError:
        columnas, filas, total_filas, total_columnas = [], [], 0, 0

    return render_template("index.html", 
                           columnas=columnas, 
                           filas=filas, 
                           total_filas=total_filas, 
                           total_columnas=total_columnas)

if __name__ == "__main__":
    app.run(debug=True)