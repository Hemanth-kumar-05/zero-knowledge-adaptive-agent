import json
from pathlib import Path

def create_co_po_matrix(results_file):
    """Create a CO-PO mapping matrix from results JSON"""
    
    with open(results_file, 'r') as f:
        data = json.load(f)
    
    print(f"\n{'='*100}")
    print(f"CO-PO/PSO Attainment Matrix: {data['course_info']['course_name']}")
    print(f"Course Code: {data['course_info']['course_code']}")
    print(f"{'='*100}\n")
    
    # Collect all POs and PSOs
    pos = set()
    psos = set()
    cos = []
    
    for co_mapping in data['mappings']:
        cos.append(co_mapping['co_id'])
        for po_map in co_mapping['po_mappings']:
            pos.add(po_map['po_id'])
        for pso_map in co_mapping['pso_mappings']:
            psos.add(pso_map['pso_id'])
    
    pos = sorted(pos, key=lambda x: int(x[2:]))  # Sort PO1, PO2, ...
    psos = sorted(psos, key=lambda x: int(x[3:]))  # Sort PSO1, PSO2, ...
    all_outcomes = pos + psos
    
    # Build matrix with levels
    matrix = {}
    
    for co_mapping in data['mappings']:
        co_id = co_mapping['co_id']
        matrix[co_id] = {}
        
        # Store PO levels
        for po_map in co_mapping['po_mappings']:
            po_id = po_map['po_id']
            matrix[co_id][po_id] = po_map['level']
        
        # Store PSO levels
        for pso_map in co_mapping['pso_mappings']:
            pso_id = pso_map['pso_id']
            matrix[co_id][pso_id] = pso_map['level']
    
    
    # Print header
    header = "CO/PO-PSO |"
    for outcome in all_outcomes:
        header += f" {outcome:^7} |"
    print(header)
    print("-" * len(header))
    
    # Print rows
    for co_id in cos:
        row = f"   {co_id:^6} |"
        for outcome in all_outcomes:
            level = matrix[co_id].get(outcome, 0)
            row += f" {level:^7} |"
        print(row)
    
    print("\n" + "="*100)
    print("\nAttainment Scale:")
    print("  0 = No correlation")
    print("  1 = Low correlation")
    print("  2 = Medium correlation")
    print("  3 = High correlation")
    print("\n" + "="*100)
    
    # Summary statistics
    print("\n📊 Summary Statistics:\n")
    for co_id in cos:
        levels = list(matrix[co_id].values())
        avg = sum(levels) / len(levels) if levels else 0
        high_count = sum(1 for l in levels if l == 3)
        medium_count = sum(1 for l in levels if l == 2)
        low_count = sum(1 for l in levels if l == 1)
        none_count = sum(1 for l in levels if l == 0)
        
        print(f"  {co_id}: Avg={avg:.2f} | High={high_count} | Medium={medium_count} | Low={low_count} | None={none_count}")
    
    print("\n" + "="*100 + "\n")

if __name__ == "__main__":
    results_file = Path(__file__).parent / "mapping_results.json"
    create_co_po_matrix(results_file)
