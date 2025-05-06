{{ config(
    materialized='incremental',
    unique_key='recipe_name'
) }}

with raw as (
    select 
        recipe_name,
        lower(attribute) as attribute,
        value
    from {{ source('raw', 'RAW_RECIPES') }}

    {% if is_incremental() %}
    where recipe_name not in (select recipe_name from {{ this }})
    {% endif %}
),

pivoted as (
    select
        recipe_name,

        -- Text
        coalesce(max(case when attribute = 'cuisine type' then value end), 'N/A') as cuisine_type,
        coalesce(max(case when attribute = 'meal type' then value end), 'N/A') as meal_type,
        coalesce(max(case when attribute = 'dish type' then value end), 'N/A') as dish_type,
        coalesce(max(case when attribute = 'link' then value end), 'N/A') as link,
        coalesce(max(case when attribute = 'image url' then value end), 'N/A') as image_url,
        coalesce(max(case when attribute = 'ingredients' then value end), 'N/A') as ingredients,
        coalesce(max(case when attribute = 'health labels' then value end), 'N/A') as health_labels,
        coalesce(max(case when attribute = 'diet labels' then value end), 'N/A') as diet_labels,
        coalesce(max(case when attribute = 'cautionary tags' then value end), 'N/A') as caution_labels,

        -- Core fields
        max(case when attribute = 'calories per serving' then value end)::float as calories_per_serving_kcal,
        max(case when attribute = 'fat' then value end)::float as fat_g,
        max(case when attribute = 'saturated' then value end)::float as saturated_g,
        max(case when attribute = 'trans' then value end)::float as trans_g,
        max(case when attribute = 'monounsaturated' then value end)::float as monounsaturated_g,
        max(case when attribute = 'polyunsaturated' then value end)::float as polyunsaturated_g,
        max(case when attribute = 'carbs' then value end)::float as carbs_g,
        max(case when attribute = 'carbohydrates (net)' then value end)::float as net_carbs_g,
        max(case when attribute = 'fiber' then value end)::float as fiber_g,
        max(case when attribute = 'sugars' then value end)::float as sugars_g,
        max(case when attribute = 'protein' then value end)::float as protein_g,
        max(case when attribute = 'cholesterol' then value end)::float as cholesterol_mg,
        max(case when attribute = 'sodium' then value end)::float as sodium_mg,

        -- Minerals
        max(case when attribute = 'calcium' then value end)::float as calcium_mg,
        max(case when attribute = 'magnesium' then value end)::float as magnesium_mg,
        max(case when attribute = 'potassium' then value end)::float as potassium_mg,
        max(case when attribute = 'iron' then value end)::float as iron_mg,
        max(case when attribute = 'zinc' then value end)::float as zinc_mg,
        max(case when attribute = 'phosphorus' then value end)::float as phosphorus_mg,

        -- Vitamins
        max(case when attribute = 'vitamin a' then value end)::float as vitamin_a_mcg,
        max(case when attribute = 'vitamin c' then value end)::float as vitamin_c_mg,
        max(case when attribute = 'thiamin (b1)' then value end)::float as thiamin_b1_mg,
        max(case when attribute = 'riboflavin (b2)' then value end)::float as riboflavin_b2_mg,
        max(case when attribute = 'niacin (b3)' then value end)::float as niacin_b3_mg,
        max(case when attribute = 'vitamin b6' then value end)::float as vitamin_b6_mg,
        max(case when attribute = 'vitamin b12' then value end)::float as vitamin_b12_mcg,
        max(case when attribute = 'vitamin d' then value end)::float as vitamin_d_mcg,
        max(case when attribute = 'vitamin e' then value end)::float as vitamin_e_mg,
        max(case when attribute = 'vitamin k' then value end)::float as vitamin_k_mcg,

        -- Folate
        max(case when attribute = 'folate equivalent (total)' then value end)::float as folate_equivalent_total_mcg,
        max(case when attribute = 'folate (food)' then value end)::float as folate_food_mcg,
        max(case when attribute = 'folic acid' then value end)::float as folic_acid_mcg,

        -- Other
        max(case when attribute = 'water' then value end)::float as water_g,
        max(case when attribute = 'daily value %' then value end)::float as daily_value_pct,
        max(case when attribute = 'servings' then value end)::float as servings

    from raw
    group by recipe_name
)

select * from pivoted