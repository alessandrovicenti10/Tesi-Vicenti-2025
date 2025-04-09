
import json
import re

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

def analyze_jsonl(file_path):
    """Analyze the JSONL file to extract relevant information."""
    products = []
    categories = {}
    materials = {}
    weights = []
    has_weight = 0
    total_products = 0
    
    with open(file_path, 'r') as f:
        for line in f:
            total_products += 1
            try:
                data = json.loads(line)
                
                # Extract product name
                product_name = data.get('title', 'Unknown Product')
                
                # Extract categories
                for cat in data.get('categories', []):
                    categories[cat] = categories.get(cat, 0) + 1
                
                # Extract material
                material = None
                if 'details' in data and 'Material' in data['details']:
                    material = data['details']['Material']
                    materials[material] = materials.get(material, 0) + 1
                
                # Extract weight
                weight_kg = None
                if 'details' in data and 'Item Weight' in data['details']:
                    weight_str = data['details']['Item Weight']
                    weight_kg = extract_weight(weight_str)
                    if weight_kg:
                        has_weight += 1
                        weights.append(weight_kg)
                
                # Store product info
                product_info = {
                    'asin': data.get('asin', ''),
                    'title': product_name,
                    'categories': data.get('categories', []),
                    'material': material,
                    'weight_kg': weight_kg,
                    'details': data.get('details', {})
                }
                products.append(product_info)
                
            except json.JSONDecodeError:
                print(f"Error decoding JSON on line {total_products}")
    
    # Calculate statistics
    avg_weight = sum(weights) / len(weights) if weights else 0
    
    # Print summary
    print(f'Total products: {total_products}')
    print(f'Products with weight info: {has_weight} ({has_weight/total_products*100:.2f}%)')
    print(f'Average weight: {avg_weight:.4f} kg')
    
    print('\nTop 10 categories:')
    for cat, count in sorted(categories.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f'- {cat}: {count}')
    
    print('\nTop 10 materials:')
    for mat, count in sorted(materials.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f'- {mat}: {count}')
    
    return products, categories, materials, weights, has_weight, total_products

if __name__ == "__main__":
    file_path = '../dataset/meta_Electronics_SMALL.jsonl'
    analyze_jsonl(file_path)
