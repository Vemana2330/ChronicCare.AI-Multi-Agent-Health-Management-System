import streamlit as st
import requests
from uuid import uuid4
import os
import psycopg2
from dotenv import load_dotenv
 
# Load from .env in frontend/
load_dotenv(dotenv_path=os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".env")))
 
def get_pg_connection():
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST"),
        port=os.getenv("POSTGRES_PORT"),
        dbname=os.getenv("POSTGRES_DB"),
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD")
    )
 
 
def fetch_tdee(username: str) -> int:
    try:
        conn = get_pg_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT tdee FROM users WHERE username = %s", (username,))
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        if result and result[0]:
            return int(result[0])
        else:
            return 2100  # fallback default
    except Exception as e:
        print(f"Error fetching TDEE: {e}")
        return 2100  # fallback on error
 
# === Nutrient Emoji Map ===
NUTRIENT_EMOJIS = {
    "Protein": "💪", "Sodium": "🧂", "Phosphorus": "🧪", "Potassium": "🍌",
    "Carbohydrates": "🍞", "Fiber": "🌾", "Fat": "🥑", "Sugars": "🍭",
    "Cholesterol": "❤️", "Calories": "🔥", "Added Sugars": "🚫🍬",
    "Saturated Fat": "🥩", "Soluble Fiber": "🧃", "Omega 3": "🐟"
}
 
def show_nutrition_agent(API_URL):
    st.header("🍽️ Personalized Nutrition Planner")
 
    st.session_state.setdefault("selected_recipes", [])
    if "tdee" not in st.session_state and "username" in st.session_state:
        st.session_state.tdee = fetch_tdee(st.session_state.username)
        st.session_state.setdefault("remaining_kcal", st.session_state.get("tdee", 2100))
    st.session_state.setdefault("selected_cuisines", [])
    st.session_state.setdefault("selected_meals", [])
    st.session_state.setdefault("last_result", "")
 
    st.info(f"🧮 You have **{st.session_state.remaining_kcal} kcal** left for today.")
    if st.session_state.selected_recipes:
        st.success("📋 **Your Meal Plan**")
        for r in st.session_state.selected_recipes:
            st.markdown(f"• 🍽️ `{r}`")
 
    st.markdown("### 🍛 Select Your Preferred Cuisines")
    cuisine_options = [
        "Indian", "Chinese", "Mexican", "Italian", "Thai",
        "American", "French", "Japanese", "Greek", "Mediterranean"
    ]
    selected_cuisines = st.multiselect(
        "Select one or more cuisines:", cuisine_options,
        default=st.session_state.selected_cuisines
    )
    st.session_state.selected_cuisines = selected_cuisines
 
    st.markdown("### 🕒 Choose Your Meals")
    meal_options = ["Breakfast", "Lunch", "Dinner", "Snack"]
    selected_meals = st.multiselect(
        "Select meal types:", meal_options,
        default=st.session_state.selected_meals
    )
    st.session_state.selected_meals = selected_meals
 
    if st.button("🔍 Get Recipe Recommendations"):
        
        if not selected_cuisines or not selected_meals:
            st.warning("⚠️ Please select at least one cuisine and one meal type.")
            return
        if "username" not in st.session_state or not st.session_state.username:
            st.error("🚫 Please log in to view personalized recommendations.")
            return
 
        payload = {
            "username": st.session_state.username,
            "cuisine_types": selected_cuisines,
            "meal_types": selected_meals
        }
 
        with st.spinner("🍳 Fetching personalized meals..."):
            try:
                response = requests.post(f"{API_URL}/nutrition", json=payload)
                if response.status_code == 200:
                    result = response.json().get("response", "")
                    if result:
                        st.session_state.last_result = result
                        st.markdown("### 📝 Suggested Recipes")
                        render_nutrition_output(result)
                    else:
                        st.info("🤷 No recipes matched your criteria.")
                else:
                    st.error(f"❌ Server error: {response.status_code}")
            except Exception as e:
                st.error(f"❌ Request failed: {str(e)}")
    elif st.session_state.last_result:
        st.markdown("### 📝 Suggested Recipes (Last Search)")
        render_nutrition_output(st.session_state.last_result)
 
 
