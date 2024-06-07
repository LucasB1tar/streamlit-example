# -*- coding: utf-8 -*-
"""
Editor Spyder

Este é um arquivo de script temporário.
"""

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt


def tratamento(row):
    if pd.notnull(row['pre']):
        if 'NEGATIVO' in row['pre']:
            row['pre'] = 'NEG'
        else:
            row['pre'] = 'T'
    if pd.notnull(row['atual']):
        if 'NEGATIVO' in row['atual']:
            row['atual'] = 'NEG'
        else:
            row['atual'] = 'T'
    return row

def analise(row):
    if row['pre'] == 'NEG':
        if row['atual'] == 'NEG':
            row['Final'] = 'Remissao'
        elif row['atual'] == 'T':
            if row['ja_teve']:
                row['Final'] = 'Recaida'
            else:
                row['Final'] = 'Diagnostico'
    elif row['pre'] == 'T':
        if row['atual'] == 'NEG':
            row['Final'] = 'Remissao'
        elif row['atual'] == 'T':
            row['Final'] = 'Doenca Ativa'
    return row

# Carregar dados do Excel
df = pd.read_excel(r'./Tabela_Pacientes_LMA_Amanda.xlsx')

df['Paciente'] = df['Código BM'].str.extract(r'(\d{4})', expand=False)
df['Tempo'] = pd.to_datetime(df['Data da coleta'])

df[['Pré-transloc', 'Resultado da trasnlocação']] = df[['Pré-transloc', 'Resultado da trasnlocação']]
df['pre'] = df['Pré-transloc'].str.upper().str.strip()
df['atual'] = df['Resultado da trasnlocação'].str.upper().str.strip()

df = df.apply(tratamento, axis=1)
df['Final'] = None
df['ja_teve'] = False

ref_result = dict()
ref = list()
for _index, row in df.sort_values(by='Tempo').iterrows():
    if row['Paciente'] in ref:
        df.loc[_index, 'ja_teve'] = True
    if row['Paciente'] in ref_result:
        if pd.isnull(row['pre']):
            df.loc[_index, 'pre'] = ref_result[row['Paciente']]

    ref_result[row['Paciente']] = row['atual']
    if pd.notnull(row['atual']):    
        if 'T' in row['atual']:
            ref.append(row['Paciente'])
    if pd.notnull(row['pre']):    
        if 'T' in row['pre']:
            ref.append(row['Paciente'])

df[['pre', 'atual']] = df[['pre', 'atual']].fillna('NEG')
df = df.apply(analise, axis=1)

# Preencher valores NaN na coluna 'Final' com 'Desconhecido'
df['Final'] = df['Final'].fillna('Desconhecido')

# Calcular a contagem de meses desde a primeira consulta, de forma acumulativa
df['Meses_acumulados'] = df.groupby('Paciente')['Tempo'].transform(lambda x: (x - x.min()).dt.days // 30)

# Definir cores para cada paciente
pacientes = df['Paciente'].unique()
colors = {paciente: plt.cm.tab20(i / float(len(pacientes)-1)) for i, paciente in enumerate(pacientes)}

# Mapeamento das categorias da coluna 'Final' para valores numéricos no eixo Y
final_categories = df['Final'].unique()
final_mapping = {category: i for i, category in enumerate(final_categories)}

df['Final_mapped'] = df['Final'].map(final_mapping)

# Seleção de pacientes
with st.sidebar:
    selected_pacientes = st.multiselect('Selecione os pacientes', pacientes, default=pacientes)

# Função para plotar gráfico de linha
def plot_linha():
    fig, ax = plt.subplots(figsize=(12, 8))
    for paciente in selected_pacientes:
        subset = df[df['Paciente'] == paciente].sort_values(by='Meses_acumulados')
        ax.plot(subset['Meses_acumulados'], subset['Final_mapped'], color=colors[paciente], label=paciente, marker='o', markersize=10)
    ax.set_xlabel('Meses acumulados desde a primeira consulta')
    ax.set_ylabel('Resultado Final')
    ax.set_yticks(list(final_mapping.values()))
    ax.set_yticklabels(list(final_mapping.keys()))
    ax.set_title('Gráfico de Resultados por Paciente ao Longo do Tempo')
    ax.legend(title='Paciente', bbox_to_anchor=(1.05, 1), loc='upper left')
    ax.xaxis.set_major_locator(plt.MultipleLocator(3))
    ax.grid(True, which='both', linestyle='--', linewidth=0.5)
    st.pyplot(fig)

# Exibir o gráfico de linha
plot_linha()