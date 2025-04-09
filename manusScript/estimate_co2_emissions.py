#!/usr/bin/env python3
import json
import re
import pandas as pd
import numpy as np

# Fattori di emissione per materiali comuni in kg CO2e/kg
# Fonti: 
# - Ecoinvent database
# - ICE (Inventory of Carbon and Energy) database
# - IPCC (Intergovernmental Panel on Climate Change)
# - Studi scientifici su LCA di prodotti elettronici
MATERIAL_EMISSION_FACTORS = {
    'plastic': 3.5,  # kg CO2e/kg (media di diversi tipi di plastica)
    'silicone': 5.2,  # kg CO2e/kg
    'vinyl': 3.8,  # kg CO2e/kg
    'aluminum': 8.24,  # kg CO2e/kg
    'tempered glass': 1.44,  # kg CO2e/kg
    'glass': 1.44,  # kg CO2e/kg
    'leather': 17.0,  # kg CO2e/kg
    'neoprene': 4.5,  # kg CO2e/kg
    'alloy steel': 2.89,  # kg CO2e/kg
    'steel': 2.89,  # kg CO2e/kg
    'nylon': 7.2,  # kg CO2e/kg
    'ethylene vinyl acetate': 3.1,  # kg CO2e/kg
    'polyester': 5.5,  # kg CO2e/kg
    'cotton': 5.9,  # kg CO2e/kg
    'abs': 3.8,  # kg CO2e/kg (Acrylonitrile Butadiene Styrene)
    'polycarbonate': 7.6,  # kg CO2e/kg
    'copper': 3.81,  # kg CO2e/kg
    'lithium-ion battery': 12.5,  # kg CO2e/kg
    'pcb': 60.0,  # kg CO2e/kg (Printed Circuit Board)
    'rubber': 3.18,  # kg CO2e/kg
    'carbon fiber': 31.0,  # kg CO2e/kg
    'wood': 0.86,  # kg CO2e/kg
    'paper': 1.32,  # kg CO2e/kg
    'cardboard': 1.07,  # kg CO2e/kg
    'default': 5.0  # kg CO2e/kg (valore di default per materiali sconosciuti)
}

# Fattori di emissione per categorie di prodotti elettronici in kg CO2e/kg
# Basati su studi LCA di prodotti elettronici
CATEGORY_EMISSION_FACTORS = {
    'smartphones': 80.0,  # kg CO2e/kg
    'laptops': 340.0,  # kg CO2e/kg
    'tablets': 120.0,  # kg CO2e/kg
    'desktop computers': 280.0,  # kg CO2e/kg
    'monitors': 220.0,  # kg CO2e/kg
    'televisions': 200.0,  # kg CO2e/kg
    'cameras': 170.0,  # kg CO2e/kg
    'headphones': 60.0,  # kg CO2e/kg
    'speakers': 40.0,  # kg CO2e/kg
    'printers': 100.0,  # kg CO2e/kg
    'routers': 130.0,  # kg CO2e/kg
    'hard drives': 190.0,  # kg CO2e/kg
    'ssds': 210.0,  # kg CO2e/kg
    'keyboards': 40.0,  # kg CO2e/kg
    'mice': 40.0,  # kg CO2e/kg
    'cables': 25.0,  # kg CO2e/kg
    'chargers': 35.0,  # kg CO2e/kg
    'adapters': 30.0,  # kg CO2e/kg
    'cases': 15.0,  # kg CO2e/kg
    'accessories': 20.0,  # kg CO2e/kg
    'default': 50.0  # kg CO2e/kg (valore di default per categorie sconosciute)
}

# Mappatura delle categorie Amazon alle categorie standardizzate
CATEGORY_MAPPING = {
    'Computers & Accessories': 'laptops',
    'Laptop Computers': 'laptops',
    'Traditional Laptops': 'laptops',
    'Camera & Photo': 'cameras',
    'Digital Cameras': 'cameras',
    'Headphones': 'headphones',
    'Headphones, Earbuds & Accessories': 'headphones',
    'Earbud & In-Ear Headphones': 'headphones',
    'Over-Ear Headphones': 'headphones',
    'On-Ear Headphones': 'headphones',
    'Computer Accessories & Peripherals': 'accessories',
    'Keyboards, Mice & Accessories': 'accessories',
    'Keyboards': 'keyboards',
    'Computer Mice': 'mice',
    'Tablet Accessories': 'accessories',
    'Tablet Cases': 'cases',
    'Laptop Accessories': 'accessories',
    'Laptop Bags & Cases': 'cases',
    'Bags, Cases & Sleeves': 'cases',
    'Cases': 'cases',
    'Cables & Accessories': 'cables',
    'Cables': 'cables',
    'Adapters': 'adapters',
    'Chargers & Adapters': 'chargers',
    'Power Strips': 'accessories',
    'Televisions & Video': 'televisions',
    'Televisions': 'televisions',
    'Monitors': 'monitors',
    'Computer Monitors': 'monitors',
    'Printers': 'printers',
    'Hard Drives & Storage': 'hard drives',
    'External Hard Drives': 'hard drives',
    'Internal Hard Drives': 'hard drives',
    'Solid State Drives': 'ssds',
    'Networking Products': 'routers',
    'Routers': 'routers',
    'Smartphones': 'smartphones',
    'Cell Phones': 'smartphones',
    'Tablets': 'tablets',
    'Desktop Computers': 'desktop computers',
    'Speakers': 'speakers',
    'Computer Speakers': 'speakers',
    'Bluetooth Speakers': 'speakers',
    'Portable Bluetooth Speakers': 'speakers'
}

