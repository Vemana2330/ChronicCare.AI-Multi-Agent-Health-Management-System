import requests
import pandas as pd
import os
import boto3
from io import BytesIO, StringIO
from dotenv import load_dotenv
import mimetypes
import time

# === Load .env credentials ===
load_dotenv()
APP_ID = os.getenv("APP_ID")
APP_KEY = os.getenv("APP_KEY")
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.getenv("AWS_REGION")
BUCKET_NAME = os.getenv("AWS_BUCKET_NAME")

# === Setup S3 client ===
s3 = boto3.client(
    "s3",
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_REGION
)

# === Cuisines to loop through ===
CUISINES = [
    "indian", "mediterranean", "mexican", "italian", "american", "chinese", "french",
    "thai", "japanese", "greek", "spanish", "korean", "vietnamese", "lebanese",
    "turkish", "moroccan", "german", "british", "cuban", "brazilian", "ethiopian"
]

def extract_recipes_main():
    seen_recipes_file = "/opt/airflow/recipe/uploaded_recipes.txt"
    print(f"📄 Checking for previously uploaded recipes at {seen_recipes_file}")
    if os.path.exists(seen_recipes_file):
        with open(seen_recipes_file, "r") as f:
            seen_recipes = set(line.strip() for line in f)
        print(f"🧠 Loaded {len(seen_recipes)} previously seen recipes")
    else:
        seen_recipes = set()
        print("🆕 No previously seen recipes found")

    for cuisine in CUISINES:
        print(f"\n🌍 Starting cuisine: {cuisine}")
        collected = 0
        MAX_RECIPES = 560
        batch_size = 80
        url = "https://api.edamam.com/api/recipes/v2"
        params = {
            "type": "public",
            "q": cuisine,
            "app_id": APP_ID,
            "app_key": APP_KEY,
            "to": batch_size
        }

        current_url = url
        current_params = params
        batch_uploaded = 0

        while collected < MAX_RECIPES and current_url:
            response = requests.get(current_url, params=current_params if collected == 0 else None)

            if response.status_code != 200:
                print("❌ Error fetching:", response.status_code, response.text)
                break

            data = response.json()
            hits = data.get("hits", [])
            next_link = data.get("_links", {}).get("next", {}).get("href", None)

            if not hits:
                print("No more recipes found.")
                break

            for hit in hits:
                if collected >= MAX_RECIPES:
                    break

                recipe = hit["recipe"]
                name_cleaned = recipe["label"].strip().lower().replace(" ", "_").replace("/", "_")

                if name_cleaned in seen_recipes:
                    continue

                seen_recipes.add(name_cleaned)

                servings = recipe.get("yield", 1)
                calories_total = recipe.get("calories", 0)
                calories_per_serving = calories_total / servings
                daily_value_percent = round((calories_per_serving / 2000) * 100, 1)

                print("=" * 50)
                print(f"🍽️ Recipe #{collected + 1}: {recipe['label']}")
                print("🔗", recipe["url"])

                # === Download image ===
                image_url = recipe["image"]
                try:
                    image_response = requests.get(image_url)
                    image_ext = mimetypes.guess_extension(image_response.headers.get("Content-Type", "image/jpeg"))
                    image_key = f"Recipe_EDA/{name_cleaned}/Images/image{image_ext or '.jpg'}"
                    s3.upload_fileobj(BytesIO(image_response.content), BUCKET_NAME, image_key)
                    print("🖼️ Image uploaded")
                except Exception as e:
                    print("⚠️ Image upload failed:", e)
                    image_key = None

                # === Nutrition Data ===
                nutrients = recipe.get("totalNutrients", {})
                nutrition_list = []

                for key, value in nutrients.items():
                    if key == "ENERC_KCAL":
                        continue
                    per_serving = value["quantity"] / servings
                    nutrition_list.append({
                        "Nutrient": value["label"],
                        "Amount per Serving": round(per_serving, 2),
                        "Unit": value["unit"]
                    })

                # === Append metadata ===
                nutrition_list.append({"Nutrient": "Servings", "Amount per Serving": servings, "Unit": "-"})
                nutrition_list.append({"Nutrient": "Calories per Serving", "Amount per Serving": round(calories_per_serving), "Unit": "kcal"})
                nutrition_list.append({"Nutrient": "Daily Value %", "Amount per Serving": daily_value_percent, "Unit": "%"})

                def add_meta_row(field_name, items):
                    if items:
                        nutrition_list.append({
                            "Nutrient": field_name,
                            "Amount per Serving": "; ".join(items),
                            "Unit": "-"
                        })

                add_meta_row("Health Labels", recipe.get("healthLabels", []))
                add_meta_row("Diet Labels", recipe.get("dietLabels", []))
                add_meta_row("Cautionary Tags", recipe.get("cautions", []))
                add_meta_row("Cuisine Type", recipe.get("cuisineType", []))
                add_meta_row("Meal Type", recipe.get("mealType", []))
                add_meta_row("Dish Type", recipe.get("dishType", []))
                add_meta_row("Ingredients", recipe.get("ingredientLines", []))

                nutrition_list.append({"Nutrient": "Link", "Amount per Serving": recipe.get("url", ""), "Unit": "-"})
                nutrition_list.append({"Nutrient": "Image URL", "Amount per Serving": recipe.get("image", ""), "Unit": "-"})

                # === Save CSV to S3 ===
                df = pd.DataFrame(nutrition_list)
                csv_buffer = StringIO()
                df.to_csv(csv_buffer, index=False)
                csv_key = f"Recipe_EDA/{name_cleaned}/{name_cleaned}.csv"
                s3.put_object(Body=csv_buffer.getvalue(), Bucket=BUCKET_NAME, Key=csv_key)
                print("📄 CSV uploaded")

                print(f"✅ Uploaded: {recipe['label']}")
                print(f"   - CSV: s3://{BUCKET_NAME}/{csv_key}")
                if image_key:
                    print(f"   - IMG: s3://{BUCKET_NAME}/{image_key}")
                print()

                with open(seen_recipes_file, "a") as f:
                    f.write(name_cleaned + "\n")

                collected += 1
                batch_uploaded += 1

                # Sleep after each batch of 80 (except at end)
                if batch_uploaded == batch_size and collected < MAX_RECIPES:
                    print(f"⏳ Uploaded batch of {batch_size} recipes. Sleeping 60 seconds before next batch...")
                    batch_uploaded = 0
                    time.sleep(60)

            current_url = next_link
            current_params = None

        print(f"✅ Done with cuisine: {cuisine} — Total collected: {collected}")
        print("⏳ Sleeping 60 seconds before next cuisine...\n")
        time.sleep(60)

    print(f"\n✅ All cuisines complete. Seen recipes file updated with {len(seen_recipes)} entries.")

