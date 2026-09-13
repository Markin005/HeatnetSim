import random
import math
from collections import Counter

qtd_ue = 5000
lista_ue = [None] * qtd_ue

# Atribui um "slot" de tempo de 1 a 360 para cada UE
for i in range(len(lista_ue)):
    lista_ue[i] = random.randint(0, 359)

lista_chamadas = [0] * qtd_ue

print("Iniciando a simulação...")

# Simulação rodando por 1 HORA (3.600 segundos)
for _ in range(3600):
    for i in range(qtd_ue):
        valor_aleatorio = random.randint(0, 359)

        # Se o valor sorteado bater com a UE específica, ELA recebe +1
        if valor_aleatorio == lista_ue[i]:
            lista_chamadas[i] += 1


frequencia = Counter(lista_chamadas)
media_simulada = sum(lista_chamadas) / qtd_ue
lambda_poisson = 10.0  

soma_diferencas = 0.0  

# ARQUIVO TXT
nome_arquivo = "relatorio.txt"

with open(nome_arquivo, "w") as f:
    f.write("==============================================================================================\n")
    f.write("                                 RELATÓRIO DE SIMULAÇÃO                                       \n")
    f.write("==============================================================================================\n")
    f.write(f"Total de UEs analisadas: {qtd_ue}\n")
    f.write(f"Média de chamadas simulada por UE: {media_simulada:.4f}\n")
    f.write("==============================================================================================\n\n")

    # 2. Frequência, Probabilidades e Diferença
    f.write(f"{'Núm. Chamadas':<15} | {'Qtd. UEs':<10} | {'Prob. Simulada (%)':<20} | {'Prob. Poisson (%)':<20} | {'Diferença Absoluta (%)'}\n")
    f.write("-" * 95 + "\n")
    
    for num_chamadas in sorted(frequencia.keys()):
        qtd_vezes = frequencia[num_chamadas]
        
        # Cálculo da probabilidade simulada (Prática)
        prob_simulada = (qtd_vezes / qtd_ue) * 100
        
        # Cálculo da probabilidade de Poisson (Teórica)
        prob_poisson = ((lambda_poisson ** num_chamadas) * math.exp(-lambda_poisson) / math.factorial(num_chamadas)) * 100
        
        # Diferença absoluta entre a prática e a teoria
        diferenca = abs(prob_simulada - prob_poisson)
        soma_diferencas += diferenca
        
        f.write(f"{num_chamadas:<15} | {qtd_vezes:<10} | {prob_simulada:>18.4f}% | {prob_poisson:>18.4f}% | {diferenca:>21.4f}%\n")
    
    f.write("-" * 95 + "\n")
    
    f.write(f"SOMA TOTAL DAS DIFERENÇAS ABSOLUTAS: {soma_diferencas:.4f}%\n")
    f.write("==============================================================================================\n\n")

    # Detalhamento por UE
    f.write("--- DETALHAMENTO POR UE (ID | CHAMADAS) ---\n")
    for id_ue, num_chamadas in enumerate(lista_chamadas):
        f.write(f"{num_chamadas}\n")

print(f"Sucesso! O arquivo '{nome_arquivo}' foi gerado.")