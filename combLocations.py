import itertools

def gerar_listas_customizadas(tamanho, location_areas):
    # Os valores são definidos pela variável location_areas 
    valores = list(range(location_areas))
    
    # Gera todas as combinações possíveis usando o tamanho escolhido
    combinacoes = itertools.product(valores, repeat=tamanho)
    
    for combinacao in combinacoes:
        print(list(combinacao))


location_areas = 2  # Isso vai gerar os valores: 0, 1, 2
tamanho_da_lista = 4  # O tamanho que as listas finais vão ter

# Executando a função
print(f"Valores disponíveis: de 0 até {location_areas - 1}")
print(f"Tamanho de cada lista: {tamanho_da_lista}\n")

gerar_listas_customizadas(tamanho_da_lista, location_areas)