def highlight_nutrient_line(line, condition):
    keywords = {
        "ckd": ["Protein", "Sodium", "Phosphorus", "Potassium"],
        "cholesterol": ["Cholesterol", "Saturated Fat", "Soluble Fiber"],
        "type2": ["Added Sugars", "Carbohydrates", "Fiber"],
        "obesity": ["Calories", "Fat", "Added Sugars"],
        "hypertension": ["Sodium", "Potassium"],
        "polycystic": ["Added Sugars", "Carbohydrates", "Fiber", "Omega 3"]
    }
    nutrient_fields = keywords.get(condition.lower(), [])
    for nutrient in nutrient_fields:
        if nutrient.lower() in line.lower():
            emoji = NUTRIENT_EMOJIS.get(nutrient, "🧬")
            return f"**{emoji} {line}**"
    return line
 
 
def render_nutrition_output(result: str):
    recipes = result.strip().split("\n\n🍽️")
    grouped = {"Breakfast": [], "Lunch": [], "Dinner": [], "Snack": []}
    condition = st.session_state.get("chronic_condition", "").lower()
 
    for idx, block in enumerate(recipes):
        block = "🍽️" + block if not block.startswith("🍽️") else block
        if idx < 6:
            grouped["Breakfast"].append(block)
        elif idx < 11:
            grouped["Lunch"].append(block)
        elif idx < 16:
            grouped["Dinner"].append(block)
        else:
            grouped["Snack"].append(block)
 
    used_keys = set()
 
    for meal_type, blocks in grouped.items():
        if not blocks:
            continue
        st.markdown(f"## 🍴 {meal_type} Recipes")
 
        for i, block in enumerate(blocks):
            lines = block.strip().split("\n")
            recipe_name = None
            display_lines = []
            kcal_value = None
 
            for line in lines:
                line = line.strip()
                if line.startswith("🍽️"):
                    if "**" in line:
                        try:
                            recipe_name = line.split("**")[1].strip()
                        except:
                            pass
                    if not recipe_name:
                        recipe_name = line.replace("🍽️", "").strip()
                elif "Calories/Serving" in line:
                    try:
                        kcal_value = float(line.split(":")[-1].replace("kcal", "").strip())
                    except:
                        kcal_value = None
                elif line.startswith("📸"):
                    continue
                else:
                    display_lines.append(line)
 
            if not recipe_name or recipe_name.lower().startswith("###"):
                continue
 
            with st.expander(f"🍽️ {recipe_name}"):
                if kcal_value:
                    st.markdown(f"🔥 **Calories/Serving:** {kcal_value} kcal")
                for display_line in display_lines:
                    
                    st.markdown(highlight_nutrient_line(display_line, condition), unsafe_allow_html=True)
 
                raw_key = f"add_{recipe_name}_{i}".replace(" ", "_").replace("(", "").replace(")", "")
                unique_key = raw_key
                while unique_key in used_keys:
                    unique_key = f"{raw_key}_{uuid4().hex[:5]}"
                used_keys.add(unique_key)
 
                if recipe_name not in st.session_state.selected_recipes:
                    if st.button(f"➕ Add to Meal Plan", key=unique_key):
                        st.session_state.selected_recipes.append(recipe_name)
                        if kcal_value:
                            st.session_state.remaining_kcal -= kcal_value
                        # === Log into user_nutrition_logs ===
                        try:
                            conn = get_pg_connection()
                            cursor = conn.cursor()
                            cursor.execute("""
                                           INSERT INTO user_nutrition_logs (
                                           username, date, meal_type, recipe_name, calories_per_serving_kcal
                                           ) VALUES (%s, CURRENT_DATE, %s, %s, %s)
                                           """,(
                                               st.session_state.username,
                                               meal_type,
                                               recipe_name,
                                               kcal_value if kcal_value else 0
                                               ))
                            conn.commit()
                            cursor.close()
                            conn.close()
 
                        except Exception as e:
                            print(f"Error inserting into user_nutrition_logs: {e}")
                        st.success(f"✅ '{recipe_name}' added. {kcal_value} kcal deducted.")
                        st.rerun()
                else:
                    st.info("✅ Already added to your plan.")