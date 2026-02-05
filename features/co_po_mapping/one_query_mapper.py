#!/usr/bin/env python3
"""
ONE-QUERY CO-PO Mapper - Cost-Efficient Edition 💰
"""

import json
import os
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

from google import genai
from dotenv import load_dotenv

load_dotenv()

mapper = None
client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
model = "gemini-2.5-flash"

def load_data(json_file):
    with open(json_file, 'r') as f:
        return json.load(f)

def build_prompt(data):
    prompt = f"""You are an engineering curriculum assessor evaluating Course Outcome attainment levels against Programme Outcomes.

Course: {data['course_info']['course_name']}
Department: {data['course_info']['department']}

Course Outcomes:
"""
    for co in data['course_outcomes']:
        prompt += f"  {co['co_id']}: {co['description']}\n"
    
    prompt += "\nProgramme Outcomes:\n"
    for po in data['programme_outcomes']:
        prompt += f"\n{po['po_id']} - {po['title']}:\n"
        for comp in po['competencies']:
            prompt += f"  {comp['competency_id']}: {comp['description']}\n"
            for ind in comp['indicators']:
                prompt += f"    • {ind['indicator_id']}: {ind['description']}\n"
    
    prompt += "\nProgramme Specific Outcomes:\n"
    for pso in data['programme_specific_outcomes']:
        prompt += f"\n{pso['pso_id']} - {pso['description']}:\n"
        for comp in pso['competencies']:
            prompt += f"  {comp['competency_id']}: {comp['description']}\n"
            for ind in comp['indicators']:
                prompt += f"    • {ind['indicator_id']}: {ind['description']}\n"
    
    prompt += """

Task: Assess the attainment level between each CO and each PO/PSO.

Attainment Scale:
0 - No correlation (CO does not address this outcome)
1 - Low correlation (CO slightly addresses this outcome)
2 - Medium correlation (CO moderately addresses this outcome)
3 - High correlation (CO strongly addresses this outcome)

Return correlation matrix as JSON:
{
  "mappings": {
    "CO1": {
      "PO1": {"level": 2, "justification": "Applies basic science concepts"},
      "PO2": {"level": 3, "justification": "Directly involves problem analysis"},
      "PSO1": {"level": 1, "justification": "Limited tool application"}
    },
    "CO2": {...}
  }
}

Justifications: 5-10 words explaining the level."""
    
    return prompt

def map_all(data):
    """ONE API CALL"""
    print(f"\n{'='*80}")
    print(f"CO-PO Mapping: {data['course_info']['course_name']}")
    print(f"{'='*80}\n")
    print("🚀 ONE query only...")
    
    prompt = build_prompt(data)
    
    try:
        response = client.models.generate_content(
            model=model,
            contents=prompt,
            config={
                'temperature': 0.1,
                'response_mime_type': 'application/json'
            }
        )
        
        mapping_results = json.loads(response.text)
        results = format_results(data, mapping_results)
        
        print("✅ Done!\n")
        return results
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def format_results(data, mapping_results):
    results = {
        "course_info": data["course_info"],
        "mappings": []
    }
    
    for co in data["course_outcomes"]:
        co_id = co["co_id"]
        print(f"\n🎯 {co_id}: {co['description'][:60]}...")
        
        co_mapping = {
            "co_id": co_id,
            "co_description": co["description"],
            "po_mappings": [],
            "pso_mappings": []
        }
        
        co_results = mapping_results.get("mappings", {}).get(co_id, {})
        
        # POs
        for po in data["programme_outcomes"]:
            po_id = po["po_id"]
            po_result = co_results.get(po_id, {"level": 0, "justification": "Not applicable"})
            level = po_result.get("level", 0)
            justification = po_result.get("justification", "No correlation")
            
            co_mapping["po_mappings"].append({
                "po_id": po_id,
                "level": level,
                "justification": justification
            })
        
        # PSOs
        for pso in data["programme_specific_outcomes"]:
            pso_id = pso["pso_id"]
            pso_result = co_results.get(pso_id, {"level": 0, "justification": "Not applicable"})
            level = pso_result.get("level", 0)
            justification = pso_result.get("justification", "No correlation")
            
            co_mapping["pso_mappings"].append({
                "pso_id": pso_id,
                "level": level,
                "justification": justification
            })
        
        po_levels = [m["level"] for m in co_mapping["po_mappings"]]
        pso_levels = [m["level"] for m in co_mapping["pso_mappings"]]
        avg_po = sum(po_levels) / len(po_levels) if po_levels else 0
        avg_pso = sum(pso_levels) / len(pso_levels) if pso_levels else 0
        
        print(f"  ✅ Avg PO: {avg_po:.2f} | Avg PSO: {avg_pso:.2f}")
        results["mappings"].append(co_mapping)
    
    return results

# Run
input_file = Path(__file__).parent / "sample_data.json"
data = load_data(input_file)
results = map_all(data)

if results:
    output_file = Path(__file__).parent / "mapping_results.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\n✅ Saved: {output_file}")
