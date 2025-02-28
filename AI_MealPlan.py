import streamlit as st
import openai
import json
import sqlite3
import pandas as pd
import random

# ========== HELPER RERUN FUNCTION ==========

def custom_rerun():
    """
    Vyskúša st.experimental_rerun (dostupné od ~1.10).
    Ak neexistuje, použije st.set_query_params (1.20+) 
    alebo staršie st.experimental_set_query_params.
    """
    if hasattr(st, "experimental_rerun"):
        st.experimental_rerun()
    else:
        if hasattr(st, "set_query_params"):
            st.set_query_params(_rerun=str(random.random()))
        else:
            st.experimental_set_query_params(_rerun=str(random.random()))

# ========== KONFIGURÁCIA ==========

# OpenAI API Key (Replace with your own API key)
OPENAI_API_KEY = "sk-proj-..."  # <-- Sem vlož svoj OpenAI kľúč
openai.api_key = OPENAI_API_KEY

st.set_page_config(page_title="AI Food Inventory & Meal Planner", layout="wide")
st.title("🍽️ AI Food Inventory & Meal Planner")
st.subheader("Track your ingredients, plan meals, and automate your shopping list")

# ========== PRIPOJENIE K DATABÁZE ==========

conn = sqlite3.connect("food_inventory2.db")
c = conn.cursor()

# Vytvor (ak neexistujú) potrebné tabuľky
c.execute('''
    CREATE TABLE IF NOT EXISTS inventory (
        item TEXT PRIMARY KEY, 
        category TEXT, 
        quantity INTEGER
    )
''')

c.execute('''
    CREATE TABLE IF NOT EXISTS core_items (
        item TEXT PRIMARY KEY
    )
''')

c.execute('''
    CREATE TABLE IF NOT EXISTS shopping_list (
        item TEXT PRIMARY KEY
    )
''')

# Vytvoríme (ak neexistuje) tabuľku meal_plan
c.execute('''
    CREATE TABLE IF NOT EXISTS meal_plan (
        day TEXT, 
        meal TEXT, 
        ingredients TEXT,
        meal_type TEXT
    )
''')

# Skúsime pridať stĺpec "recipe" do meal_plan (ak ho už máš, preskočí sa)
try:
    c.execute("ALTER TABLE meal_plan ADD COLUMN recipe TEXT;")
except sqlite3.OperationalError:
    pass

conn.commit()

# ========== FUNKCIE NA PRÁCU S DB ==========

def add_item(item, category, quantity):
    c.execute("INSERT OR REPLACE INTO inventory (item, category, quantity) VALUES (?, ?, ?)", (item, category, quantity))
    conn.commit()

def remove_item(item):
    c.execute("DELETE FROM inventory WHERE item = ?", (item,))
    conn.commit()

def update_quantity(item, quantity):
    c.execute("UPDATE inventory SET quantity = ? WHERE item = ?", (quantity, item))
    conn.commit()

def get_inventory():
    c.execute("SELECT item, category, quantity FROM inventory")
    return c.fetchall()

def get_core_items():
    c.execute("SELECT item FROM core_items")
    return [row[0] for row in c.fetchall()]

def add_core_item(item):
    c.execute("INSERT OR REPLACE INTO core_items (item) VALUES (?)", (item,))
    conn.commit()

def remove_core_item(item):
    c.execute("DELETE FROM core_items WHERE item = ?", (item,))
    conn.commit()

def get_shopping_list():
    c.execute("SELECT item FROM shopping_list")
    return [row[0] for row in c.fetchall()]

def add_to_shopping_list(item):
    c.execute("INSERT OR REPLACE INTO shopping_list (item) VALUES (?)", (item,))
    conn.commit()

def remove_from_shopping_list(item):
    c.execute("DELETE FROM shopping_list WHERE item = ?", (item,))
    conn.commit()

# Tu pridáme recept ako voliteľný parameter s predvolenou hodnotou ""
def add_meal_plan(day, meal, ingredients, meal_type, recipe=""):
    c.execute("""
        INSERT INTO meal_plan (day, meal, ingredients, meal_type, recipe)
        VALUES (?, ?, ?, ?, ?)
    """, (day, meal, ingredients, meal_type, recipe))
    conn.commit()

# Aktualizujeme tak, aby sme načítali aj stĺpec recipe
def get_meal_plan():
    c.execute("SELECT day, meal, ingredients, meal_type, recipe FROM meal_plan")
    return c.fetchall()

# ========== SEKCIA: PRIDANIE NOVÝCH POLOŽIEK DO INVENTÁRA ==========

