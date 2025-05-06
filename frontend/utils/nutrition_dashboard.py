import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import psycopg2
import os
from dotenv import load_dotenv
from datetime import datetime

# Load env vars
load_dotenv(dotenv_path=os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".env")))

def get_pg_connection():
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST"),
        port=os.getenv("POSTGRES_PORT"),
        dbname=os.getenv("POSTGRES_DB"),
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD")
    )

def fetch_user_logs(username):
    conn = get_pg_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT date, meal_type, recipe_name, calories_per_serving_kcal,
               cholesterol_mg, saturated_g, trans_g, fiber_g
        FROM user_nutrition_logs
        WHERE username = %s AND date >= CURRENT_DATE - INTERVAL '6 days'
        ORDER BY date ASC
    """, (username,))
    rows = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description]
    cursor.close()
    conn.close()
    return pd.DataFrame(rows, columns=columns)

def fetch_tdee(username):
    conn = get_pg_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT tdee FROM users WHERE username = %s", (username,))
    tdee = cursor.fetchone()
    cursor.close()
    conn.close()
    return int(tdee[0]) if tdee else 2100

def show_nutrition_dashboard():
    st.title("📊 Your Nutrition Dashboard")

    if "username" not in st.session_state or not st.session_state.username:
        st.warning("⚠️ Please log in to view your dashboard.")
        return

    username = st.session_state.username
    tdee = fetch_tdee(username)
    df = fetch_user_logs(username)

    if df.empty:
        st.info("📭 No nutrition logs found for this week.")
        return

    df["date"] = pd.to_datetime(df["date"])
    df["day"] = df["date"].dt.strftime("%a\n%b %d")

    # === 1. Calories vs TDEE ===
    st.subheader("📈 Daily Calorie Intake vs TDEE")
    daily_summary = df.groupby("date").agg({
        "calories_per_serving_kcal": "sum"
        }).reset_index()
    daily_summary["tdee"] = tdee

    fig1, ax1 = plt.subplots(figsize=(10, 4))
    ax1.plot(daily_summary["date"], daily_summary["calories_per_serving_kcal"], marker='o', label="Calories Consumed")
    ax1.plot(daily_summary["date"], daily_summary["tdee"], color="red", linestyle="--", label="TDEE Goal")
    ax1.set_title("Calories vs TDEE (Last 7 Days)")
    ax1.set_ylabel("Calories")
    ax1.set_xlabel("Date")
    ax1.legend()
    ax1.grid(True)
    st.pyplot(fig1)

    # === 2. Pie Chart for Meal Type Distribution ===
    st.subheader("🥧 Meal Type Calorie Distribution")
    meal_summary = df.groupby("meal_type")["calories_per_serving_kcal"].sum()

    fig2, ax2 = plt.subplots()
    colors = sns.color_palette("pastel")
    wedges, texts, autotexts = ax2.pie(meal_summary, labels=meal_summary.index, autopct='%1.1f%%', colors=colors, startangle=140)
    ax2.set_title("Calories Split by Meal Type")
    st.pyplot(fig2)

    # === 3. Smart Dietary Suggestions ===
    st.subheader("🧠 Smart Dietary Suggestions")
    avg_kcal = daily_summary["calories_per_serving_kcal"].mean()
    suggestions = []

    if avg_kcal > tdee:
        suggestions.append("⚠️ You’ve been consuming more than your TDEE. Consider reducing portion sizes.")
    elif avg_kcal < 0.8 * tdee:
        suggestions.append("⚠️ You’re significantly under your TDEE. Ensure you're getting enough energy.")

    avg_fiber = df["fiber_g"].mean()
    if avg_fiber < 3:
        suggestions.append("🌾 Fiber intake is low. Include more oats, legumes, and vegetables.")

    if suggestions:
        for s in suggestions:
            st.markdown(f"- {s}")
    else:
        st.success("🎯 You’re on track nutritionally. Keep it up!")

    # === 7. Meal Logging Consistency Heatmap ===
    st.subheader("✅ Meal Logging Consistency Heatmap")
    heatmap_df = df.groupby(["date", "meal_type"]).size().reset_index(name="count")
    pivot = heatmap_df.pivot(index="meal_type", columns="date", values="count").fillna(0)

    fig3, ax3 = plt.subplots(figsize=(8, 4))
    sns.heatmap(pivot, cmap="YlGnBu", annot=True, fmt=".0f", linewidths=.5, ax=ax3)
    ax3.set_title("Meals Logged Per Day")
    st.pyplot(fig3)

    # === 8. Cholesterol-related Nutrient Stacked Bar ===
    condition = st.session_state.get("chronic_condition", "").lower()
    if condition == "cholesterol":
        st.subheader("❤️ Cholesterol-related Nutrient Tracking")
        chol_df = df.groupby("date")[["cholesterol_mg", "saturated_g", "trans_g"]].sum().reset_index()

        fig4, ax4 = plt.subplots(figsize=(10, 4))
        bar1 = ax4.bar(chol_df["date"], chol_df["cholesterol_mg"], label="Cholesterol (mg)")
        bar2 = ax4.bar(chol_df["date"], chol_df["saturated_g"], bottom=chol_df["cholesterol_mg"], label="Saturated Fat (g)")
        bottom_sum = chol_df["cholesterol_mg"] + chol_df["saturated_g"]
        bar3 = ax4.bar(chol_df["date"], chol_df["trans_g"], bottom=bottom_sum, label="Trans Fat (g)")

        ax4.set_ylabel("mg / g")
        ax4.set_title("Cholesterol, Saturated & Trans Fat Per Day")
        ax4.legend()
        st.pyplot(fig4)

        st.info("✅ Daily Target: Cholesterol < 60mg, Saturated Fat < 6g, Trans Fat < 1g")

    # === Final Table ===
    st.subheader("📋 Weekly Meal Log")
    st.dataframe(df[["date", "meal_type", "recipe_name", "calories_per_serving_kcal"]])
