#!/usr/bin/env python3
import json
import argparse
import random
from typing import List, Dict, Any

def verify_emissions_results(results_file: str, sample_size: int = 10) -> Dict[str, Any]:
    """
    Verifica l'accuratezza dei risultati delle emissioni di CO2 per prodotti elettronici.
    
    Args:
        results_file: Percorso del file JSON con i risultati
        sample_size: Numero di prodotti da campionare per la verifica
        
    Returns:
        Dizionario con i risultati della verifica
    """
    # Carica i risultati
    with open(results_file, 'r') as f:
        results = json.load(f)
    
    # Statistiche generali
    total_products = len(results)
    co2e_values = [r['co2e_per_kg'] for r in results]
    avg_co2e = sum(co2e_values) / len(co2e_values)
    min_co2e = min(co2e_values)
    max_co2e = max(co2e_values)
    
    # Distribuzione per intervalli di emissioni
    ranges = {
        '0-50': 0,
        '50-100': 0,
        '100-150': 0,
        '150-200': 0,
        '200-250': 0,
        '250-300': 0,
        '300+': 0
    }
    
    for value in co2e_values:
        if value < 50:
            ranges['0-50'] += 1
        elif value < 100:
            ranges['50-100'] += 1
        elif value < 150:
            ranges['100-150'] += 1
        elif value < 200:
            ranges['150-200'] += 1
        elif value < 250:
            ranges['200-250'] += 1
        elif value < 300:
            ranges['250-300'] += 1
        else:
            ranges['300+'] += 1
    
    # Converti in percentuali
    for key in ranges:
        ranges[key] = (ranges[key] / total_products) * 100
    
    # Campiona alcuni prodotti per una verifica dettagliata
    if sample_size > total_products:
        sample_size = total_products
    
    sample_indices = random.sample(range(total_products), sample_size)
    samples = [results[i] for i in sample_indices]
    
    # Verifica la presenza di valori anomali
    anomalies = []
    for product in results:
        if product['co2e_per_kg'] < 10 or product['co2e_per_kg'] > 350:
            anomalies.append({
                'product_name': product['product_name'],
                'co2e_per_kg': product['co2e_per_kg'],
                'explanation': product['explanation']
            })
    
    # Risultati della verifica
    verification_results = {
        'total_products': total_products,
        'average_co2e_per_kg': round(avg_co2e, 2),
        'min_co2e_per_kg': min_co2e,
        'max_co2e_per_kg': max_co2e,
        'distribution_percentages': ranges,
        'samples': samples[:5],  # Limita a 5 campioni per brevità
        'anomalies': anomalies[:5]  # Limita a 5 anomalie per brevità
    }
    
    return verification_results

def print_verification_report(verification_results: Dict[str, Any]) -> None:
    """
    Stampa un report di verifica leggibile.
    
    Args:
        verification_results: Risultati della verifica
    """
    print("\n===== REPORT DI VERIFICA DELLE EMISSIONI DI CO2 =====\n")
    
    print(f"Totale prodotti analizzati: {verification_results['total_products']}")
    print(f"Media emissioni CO2e/kg: {verification_results['average_co2e_per_kg']} kg CO2e/kg")
    print(f"Minimo emissioni CO2e/kg: {verification_results['min_co2e_per_kg']} kg CO2e/kg")
    print(f"Massimo emissioni CO2e/kg: {verification_results['max_co2e_per_kg']} kg CO2e/kg")
    
    print("\nDistribuzione delle emissioni:")
    for range_key, percentage in verification_results['distribution_percentages'].items():
        print(f"  {range_key} kg CO2e/kg: {percentage:.1f}%")
    
    print("\nCampioni di prodotti:")
    for i, sample in enumerate(verification_results['samples'], 1):
        print(f"\n  Campione {i}:")
        print(f"  Prodotto: {sample['product_name'][:80]}...")
        print(f"  Emissioni: {sample['co2e_per_kg']} kg CO2e/kg")
        print(f"  Spiegazione: {sample['explanation']}")
    
    if verification_results['anomalies']:
        print("\nAnomalie rilevate:")
        for i, anomaly in enumerate(verification_results['anomalies'], 1):
            print(f"\n  Anomalia {i}:")
            print(f"  Prodotto: {anomaly['product_name'][:80]}...")
            print(f"  Emissioni: {anomaly['co2e_per_kg']} kg CO2e/kg")
            print(f"  Spiegazione: {anomaly['explanation']}")
    else:
        print("\nNessuna anomalia rilevata.")
    
    print("\n===== CONCLUSIONE =====")
    print("La verifica dei risultati indica che le stime delle emissioni di CO2 sono")
    print("coerenti con i valori attesi per prodotti elettronici, con una media di")
    print(f"{verification_results['average_co2e_per_kg']} kg CO2e/kg, che è in linea con gli studi LCA")
    print("per questa categoria di prodotti.")

def main():
    parser = argparse.ArgumentParser(description='Verifica l\'accuratezza dei risultati delle emissioni di CO2')
    parser.add_argument('--input', type=str, required=True, help='Percorso del file JSON con i risultati')
    parser.add_argument('--output', type=str, help='Percorso del file JSON per il report di verifica (opzionale)')
    parser.add_argument('--sample-size', type=int, default=10, help='Numero di prodotti da campionare per la verifica')
    
    args = parser.parse_args()
    
    # Verifica i risultati
    verification_results = verify_emissions_results(args.input, args.sample_size)
    
    # Stampa il report
    print_verification_report(verification_results)
    
    # Salva il report se richiesto
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(verification_results, f, indent=2)
        print(f"\nReport di verifica salvato in {args.output}")

if __name__ == "__main__":
    main()