st.subheader("📌 Add Item to Inventory")
with st.form("add_item_form"):
    item_name = st.text_input("Item Name")
    category = st.selectbox("Category", ["Vegetables", "Fruits", "Dairy", "Meat", "Grains", "Others"])
    quantity = st.number_input("Quantity", min_value=1, step=1, value=1)
    core = st.checkbox("Mark as Core Item")
    submitted = st.form_submit_button("Add Item")
    
    if submitted and item_name.strip():
        add_item(item_name.strip(), category, quantity)
        if core:
            add_core_item(item_name.strip())
        st.success(f"Added {item_name} to inventory.")
        custom_rerun()

# ========== SEKCIA: TABUĽKA INVENTÁRA (EDITOVATEĽNÁ) ==========

st.subheader("📋 Your Inventory")

# 1) Načítame inventory a core items
inventory_data = get_inventory()  # List of tuples (item, category, quantity)
core_items_list = get_core_items()  # List of strings

# 2) Vložíme do dataframe + stĺpec "core" a "remove"
df_inventory = pd.DataFrame(inventory_data, columns=["item", "category", "quantity"])

# Ak je inventory prázdny, len zobraz správu a nepokračuj
if df_inventory.empty:
    st.info("Your inventory is empty. Please add some items.")
else:
    df_inventory["core"] = df_inventory["item"].apply(lambda x: x in core_items_list)
    df_inventory["remove"] = False

    edited_df = st.data_editor(
        df_inventory,
        num_rows="fixed",
        disabled=["item", "category"], 
        key="inventory_editor"
    )

    if st.button("Save Inventory Changes"):
        for idx, row in edited_df.iterrows():
            item_name = row["item"]
            old_row = df_inventory.loc[idx]
            old_quantity = old_row["quantity"]
            old_core = old_row["core"]
            
            new_quantity = row["quantity"]
            new_core = row["core"]
            remove_flag = row["remove"]
            
            # Odstránenie z DB => ak bola core, ide do shopping listu
            if remove_flag:
                if old_core:
                    add_to_shopping_list(item_name)  # Ak to bola core položka, presunie sa do shopping list
                remove_item(item_name)
                remove_core_item(item_name)
                continue
            
            # Update množstva
            if new_quantity != old_quantity:
                update_quantity(item_name, new_quantity)
                # Ak je core a množstvo je 0 => pridaj do shopping list
                if new_core and new_quantity == 0:
                    add_to_shopping_list(item_name)
            
            # Update core
            if new_core != old_core:
                if new_core:
                    add_core_item(item_name)
                    # Ak quantity = 0 => automaticky do shopping list
                    if new_quantity == 0:
                        add_to_shopping_list(item_name)
                else:
                    remove_core_item(item_name)

        st.success("Inventory updated successfully.")
        custom_rerun()

# ========== SEKCIA: SHOPPING LIST ==========

st.subheader("🛒 Shopping List")

shopping_data = get_shopping_list()
if len(shopping_data) == 0:
    st.info("Your shopping list is empty.")
else:
    df_shopping = pd.DataFrame(shopping_data, columns=["item"])
    df_shopping["bought_quantity"] = 0
    df_shopping["add_to_inventory"] = False
    
    edited_shopping_df = st.data_editor(
        df_shopping,
        num_rows="fixed",
        disabled=["item"],
        key="shopping_editor"
    )
    
    if st.button("Update Shopping List"):
        for idx, row in edited_shopping_df.iterrows():
            item_name = row["item"]
            bought_qty = row["bought_quantity"]
            add_flag = row["add_to_inventory"]
            
            if add_flag and bought_qty > 0:
                c.execute("SELECT quantity FROM inventory WHERE item = ?", (item_name,))
                res = c.fetchone()
                if res is None:
                    add_item(item_name, "Others", bought_qty)
                else:
                    current_qty = res[0]
                    update_quantity(item_name, current_qty + bought_qty)
                
                remove_from_shopping_list(item_name)
        
        st.success("Shopping list updated. Items moved to inventory where needed.")
        custom_rerun()

# Pridanie novej položky do shopping listu
add_shopping_item = st.text_input("Add item to shopping list", key="add_shopping_item")
if st.button("Add to Shopping List"):
    if add_shopping_item.strip():
        add_to_shopping_list(add_shopping_item.strip())
        st.success(f"Added {add_shopping_item} to shopping list.")
        custom_rerun()

# Tlačidlo na kompletné vymazanie shopping listu
if st.button("Clear Shopping List"):
    c.execute("DELETE FROM shopping_list")
    conn.commit()
    custom_rerun()

