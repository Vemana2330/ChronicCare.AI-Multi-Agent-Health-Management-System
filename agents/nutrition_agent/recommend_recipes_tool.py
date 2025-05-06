# FILE: agents/nutrition_agent/recommend_recipes_tool.py
 
from langchain.tools import tool
from agents.nutrition_agent.snowflake_connector import run_query
from agents.nutrition_agent.nutrition_constraints import NUTRITION_THRESHOLDS
from typing import List
import random
import os
from dotenv import load_dotenv
 
load_dotenv()
 
SNOWFLAKE_DATABASE = os.getenv("SNOWFLAKE_DATABASE", "RECIPE_DB")
SNOWFLAKE_SCHEMA = os.getenv("SNOWFLAKE_SCHEMA_DBT", "RAW_DATA_SCHEMA")
TABLE_NAME = "STG_RECIPES"
FULL_TABLE_NAME = f'{SNOWFLAKE_DATABASE}.{SNOWFLAKE_SCHEMA}.{TABLE_NAME}'
 
@tool
def recommend_recipes_tool(username: str, chronic_condition: str, cuisine_types: List[str], meal_types: List[str]) -> str:
    """
    🍲 Recommend personalized recipes for a user based on:
        - Chronic condition (e.g. CKD, Type2, Obesity, etc)
        - Selected cuisine types (e.g. Indian, Chinese)
        - Selected meal types (e.g. Breakfast, Lunch)
 
    Filters are applied using the chronic condition thresholds from `nutrition_constraints.py`
    Returns 5 recipes for each meal+cuisine combination
    Filters out recipes violating key nutrient thresholds (e.g., high sugar for diabetes)
    Calories per serving are constrained based on meal type:
       - Breakfast: 200–300 kcal
       - Lunch: 350–700 kcal
       - Dinner: 300–600 kcal
       - Snack: 50–300 kcal
    """
 
    print(f"🔍 [recommend_recipes_tool] Username: {username}")
    print(f"🔍 Chronic condition: {chronic_condition}")
    print(f"🔍 Cuisine types: {cuisine_types}")
    print(f"🔍 Meal types: {meal_types}")
 
    if not cuisine_types or not meal_types:
        return "⚠️ Please select at least one cuisine type and one meal type."
 
    condition_key = chronic_condition.lower().strip()
    thresholds = NUTRITION_THRESHOLDS.get(condition_key, {})
    print(f"📉 Nutrient thresholds applied: {thresholds}")
 
    # 🧮 Per-meal calorie constraints
    meal_calorie_ranges = {
        "breakfast": (200, 300),
        "lunch": (350, 700),
        "dinner": (300, 600),
        "snack": (50, 300)
    }
 
    all_results = []
 
    for cuisine in cuisine_types:
        for meal in meal_types:
            print(f"\n🍴 Processing {meal} ({cuisine})")
            where_clauses = [f"CUISINE_TYPE ILIKE '%{cuisine}%'", f"MEAL_TYPE ILIKE '%{meal}%'"]
 
            for col, val in thresholds.items():
                if isinstance(val, bool):
                    if col == "Gluten_free":
                        where_clauses.append("LOWER(\"Cautionary_Tags\") NOT ILIKE '%gluten%'")
                        print(f"🚫 Filtering out gluten-containing recipes")
                else:
                    where_clauses.append(f"{col.upper()} <= {val}")
                    print(f"✅ Applying constraint: {col} <= {val}")
 
            # ✅ Dynamic calorie filtering
            meal_lower = meal.lower()
            if meal_lower in meal_calorie_ranges:
                min_kcal, max_kcal = meal_calorie_ranges[meal_lower]
                where_clauses.append(f"CALORIES_PER_SERVING_KCAL BETWEEN {min_kcal} AND {max_kcal}")
                print(f"📊 Applied calorie range: {min_kcal}–{max_kcal} kcal for {meal}")
            else:
                print(f"⚠️ No calorie range defined for meal type: {meal}")
 
            where_sql = " AND ".join(where_clauses)
 
            # Include condition-specific nutrient fields in SELECT
            nutrient_cols = set(["CALORIES_PER_SERVING_KCAL"])
            nutrient_cols.update([col.upper() for col in thresholds if isinstance(thresholds[col], (int, float))])
            nutrient_col_str = ", ".join(nutrient_cols)
 
            query = f"""
                SELECT RECIPE_NAME, IMAGE_URL, INGREDIENTS, LINK, HEALTH_LABELS, DIET_LABELS, CAUTION_LABELS, {nutrient_col_str}
                FROM {FULL_TABLE_NAME}
                WHERE {where_sql}
                LIMIT 15;
            """
            print(f"📥 Running SQL Query:\n{query}")
 
            rows = run_query(query)
            print(f"📦 Fetched {len(rows)} recipes")
            # Step 1: Remove previously seen recipes in this session
 
            if not rows:
                all_results.append(f"❌ No suitable recipes found for {meal} ({cuisine}).")
                continue
 
            selected = random.sample(rows, min(5, len(rows)))
            print(f"✅ Selected {len(selected)} recipes to return")
 
            for r in selected:
                print(f"🔗 Final image URL for {r['recipe_name']}: {r['image_url']}")
 
            formatted = "\n".join([
                f"""🍽️ **{r['recipe_name']}**  
🔗 [View Recipe]({r['link']})  
📸 ImageURL: {r['image_url'].split("?")[0]}  
📝 Ingredients: {r['ingredients']}  
💡 Health Labels: {r['health_labels']}  
⚠️ Caution Tags: {r['caution_labels']}  
🔥 Calories/Serving: {r['calories_per_serving_kcal']} kcal""" +
                "".join([
                    f"\n🧬 {col.replace('_', ' ').title()}: {r.get(col.lower(), 'N/A')}"
                    for col in nutrient_cols if col != "CALORIES_PER_SERVING_KCAL"
                ]) + "\n"
                for r in selected
            ])
 
            all_results.append(f"### 🥗 {meal} ({cuisine})\n\n{formatted}")
 
    return "\n\n".join(all_results)