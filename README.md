# AI-Food-Inventory-Meal-Planner

Tento projekt je jednoduchá aplikácia v Python-e, ktorá umožňuje:

 - Spravovať inventár potravín (pridávať, odstraňovať, upravovať množstvo, označovať ako „Core Items“).
 - Generovať nákupný zoznam na základe chýbajúcich „Core“ položiek a ručne tam pridávať ďalšie položky.
 - Plánovať jedlá na jednotlivé dni v týždni, vrátane generovania receptov pomocou OpenAI GPT.
 - Lokálne ukladanie dát do SQLite databázy (food_inventory2.db).
 - Aplikácia využíva knižnicu Streamlit na vytvorenie interaktívneho webového rozhrania.

**Hlavné funkcie:**

Inventár:
 - Môžete pridať potravinu (názov, kategóriu, množstvo).
 - Môžete označiť položku ako „Core“; ak je jej množstvo 0 alebo je odstránená, presunie sa do nákupného zoznamu.
 - Prehľad položiek je v prehľadnej tabuľke, kde sa dá upraviť množstvo, označiť/odznačiť ako „Core“ alebo položku odstrániť.

Nákupný zoznam:
 - Zobrazuje položky, ktoré chýbajú (hlavne „Core“ s množstvom 0) alebo ktoré si ručne pridáte.
 - Dokážete označiť, koľko kusov ste kúpili, a po kliknutí na tlačidlo sa položky automaticky presunú (alebo navýšia) v inventári.
 - Možnosť pridať novú položku alebo vyprázdniť celý zoznam.
   
Plánovanie jedál:
 - Môžete si naplánovať jedlo (napr. na pondelok – raňajky), vybrať si z inventára ingrediencie a pridať názov jedla.
 - Alebo môžete použiť tlačidlo "Generate GPT Meal", ktoré na základe vybraných ingrediencií požiada OpenAI GPT o recept.
 - Recept sa uloží do databázy a zobrazí sa v týždennom prehľade ako rozbaľovací panel (expander).

Automatické doplnenie receptov:
 - K dispozícii je sekcia AI Recipe Suggestions, kde môžete nechať GPT navrhnúť recept na základe celého inventára (napr. na obed).
   
Lokálna databáza:
 - Všetky údaje sa ukladajú do lokálneho súboru food_inventory2.db s tabuľkami (inventory, core_items, shopping_list, meal_plan).
 - Databáza sa vytvorí automaticky pri prvom spustení, ak neexistuje.

**Požiadavky**

Python 3.8+ (odporúča sa aspoň 3.9)
Knižnice:
 - streamlit (minimálne 1.10, odporúčaná 1.20+)
 - openai
 - pandas
 - sqlite3 (zvyčajne zabudovaná v Pythone)
 - Platný OpenAI API kľúč, ktorý budeš používať na volania GPT.
 - Odporúča sa vytvoriť si virtuálne prostredie (napr. cez venv alebo conda).

**Inštalácia**

Naklonuj repozitár:
 - git clone https://github.com/tvoj-username/ai-food-inventory-meal-planner.git
 - cd ai-food-inventory-planner
   
Vytvor si a aktivuj virtuálne prostredie:
 - python -m venv venv
 - source venv/bin/activate  # Na Windows: venv\Scripts\activate
   
Nainštaluj závislosti:
 - pip install -r requirements.txt
(Predpokladáme, že existuje súbor requirements.txt, kde sú potrebné balíčky. Napríklad:)
 - streamlit>=1.10
 - openai
 - pandas
 - sqlite3  # (ak si to vyžaduje tvoja platforma, inak býva v štandardnom Pythone)
   
V súbore AI_tool.py (alebo akomkoľvek názve skriptu) zmeň OPENAI_API_KEY na svoj vlastný API kľúč.

**Spustenie aplikácie**

Uisti sa, že si v správnom priečinku (kde je skript AI_tool.py) a že máš aktivované virtuálne prostredie.

Spusti príkaz:
 - streamlit run AI_MealPlan.py
 - V konzole uvidíš odkaz (URL) – zvyčajne niečo ako http://localhost:8501.
 - Otvor si ho v prehliadači; zobrazí sa ti interaktívna aplikácia.

   
**Ako aplikácia funguje:**

 - V Add Item to Inventory pridaj názov položky, kategóriu, množstvo a označ, či je Core Item.
 - V Your Inventory uvidíš prehľadnú tabuľku, kde môžeš meniť množstvo, označovať Core alebo odstrániť položku.
 - Ak odstrániš Core položku alebo ju znížiš na 0, automaticky sa pridá do Shopping Listu.
 - V Shopping List môžeš vidieť položky, ktoré chýbajú. Zadaj, koľko kusov kupuješ, a po kliknutí na Update Shopping List sa nákup premietne do inventára.
 - V Plan Your Meals môžeš plánovať jedlá. Buď ručne zadáš názov jedla, alebo klikneš na Generate GPT Meal, vyberieš ingrediencie (z inventára) a GPT ti vygeneruje recept, ktorý sa uloží aj do týždenného prehľadu.
 - V časti Weekly Meal Plan sa zobrazuje zoznam všetkých naplánovaných jedál. Po rozkliknutí expandera vidíš recept a ingrediencie.
 - AI Recipe Suggestions je dobrovoľná sekcia, kde si môžeš nechať poradiť ďalší recept na raňajky/obed/večeru atď.

Tipy / Poznámky

Ak sa ti nepodarí re-run aplikácie (pri staršej verzii Streamlit), používa sa vlastná funkcia custom_rerun(), ktorá ošetrí kompatibilitu.
Celá databáza sa tvorí lokálne (súbor food_inventory2.db v koreňovom priečinku). Ak ho zmažeš, aplikácia si vytvorí čistý nový.
Na GPT dotazy sa používa gpt-3.5-turbo. Ak chceš použiť GPT-4 (alebo iný model), zmeň názov modelu v kóde.