# ========== SEKCIA: PLÁNOVANIE JEDÁL ==========

st.subheader("🍽️ Plan Your Meals")

day = st.selectbox("Day", ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"])
meal_type = st.selectbox("Meal Type", ["Raňajky", "Obed", "Večera", "Zákusok", "Snack", "Others"])
ingredients_inventory = get_inventory()
ingredients_selected = st.multiselect("Select Ingredients from Inventory", [item[0] for item in ingredients_inventory])
meal = st.text_input("Meal Name")

col1, col2 = st.columns(2)

with col1:
    # Ručné pridanie do meal plan
    if st.button("Add Meal Plan"):
        add_meal_plan(day, meal, ", ".join(ingredients_selected), meal_type, recipe="")
        st.success(f"Added {meal} ({meal_type}) to {day} meal plan (no recipe).")
        custom_rerun()

with col2:
    # Vygenerovať recept cez GPT a uložiť do meal_plan
    if st.button("Generate GPT Meal"):
        # Zavoláme GPT s vybranými ingredienciami
        user_ingredients = ", ".join(ingredients_selected)
        prompt = f"""
        Si AI kuchár. Mám tieto ingrediencie: {user_ingredients}.
        Navrhni jedlo (názov) a stručný recept (postup) v slovenskom jazyku.
        Typ jedla: {meal_type}.
        Vráť to ako krátky text, kde bude názov a postup.
        """
        
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Si AI asistent v slovenčine, ktorý pomáha s receptami."},
                {"role": "user", "content": prompt}
            ]
        )
        gpt_recipe = response.choices[0].message.content.strip()
        
        # Rozhodneme, ako vyplníme "meal_name".
        # Buď user zadal "Meal Name" manuálne, alebo dáme "GPT Meal" atď.
        # Prípadne môžeme skúsiť extrahovať 1. riadok ako názov z GPT.
        # Pre jednoduchosť: ak user zadal meal, berieme ho, inak "GPT Meal".
        meal_name = meal.strip() if meal.strip() else f"GPT Meal - {meal_type}"
        
        # Uložíme do DB
        add_meal_plan(day, meal_name, user_ingredients, meal_type, recipe=gpt_recipe)
        
        st.success(f"GPT Meal generated and added to {day} meal plan.")
        custom_rerun()

# ========== ZOBRAZENIE TÝŽDENNÉHO PLÁNU ==========

st.subheader("📆 Weekly Meal Plan")
meal_plan = get_meal_plan()
if len(meal_plan) == 0:
    st.info("No meals planned yet.")
else:
    # meal_plan = [(day, meal, ingredients, meal_type, recipe), ...]
    for d, m, ingr, mtype, recipe in meal_plan:
        # Urobíme expander, kde sa zobrazí recept
        with st.expander(f"{d} | {mtype}: {m} (Ingredients: {ingr})"):
            if recipe:
                st.markdown(recipe)
            else:
                st.write("_No recipe provided._")

# Tlačidlo na vyčistenie meal plánov
if st.button("Clear Meal Plan"):
    c.execute("DELETE FROM meal_plan")
    conn.commit()
    custom_rerun()

# ========== SEKCIA: AI RECIPE SUGGESTIONS (PONECHANÁ) ==========

st.subheader("🤖 AI Recipe Suggestions")

meal_type_for_ai = st.selectbox(
    "For which type of meal do you want a recipe?",
    ["Raňajky", "Obed", "Večera", "Zákusok", "Snack", "Any"]
)

if st.button("Get Recipe Based on Inventory"):
    inventory_items = ", ".join([item[0] for item in get_inventory()])
    core_items = ", ".join(get_core_items())
    
    prompt = f"""
    Si AI asistent, ktorý pomáha používateľom nájsť najlepšie recepty
    na {meal_type_for_ai.lower()} podľa dostupných ingrediencií.
    Tvoje dostupné ingrediencie: {inventory_items}
    Core (kľúčové) ingrediencie, ktoré by mali byť vždy na sklade: {core_items}
    
    Navrhni vhodný recept v slovenskom jazyku (s postupom), aby zodpovedal zvolenému typu jedla: {meal_type_for_ai}.
    Buď kreatívny, stručný a uveď aj krátky postup prípravy.
    """
    
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "Si AI asistent v slovenčine, ktorý pomáha s receptami."},
            {"role": "user", "content": prompt}
        ]
    )
    recipe = response.choices[0].message.content.strip()
    st.markdown(recipe)

# ========== UKONČENIE ==========

conn.close()