def extract_weight(weight_str):
    """Extract weight in kg from weight string."""
    if not weight_str:
        return None
    
    # Convert to lowercase for consistency
    weight_str = weight_str.lower()
    
    # Extract numeric value and unit
    match = re.search(r'([\d.]+)\s*(ounces|pounds|kg|grams|g|oz|lbs)', weight_str)
    if not match:
        return None
    
    value, unit = match.groups()
    value = float(value)
    
    # Convert to kg
    if 'ounces' in unit or 'oz' in unit:
        return value * 0.0283495  # 1 oz = 0.0283495 kg
    elif 'pounds' in unit or 'lbs' in unit:
        return value * 0.453592  # 1 lb = 0.453592 kg
    elif 'grams' in unit or 'g' in unit:
        return value / 1000  # 1 g = 0.001 kg
    elif 'kg' in unit:
        return value
    
    return None

def get_product_category(categories):
    """Determine the most specific product category from the list of categories."""
    if not categories:
        return 'default'
    
    # Try to find a match in our category mapping
    for category in categories:
        if category in CATEGORY_MAPPING:
            return CATEGORY_MAPPING[category]
    
    # Check for partial matches
    for category in categories:
        for key, value in CATEGORY_MAPPING.items():
            if key.lower() in category.lower() or category.lower() in key.lower():
                return value
    
    # Default to 'accessories' for Electronics category
    if 'Electronics' in categories:
        return 'accessories'
    
    return 'default'

def get_material_emission_factor(material):
    """Get emission factor for a specific material."""
    if not material:
        return MATERIAL_EMISSION_FACTORS['default']
    
    material_lower = material.lower()
    
    # Direct match
    for key, value in MATERIAL_EMISSION_FACTORS.items():
        if key == material_lower:
            return value
    
    # Partial match
    for key, value in MATERIAL_EMISSION_FACTORS.items():
        if key in material_lower or material_lower in key:
            return value
    
    return MATERIAL_EMISSION_FACTORS['default']

def estimate_co2_emissions(product):
    """Estimate CO2e emissions for a product based on its weight, category, and material."""
    # Get product weight
    weight_kg = product.get('weight_kg')
    
    # If weight is missing, estimate based on category
    if not weight_kg:
        # Use average weight for the category or default
        weight_kg = 1.1688  # Average weight from analysis
    
    # Get product category
    category = get_product_category(product.get('categories', []))
    category_factor = CATEGORY_EMISSION_FACTORS.get(category, CATEGORY_EMISSION_FACTORS['default'])
    
    # Get material emission factor
    material = product.get('material')
    material_factor = get_material_emission_factor(material)
    
    # Calculate emissions
    # We use a weighted approach: 80% based on category (which includes manufacturing processes)
    # and 20% based on material composition
    emissions_per_kg = 0.8 * category_factor + 0.2 * material_factor
    
    # Total emissions for the product
    total_emissions = emissions_per_kg * weight_kg
    
    return {
        'emissions_per_kg': round(emissions_per_kg, 2),
        'total_emissions': round(total_emissions, 2),
        'weight_kg': round(weight_kg, 4),
        'category': category,
        'material': material if material else 'unknown'
    }

def generate_explanation(product, emissions_data):
    """Generate an explanation for the CO2e emissions estimate."""
    explanation = f"Stima basata su "
    
    if product.get('weight_kg'):
        explanation += f"peso effettivo di {emissions_data['weight_kg']} kg"
    else:
        explanation += f"peso stimato di {emissions_data['weight_kg']} kg (media della categoria)"
    
    explanation += f", categoria '{emissions_data['category']}'"
    
    if emissions_data['material'] != 'unknown':
        explanation += f" e materiale '{emissions_data['material']}'"
    
    explanation += f". Fattore di emissione: {emissions_data['emissions_per_kg']} kg CO2e/kg."
    
    return explanation

def process_electronics_data(input_file, output_file):
    """Process electronics data from JSONL file and calculate CO2e emissions."""
    results = []
    
    with open(input_file, 'r') as f:
        for line in f:
            try:
                data = json.loads(line)
                
                # Extract product info
                product_info = {
                    'asin': data.get('asin', ''),
                    'title': data.get('title', 'Unknown Product'),
                    'categories': data.get('categories', []),
                    'material': data.get('details', {}).get('Material'),
                    'weight_kg': extract_weight(data.get('details', {}).get('Item Weight'))
                }
                
                # Estimate CO2 emissions
                emissions_data = estimate_co2_emissions(product_info)
                
                # Generate explanation
                explanation = generate_explanation(product_info, emissions_data)
                
                # Create result entry
                result = {
                    'product_name': product_info['title'],
                    'co2e_per_kg': emissions_data['emissions_per_kg'],
                    'explanation': explanation
                }
                
                results.append(result)
                
            except json.JSONDecodeError:
                print(f"Error decoding JSON")
            except Exception as e:
                print(f"Error processing product: {str(e)}")
    
    # Save results to JSON file
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"Processed {len(results)} products. Results saved to {output_file}")
    
    # Generate some statistics
    emissions_per_kg = [r['co2e_per_kg'] for r in results]
    print(f"Average CO2e per kg: {sum(emissions_per_kg) / len(emissions_per_kg):.2f} kg CO2e/kg")
    print(f"Min CO2e per kg: {min(emissions_per_kg):.2f} kg CO2e/kg")
    print(f"Max CO2e per kg: {max(emissions_per_kg):.2f} kg CO2e/kg")
    
    return results

if __name__ == "__main__":
    input_file = '../dataset/elctronics.jsonl'
    output_file = '../dataset/electronics_co2_emissions.json'
    process_electronics_data(input_file, output_file)
