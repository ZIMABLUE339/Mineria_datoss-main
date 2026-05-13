import pandas as pd

df = pd.read_csv('data/ods_data.csv')

print('Estructura del Dataset:')
print(f'Forma: {df.shape}')
print(f'\nColumnas: {list(df.columns)}')
print(f'\nPrimeras filas:')
print(df.head(3))
print(f'\nInfo:')
print(df.info())
