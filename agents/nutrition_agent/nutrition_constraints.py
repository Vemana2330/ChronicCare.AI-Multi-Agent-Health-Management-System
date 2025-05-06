# FILE: agents/nutrition_agent/nutrition_constraints.py

NUTRITION_THRESHOLDS = {
    "cholesterol": {
        "Cholesterol_mg": 60,        # Aim to keep dietary cholesterol low per meal
        "Saturated_g": 6,        # Limit saturated fat intake per meal
        "Trans_g": 1,            # Minimize trans fat intake per meal
        "Fiber_g": 3         # Encourage soluble fiber intake per meal
    },
    "type2": {
        "Sugars_g": 8,         # Limit added sugars per meal
        "Carbohydrates_g": 35,       # Control carbohydrate intake per meal
        "Fiber_g": 5                 # Ensure adequate fiber intake per meal
    },
    "hypertension": {
        "Sodium_mg": 500,            # Limit sodium intake per meal
        "Potassium_mg": 700          # Encourage potassium intake per meal
    },
    "obesity": {
        "Calories_per_serving_kcal": 500,        # Control calorie intake per meal
        "Fat_g": 17,                 # Limit fat intake per meal
        "Sugars_g": 10         # Limit added sugars per meal
    },
    "ckd": {
        "Protein_g": 15,             # Limit protein intake per meal
        "Sodium_mg": 500,            # Limit sodium intake per meal
        "Phosphorus_mg": 300,        # Limit phosphorus intake per meal
        "Potassium_mg": 400          # Limit potassium intake per meal
    },
    "gluten": {
        "Gluten_free": True          # Ensure meals are gluten-free
    },
    "polycystic": {
        "Sugars_g": 10,        # Limit added sugars per meal
        "Carbohydrates_g": 30,       # Control carbohydrate intake per meal
        "Fiber_g": 5              # Ensure adequate fiber intake per meal
                    
    }
}
