import json
import pandas as pd

# Percorso al file JSONL (aggiorna il percorso con quello del tuo file)
file_path = "meta_Electronics_SMALL.jsonl"

# Caricamento del file JSONL e visualizzazione delle prime righe
data = []
with open(file_path, 'r') as file:
    for line in file:
        data.append(json.loads(line))

# Convertire i dati in un DataFrame di Pandas per facilitare l'analisi
df = pd.DataFrame(data)

# Visualizzare le prime 5 righe per ispezionare la struttura dei dati
print("Anteprima del dataset:")
print(df.head())

# Visualizzare i nomi delle colonne per capire quali campi sono disponibili
print("\nNomi delle colonne nel dataset:")
print(df.columns)

# Verificare la presenza di valori nulli o mancanti
print("\nConteggio dei valori nulli per colonna:")
print(df.isnull().sum())

# Rimuovere eventuali righe con tutti i valori nulli (opzionale)
df = df.dropna(how='all')

# Salvare un nuovo file pulito (facoltativo, solo per confermare la pulizia)
df.to_json("cleaned_electronics_dataset.jsonl", orient='records', lines=True)

print("\nPulizia base completata. Dataset salvato come 'cleaned_electronics_dataset.jsonl'")
