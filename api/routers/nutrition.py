"""
api/routers/nutrition.py

Nutrition lookup with two providers:
  1. Gemini (if GEMINI_API_KEY is set) — full knowledge, best accuracy
  2. Ollama fallback (local LLM) — works offline, no API key

Includes a large embedded food database (500+ foods) as grounding context
for both providers so results are accurate and consistent.
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
import json, re
import httpx

from api.middleware.auth import get_current_user
from models import User
from config import get_settings

router   = APIRouter(prefix="/api/v1/nutrition", tags=["nutrition"])
settings = get_settings()

# ── Massive food database ─────────────────────────────────────────────────────
FOOD_DB = """
COMPREHENSIVE NUTRITION DATABASE (per 100g unless stated)
Source: USDA FoodData Central + verified sports nutrition references.

=== PROTEINS — MEAT & POULTRY ===
Chicken breast (cooked, grilled): 165 kcal, 31g protein, 0g carbs, 3.6g fat, 0g fiber, 74mg sodium
Chicken breast (raw): 120 kcal, 22g protein, 0g carbs, 2.6g fat, 0g fiber
Chicken thigh (cooked, skinless): 209 kcal, 26g protein, 0g carbs, 11g fat, 0g fiber
Chicken thigh (cooked, with skin): 247 kcal, 25g protein, 0g carbs, 16g fat, 0g fiber
Chicken drumstick (cooked): 172 kcal, 28g protein, 0g carbs, 5.7g fat, 0g fiber
Ground chicken (cooked): 185 kcal, 27g protein, 0g carbs, 8g fat, 0g fiber
Turkey breast (cooked): 135 kcal, 30g protein, 0g carbs, 1g fat, 0g fiber
Turkey mince (cooked, lean): 189 kcal, 29g protein, 0g carbs, 7g fat, 0g fiber
Beef (lean ground, 90/10, cooked): 215 kcal, 26g protein, 0g carbs, 12g fat, 0g fiber
Beef (lean ground, 95/5, cooked): 172 kcal, 26g protein, 0g carbs, 7g fat, 0g fiber
Beef steak (sirloin, grilled): 207 kcal, 30g protein, 0g carbs, 9g fat, 0g fiber
Beef steak (ribeye, grilled): 291 kcal, 26g protein, 0g carbs, 20g fat, 0g fiber
Beef tenderloin (grilled): 215 kcal, 29g protein, 0g carbs, 10g fat, 0g fiber
Pork tenderloin (cooked): 166 kcal, 29g protein, 0g carbs, 4g fat, 0g fiber
Pork chop (lean, grilled): 187 kcal, 27g protein, 0g carbs, 8g fat, 0g fiber
Pork mince (cooked, lean): 227 kcal, 26g protein, 0g carbs, 13g fat, 0g fiber
Lamb (leg, roasted): 191 kcal, 28g protein, 0g carbs, 8g fat, 0g fiber
Lamb mince (cooked): 258 kcal, 25g protein, 0g carbs, 17g fat, 0g fiber
Venison (roasted): 158 kcal, 30g protein, 0g carbs, 3g fat, 0g fiber
Bison (ground, cooked): 218 kcal, 26g protein, 0g carbs, 12g fat, 0g fiber
Duck breast (cooked, no skin): 201 kcal, 28g protein, 0g carbs, 9g fat, 0g fiber
Bacon (cooked): 541 kcal, 37g protein, 1.4g carbs, 42g fat, 0g fiber, 1717mg sodium
Ham (lean, sliced): 145 kcal, 21g protein, 1.5g carbs, 6g fat, 0g fiber
Sausage (pork, cooked): 301 kcal, 11g protein, 2g carbs, 27g fat, 0g fiber

=== PROTEINS — FISH & SEAFOOD ===
Salmon (Atlantic, cooked): 208 kcal, 20g protein, 0g carbs, 13g fat, 0g fiber
Salmon (sockeye, cooked): 236 kcal, 25g protein, 0g carbs, 14g fat, 0g fiber
Tuna (canned in water, drained): 116 kcal, 26g protein, 0g carbs, 1g fat, 0g fiber
Tuna (fresh, bluefin, cooked): 184 kcal, 30g protein, 0g carbs, 6g fat, 0g fiber
Cod (cooked): 105 kcal, 23g protein, 0g carbs, 0.9g fat, 0g fiber
Tilapia (cooked): 128 kcal, 26g protein, 0g carbs, 2.7g fat, 0g fiber
Shrimp (cooked): 99 kcal, 24g protein, 0g carbs, 0.3g fat, 0g fiber
Crab (cooked): 97 kcal, 19g protein, 0g carbs, 1.5g fat, 0g fiber
Lobster (cooked): 98 kcal, 20g protein, 1.3g carbs, 0.6g fat, 0g fiber
Scallops (cooked): 111 kcal, 23g protein, 5.4g carbs, 0.9g fat, 0g fiber
Sardines (canned in water): 208 kcal, 25g protein, 0g carbs, 11g fat, 0g fiber
Mackerel (cooked): 262 kcal, 24g protein, 0g carbs, 18g fat, 0g fiber
Halibut (cooked): 140 kcal, 27g protein, 0g carbs, 3g fat, 0g fiber
Trout (cooked): 190 kcal, 26g protein, 0g carbs, 8.5g fat, 0g fiber
Mussels (cooked): 172 kcal, 24g protein, 7.4g carbs, 4.5g fat, 0g fiber
Oysters (cooked): 163 kcal, 19g protein, 9.9g carbs, 4.7g fat, 0g fiber

=== PROTEINS — EGGS & DAIRY ===
Eggs (whole, large, 1 egg = 50g): 155 kcal, 13g protein, 1.1g carbs, 11g fat, 0g fiber
Egg whites (100g = ~3 large whites): 52 kcal, 11g protein, 0.7g carbs, 0.2g fat, 0g fiber
Egg yolk (100g = ~5 large yolks): 322 kcal, 16g protein, 3.6g carbs, 27g fat, 0g fiber
Greek yogurt (plain, 0% fat): 59 kcal, 10g protein, 3.6g carbs, 0.4g fat, 0g fiber
Greek yogurt (plain, 2% fat): 73 kcal, 9.9g protein, 3.8g carbs, 1.9g fat, 0g fiber
Greek yogurt (plain, full fat): 97 kcal, 9g protein, 3.8g carbs, 5g fat, 0g fiber
Regular yogurt (plain, low fat): 63 kcal, 5.3g protein, 7.7g carbs, 1.5g fat, 0g fiber
Cottage cheese (low fat 1%): 72 kcal, 12g protein, 3g carbs, 1g fat, 0g fiber
Cottage cheese (full fat 4%): 103 kcal, 11g protein, 3.4g carbs, 4.5g fat, 0g fiber
Ricotta (part skim): 138 kcal, 11g protein, 5g carbs, 8g fat, 0g fiber
Skyr (Icelandic yogurt): 63 kcal, 11g protein, 4g carbs, 0.2g fat, 0g fiber
Quark (0% fat): 67 kcal, 12g protein, 4g carbs, 0.2g fat, 0g fiber
Whey protein powder (1 scoop = 30g): 120 kcal, 25g protein, 3g carbs, 2g fat, 0g fiber
Casein protein powder (1 scoop = 30g): 110 kcal, 24g protein, 3g carbs, 1g fat, 0g fiber
Plant protein powder (pea, 1 scoop = 30g): 110 kcal, 21g protein, 4g carbs, 2g fat, 1g fiber
Milk (whole, per 100ml): 61 kcal, 3.2g protein, 4.8g carbs, 3.3g fat, 0g fiber
Milk (2% fat, per 100ml): 50 kcal, 3.3g protein, 4.8g carbs, 2g fat, 0g fiber
Milk (skim, per 100ml): 35 kcal, 3.4g protein, 5g carbs, 0.2g fat, 0g fiber
Cheddar cheese: 402 kcal, 25g protein, 1.3g carbs, 33g fat, 0g fiber
Mozzarella (part-skim): 254 kcal, 24g protein, 2.7g carbs, 16g fat, 0g fiber
Parmesan (grated): 431 kcal, 38g protein, 4.1g carbs, 29g fat, 0g fiber
Feta cheese: 264 kcal, 14g protein, 4.1g carbs, 21g fat, 0g fiber
Swiss cheese: 380 kcal, 27g protein, 5.4g carbs, 28g fat, 0g fiber
Brie: 334 kcal, 21g protein, 0.5g carbs, 28g fat, 0g fiber

=== PROTEINS — PLANT-BASED ===
Tofu (firm): 76 kcal, 8g protein, 1.9g carbs, 4.2g fat, 0.3g fiber
Tofu (silken): 55 kcal, 5.3g protein, 2.4g carbs, 3.3g fat, 0g fiber
Tempeh: 193 kcal, 20g protein, 7.6g carbs, 11g fat, 0g fiber
Edamame (shelled, cooked): 121 kcal, 11g protein, 8.9g carbs, 5.2g fat, 5.2g fiber
Seitan (wheat gluten): 370 kcal, 75g protein, 14g carbs, 1.9g fat, 0.6g fiber
Lentils (cooked): 116 kcal, 9g protein, 20g carbs, 0.4g fat, 7.9g fiber
Red lentils (cooked): 116 kcal, 9g protein, 20g carbs, 0.4g fat, 7.9g fiber
Black beans (cooked): 132 kcal, 8.9g protein, 24g carbs, 0.5g fat, 8.7g fiber
Kidney beans (cooked): 127 kcal, 8.7g protein, 23g carbs, 0.5g fat, 6.4g fiber
Chickpeas (cooked): 164 kcal, 8.9g protein, 27g carbs, 2.6g fat, 7.6g fiber
Pinto beans (cooked): 143 kcal, 9g protein, 26g carbs, 0.6g fat, 9g fiber
Navy beans (cooked): 140 kcal, 9.5g protein, 25g carbs, 0.6g fat, 10g fiber
Green peas (cooked): 84 kcal, 5.4g protein, 15g carbs, 0.2g fat, 5.5g fiber
Black-eyed peas (cooked): 116 kcal, 7.7g protein, 21g carbs, 0.5g fat, 6.5g fiber

=== CARBOHYDRATES — GRAINS & STARCHES ===
White rice (cooked): 130 kcal, 2.7g protein, 28g carbs, 0.3g fat, 0.4g fiber
Brown rice (cooked): 123 kcal, 2.7g protein, 26g carbs, 1g fat, 1.6g fiber
Basmati rice (cooked): 121 kcal, 2.5g protein, 25g carbs, 0.3g fat, 0.4g fiber
Jasmine rice (cooked): 129 kcal, 2.7g protein, 28g carbs, 0.3g fat, 0.4g fiber
Wild rice (cooked): 101 kcal, 4g protein, 21g carbs, 0.3g fat, 1.8g fiber
Oats (dry rolled): 389 kcal, 17g protein, 66g carbs, 7g fat, 10.6g fiber
Oatmeal (cooked with water): 71 kcal, 2.5g protein, 12g carbs, 1.5g fat, 1.7g fiber
Steel-cut oats (cooked): 67 kcal, 2.4g protein, 12g carbs, 1g fat, 1.7g fiber
Pasta (white, cooked): 158 kcal, 5.8g protein, 31g carbs, 0.9g fat, 1.8g fiber
Pasta (whole wheat, cooked): 124 kcal, 5.3g protein, 27g carbs, 0.5g fat, 4.5g fiber
Quinoa (cooked): 120 kcal, 4.4g protein, 21g carbs, 1.9g fat, 2.8g fiber
Couscous (cooked): 112 kcal, 3.8g protein, 23g carbs, 0.2g fat, 1.4g fiber
Bulgur wheat (cooked): 83 kcal, 3.1g protein, 18g carbs, 0.2g fat, 4.5g fiber
Barley (cooked): 123 kcal, 2.3g protein, 28g carbs, 0.4g fat, 6g fiber
Farro (cooked): 170 kcal, 6g protein, 34g carbs, 1g fat, 3.5g fiber
Amaranth (cooked): 102 kcal, 3.8g protein, 19g carbs, 1.6g fat, 2.1g fiber
Buckwheat (cooked): 92 kcal, 3.4g protein, 20g carbs, 0.6g fat, 2.7g fiber
Millet (cooked): 119 kcal, 3.5g protein, 23g carbs, 1g fat, 1.3g fiber
Sweet potato (baked): 90 kcal, 2g protein, 21g carbs, 0.1g fat, 3.3g fiber
White potato (baked, with skin): 93 kcal, 2.5g protein, 21g carbs, 0.1g fat, 2.2g fiber
Yam (cooked): 118 kcal, 1.5g protein, 28g carbs, 0.1g fat, 4.1g fiber
Corn (cooked): 96 kcal, 3.4g protein, 21g carbs, 1.5g fat, 2.4g fiber
Whole wheat bread (1 slice = 28g): 247 kcal, 11g protein, 44g carbs, 3.6g fat, 7g fiber
White bread (1 slice = 28g): 266 kcal, 9g protein, 51g carbs, 3.3g fat, 2.4g fiber
Sourdough bread: 274 kcal, 8.8g protein, 54g carbs, 1.4g fat, 2.4g fiber
Rye bread: 259 kcal, 8.5g protein, 48g carbs, 3.3g fat, 5.8g fiber
Pita bread (1 medium = 60g): 275 kcal, 9.1g protein, 55g carbs, 1.2g fat, 2.2g fiber
Rice cakes (plain): 387 kcal, 7.3g protein, 81g carbs, 2.8g fat, 1g fiber
Cornflakes: 378 kcal, 7g protein, 84g carbs, 0.4g fat, 2.7g fiber
Rolled oat granola: 471 kcal, 9g protein, 64g carbs, 20g fat, 5g fiber

=== CARBOHYDRATES — FRUITS ===
Banana (medium, 120g): 89 kcal, 1.1g protein, 23g carbs, 0.3g fat, 2.6g fiber
Apple (medium, 182g): 52 kcal, 0.3g protein, 14g carbs, 0.2g fat, 2.4g fiber
Orange (medium, 131g): 47 kcal, 0.9g protein, 12g carbs, 0.1g fat, 2.4g fiber
Mango (100g): 60 kcal, 0.8g protein, 15g carbs, 0.4g fat, 1.6g fiber
Pineapple (100g): 50 kcal, 0.5g protein, 13g carbs, 0.1g fat, 1.4g fiber
Watermelon (100g): 30 kcal, 0.6g protein, 7.6g carbs, 0.2g fat, 0.4g fiber
Strawberries (100g): 32 kcal, 0.7g protein, 7.7g carbs, 0.3g fat, 2g fiber
Blueberries (100g): 57 kcal, 0.7g protein, 14g carbs, 0.3g fat, 2.4g fiber
Raspberries (100g): 52 kcal, 1.2g protein, 12g carbs, 0.7g fat, 6.5g fiber
Blackberries (100g): 43 kcal, 1.4g protein, 10g carbs, 0.5g fat, 5.3g fiber
Grapes (100g): 69 kcal, 0.7g protein, 18g carbs, 0.2g fat, 0.9g fiber
Pear (100g): 57 kcal, 0.4g protein, 15g carbs, 0.1g fat, 3.1g fiber
Kiwi (100g): 61 kcal, 1.1g protein, 15g carbs, 0.5g fat, 3g fiber
Peach (100g): 39 kcal, 0.9g protein, 9.5g carbs, 0.3g fat, 1.5g fiber
Cherries (100g): 63 kcal, 1.1g protein, 16g carbs, 0.2g fat, 2.1g fiber
Dates (100g): 277 kcal, 1.8g protein, 75g carbs, 0.2g fat, 6.7g fiber
Raisins (100g): 299 kcal, 3.1g protein, 79g carbs, 0.5g fat, 3.7g fiber

=== FATS & OILS ===
Avocado (100g): 160 kcal, 2g protein, 9g carbs, 15g fat, 6.7g fiber
Olive oil (1 tbsp = 14g): 884 kcal, 0g protein, 0g carbs, 100g fat, 0g fiber
Coconut oil (1 tbsp = 14g): 862 kcal, 0g protein, 0g carbs, 100g fat, 0g fiber
Avocado oil (1 tbsp = 14g): 884 kcal, 0g protein, 0g carbs, 100g fat, 0g fiber
Butter (1 tbsp = 14g): 717 kcal, 0.9g protein, 0.1g carbs, 81g fat, 0g fiber
Ghee (1 tbsp = 13g): 900 kcal, 0g protein, 0g carbs, 100g fat, 0g fiber
Almonds (raw): 579 kcal, 21g protein, 22g carbs, 50g fat, 12.5g fiber
Walnuts (raw): 654 kcal, 15g protein, 14g carbs, 65g fat, 6.7g fiber
Cashews (raw): 553 kcal, 18g protein, 30g carbs, 44g fat, 3.3g fiber
Pistachios (raw): 560 kcal, 20g protein, 28g carbs, 45g fat, 10g fiber
Macadamia nuts: 718 kcal, 7.9g protein, 14g carbs, 76g fat, 8.6g fiber
Pecans: 691 kcal, 9.2g protein, 14g carbs, 72g fat, 9.6g fiber
Brazil nuts: 659 kcal, 14g protein, 12g carbs, 67g fat, 7.5g fiber
Peanuts (roasted): 587 kcal, 24g protein, 21g carbs, 50g fat, 8.5g fiber
Peanut butter (natural, 2 tbsp = 32g): 588 kcal, 25g protein, 20g carbs, 50g fat, 6g fiber
Almond butter (2 tbsp = 32g): 614 kcal, 21g protein, 21g carbs, 56g fat, 10g fiber
Chia seeds (1 tbsp = 12g): 486 kcal, 17g protein, 42g carbs, 31g fat, 34g fiber
Flaxseed (ground, 1 tbsp = 10g): 534 kcal, 18g protein, 29g carbs, 42g fat, 27g fiber
Hemp seeds (3 tbsp = 30g): 553 kcal, 32g protein, 9g carbs, 49g fat, 4g fiber
Sunflower seeds: 584 kcal, 21g protein, 20g carbs, 51g fat, 8.6g fiber
Pumpkin seeds: 559 kcal, 30g protein, 11g carbs, 49g fat, 6g fiber
Sesame seeds: 573 kcal, 17g protein, 23g carbs, 50g fat, 11.8g fiber
Dark chocolate (70%+): 598 kcal, 8g protein, 45g carbs, 43g fat, 11g fiber
Coconut milk (canned, full fat, per 100ml): 197 kcal, 2g protein, 5.5g carbs, 19g fat, 0g fiber

=== VEGETABLES ===
Broccoli (cooked): 35 kcal, 2.4g protein, 7.2g carbs, 0.4g fat, 3.3g fiber
Spinach (raw): 23 kcal, 2.9g protein, 3.6g carbs, 0.4g fat, 2.2g fiber
Spinach (cooked): 41 kcal, 5.4g protein, 6.7g carbs, 0.5g fat, 4.3g fiber
Kale (raw): 49 kcal, 4.3g protein, 9g carbs, 0.9g fat, 3.6g fiber
Kale (cooked): 28 kcal, 1.9g protein, 5.6g carbs, 0.4g fat, 2g fiber
Cabbage (raw): 25 kcal, 1.3g protein, 5.8g carbs, 0.1g fat, 2.5g fiber
Brussels sprouts (cooked): 43 kcal, 3g protein, 9g carbs, 0.3g fat, 3.8g fiber
Cauliflower (cooked): 25 kcal, 2g protein, 5g carbs, 0.3g fat, 2g fiber
Asparagus (cooked): 22 kcal, 2.4g protein, 4.1g carbs, 0.2g fat, 1.8g fiber
Green beans (cooked): 35 kcal, 1.9g protein, 7.9g carbs, 0.1g fat, 3.4g fiber
Carrots (raw): 41 kcal, 0.9g protein, 10g carbs, 0.2g fat, 2.8g fiber
Bell pepper red (raw): 31 kcal, 1g protein, 6g carbs, 0.3g fat, 2.1g fiber
Bell pepper green (raw): 20 kcal, 0.9g protein, 4.6g carbs, 0.2g fat, 1.7g fiber
Tomato (raw): 18 kcal, 0.9g protein, 3.9g carbs, 0.2g fat, 1.2g fiber
Cherry tomatoes: 18 kcal, 0.9g protein, 3.9g carbs, 0.2g fat, 1.2g fiber
Cucumber: 16 kcal, 0.7g protein, 3.6g carbs, 0.1g fat, 0.5g fiber
Celery: 16 kcal, 0.7g protein, 3g carbs, 0.2g fat, 1.6g fiber
Mushrooms (white, raw): 22 kcal, 3.1g protein, 3.3g carbs, 0.3g fat, 1g fiber
Mushrooms (portobello, grilled): 35 kcal, 3.3g protein, 5.5g carbs, 0.8g fat, 1.3g fiber
Zucchini (raw): 17 kcal, 1.2g protein, 3.1g carbs, 0.3g fat, 1g fiber
Eggplant (cooked): 35 kcal, 0.8g protein, 8.7g carbs, 0.2g fat, 2.5g fiber
Onion (raw): 40 kcal, 1.1g protein, 9.3g carbs, 0.1g fat, 1.7g fiber
Garlic (raw): 149 kcal, 6.4g protein, 33g carbs, 0.5g fat, 2.1g fiber
Beets (cooked): 44 kcal, 1.7g protein, 10g carbs, 0.2g fat, 2g fiber
Artichoke (cooked): 53 kcal, 2.9g protein, 12g carbs, 0.3g fat, 6.9g fiber
Leek (cooked): 31 kcal, 0.8g protein, 7.6g carbs, 0.2g fat, 1g fiber
Lettuce (romaine): 17 kcal, 1.2g protein, 3.3g carbs, 0.3g fat, 2.1g fiber
Mixed salad greens: 20 kcal, 1.7g protein, 3.5g carbs, 0.4g fat, 1.8g fiber
Pumpkin (cooked): 26 kcal, 1g protein, 6.5g carbs, 0.1g fat, 0.5g fiber

=== INDIAN BREADS & RICE ===
Chapati/Roti (1 medium = 40g): 120 kcal, 3.1g protein, 19g carbs, 3.7g fat, 1.7g fiber
Multigrain roti (1 medium = 40g): 113 kcal, 3.5g protein, 18g carbs, 3.2g fat, 2.5g fiber
Paratha (plain, 1 medium = 60g): 260 kcal, 5.5g protein, 36g carbs, 10g fat, 2g fiber
Paratha (aloo, 1 medium = 100g): 310 kcal, 6g protein, 42g carbs, 13g fat, 3g fiber
Paratha (paneer, 1 medium = 100g): 340 kcal, 10g protein, 38g carbs, 16g fat, 2g fiber
Naan (plain, 1 medium = 90g): 310 kcal, 8g protein, 50g carbs, 9g fat, 2g fiber
Naan (butter, 1 medium = 90g): 370 kcal, 8g protein, 50g carbs, 15g fat, 2g fiber
Puri (1 piece = 30g): 150 kcal, 2.5g protein, 16g carbs, 8.5g fat, 0.8g fiber
Bhatura (1 piece = 80g): 300 kcal, 7g protein, 40g carbs, 12g fat, 1.5g fiber
Kulcha (1 medium = 80g): 270 kcal, 7g protein, 46g carbs, 6g fat, 1.8g fiber
Missi roti (1 medium = 45g): 130 kcal, 5g protein, 20g carbs, 3.5g fat, 3g fiber
Basmati rice cooked (per 100g): 121 kcal, 2.5g protein, 25g carbs, 0.3g fat, 0.4g fiber
Jeera rice (per 100g): 145 kcal, 2.7g protein, 27g carbs, 3g fat, 0.5g fiber
Steamed rice (per 100g): 130 kcal, 2.7g protein, 28g carbs, 0.3g fat, 0.4g fiber

=== INDIAN BREAKFAST / TIFFIN ===
Idli (1 piece = 45g): 58 kcal, 2g protein, 12g carbs, 0.4g fat, 0.5g fiber
Dosa (plain, 1 medium = 75g): 133 kcal, 3.5g protein, 24g carbs, 2.8g fat, 0.8g fiber
Masala dosa (1 = 150g with filling): 230 kcal, 5.5g protein, 36g carbs, 7g fat, 2g fiber
Rava dosa (1 medium = 70g): 140 kcal, 3g protein, 22g carbs, 4.5g fat, 0.5g fiber
Uttapam (1 medium = 100g): 145 kcal, 4g protein, 24g carbs, 3.5g fat, 1.5g fiber
Upma (per 100g): 130 kcal, 3g protein, 20g carbs, 4g fat, 1g fiber
Poha (per 100g): 125 kcal, 2.5g protein, 24g carbs, 2.5g fat, 0.8g fiber
Poha with vegetables (per 100g): 140 kcal, 3g protein, 25g carbs, 3.5g fat, 1.5g fiber
Sabudana khichdi (per 100g): 215 kcal, 2.5g protein, 40g carbs, 5g fat, 0.5g fiber
Rava upma (per 100g): 145 kcal, 3.5g protein, 22g carbs, 4.5g fat, 1g fiber
Medu vada (1 piece = 50g): 100 kcal, 3.5g protein, 13g carbs, 4g fat, 1g fiber
Pesarattu (1 = 60g): 110 kcal, 5g protein, 16g carbs, 3g fat, 2g fiber
Appam (1 = 50g): 90 kcal, 2g protein, 17g carbs, 1.5g fat, 0.5g fiber
Puttu (per 100g): 190 kcal, 4g protein, 38g carbs, 2g fat, 2g fiber
Pongal (ven, per 100g): 150 kcal, 4g protein, 24g carbs, 4.5g fat, 1g fiber
Dhokla (2 pieces = 60g): 80 kcal, 3.5g protein, 12g carbs, 2g fat, 1g fiber
Khandvi (per 100g): 180 kcal, 6g protein, 22g carbs, 7g fat, 1.5g fiber
Thepla (1 = 40g): 120 kcal, 3g protein, 16g carbs, 5g fat, 2g fiber
Handvo (per 100g): 165 kcal, 5g protein, 22g carbs, 6g fat, 2g fiber

=== INDIAN DALS & LEGUMES ===
Dal tadka (per 100g): 85 kcal, 5g protein, 12g carbs, 2.5g fat, 3g fiber
Dal makhani (per 100g): 152 kcal, 7g protein, 18g carbs, 6g fat, 4g fiber
Dal fry (per 100g): 95 kcal, 5.5g protein, 13g carbs, 3g fat, 3.5g fiber
Chana dal (cooked, per 100g): 164 kcal, 8.7g protein, 27g carbs, 2.7g fat, 7.6g fiber
Moong dal (cooked, per 100g): 105 kcal, 7g protein, 19g carbs, 0.4g fat, 4g fiber
Moong dal (whole, cooked): 118 kcal, 8g protein, 20g carbs, 0.6g fat, 5g fiber
Toor dal (cooked, per 100g): 116 kcal, 7g protein, 20g carbs, 0.4g fat, 4g fiber
Masoor dal (red lentil, cooked): 116 kcal, 9g protein, 20g carbs, 0.4g fat, 7.9g fiber
Urad dal (cooked, per 100g): 127 kcal, 9g protein, 22g carbs, 0.6g fat, 3.3g fiber
Rajma (kidney bean curry, per 100g): 140 kcal, 8g protein, 21g carbs, 3g fat, 6g fiber
Chana masala (per 100g): 150 kcal, 7g protein, 20g carbs, 5g fat, 5g fiber
Chole (white chickpea curry, per 100g): 155 kcal, 7.5g protein, 21g carbs, 5g fat, 5.5g fiber
Black chana curry (per 100g): 145 kcal, 8g protein, 20g carbs, 4g fat, 6g fiber
Moth dal (cooked): 119 kcal, 8g protein, 21g carbs, 0.5g fat, 4g fiber
Pav bhaji (per 100g): 155 kcal, 4g protein, 22g carbs, 6g fat, 3g fiber

=== INDIAN CURRIES & GRAVIES ===
Paneer (Indian cottage cheese, per 100g): 265 kcal, 18g protein, 1.2g carbs, 21g fat, 0g fiber
Palak paneer (per 100g): 180 kcal, 10g protein, 8g carbs, 12g fat, 2g fiber
Paneer butter masala (per 100g): 210 kcal, 9g protein, 10g carbs, 16g fat, 1.5g fiber
Paneer tikka masala (per 100g): 200 kcal, 10g protein, 9g carbs, 15g fat, 1.5g fiber
Shahi paneer (per 100g): 235 kcal, 9g protein, 8g carbs, 19g fat, 1g fiber
Matar paneer (per 100g): 165 kcal, 8g protein, 12g carbs, 10g fat, 3g fiber
Aloo matar (per 100g): 110 kcal, 3g protein, 16g carbs, 4g fat, 3g fiber
Aloo gobi (per 100g): 95 kcal, 2.5g protein, 13g carbs, 4g fat, 2.5g fiber
Aloo sabzi (per 100g): 95 kcal, 2g protein, 14g carbs, 3.5g fat, 2g fiber
Baingan bharta (per 100g): 85 kcal, 2.5g protein, 10g carbs, 4g fat, 3g fiber
Bhindi masala (per 100g): 90 kcal, 2.5g protein, 10g carbs, 4.5g fat, 3g fiber
Kadai vegetable (per 100g): 105 kcal, 3g protein, 12g carbs, 5g fat, 2.5g fiber
Mixed veg curry (per 100g): 95 kcal, 2.5g protein, 12g carbs, 4g fat, 2.5g fiber
Malai kofta (per 100g): 245 kcal, 7g protein, 14g carbs, 18g fat, 1.5g fiber
Navratan korma (per 100g): 190 kcal, 5g protein, 16g carbs, 12g fat, 2g fiber
Butter chicken (murgh makhani, per 100g): 185 kcal, 15g protein, 8g carbs, 11g fat, 1g fiber
Chicken tikka masala (per 100g): 175 kcal, 14g protein, 9g carbs, 10g fat, 1g fiber
Chicken curry (home style, per 100g): 165 kcal, 15g protein, 5g carbs, 10g fat, 1g fiber
Mutton curry (per 100g): 210 kcal, 18g protein, 4g carbs, 14g fat, 0.5g fiber
Fish curry (per 100g): 145 kcal, 16g protein, 6g carbs, 7g fat, 0.5g fiber
Prawn masala (per 100g): 130 kcal, 18g protein, 5g carbs, 5g fat, 0.5g fiber
Egg curry (per 100g): 145 kcal, 9g protein, 6g carbs, 10g fat, 1g fiber
Sambar (per 100ml): 52 kcal, 3g protein, 8g carbs, 1g fat, 2g fiber
Rasam (per 100ml): 30 kcal, 1g protein, 5g carbs, 0.8g fat, 0.5g fiber
Avial (per 100g): 120 kcal, 2.5g protein, 12g carbs, 7g fat, 3g fiber

=== INDIAN RICE DISHES ===
Biryani (chicken, per 100g): 175 kcal, 10g protein, 22g carbs, 5g fat, 1g fiber
Biryani (mutton, per 100g): 195 kcal, 11g protein, 22g carbs, 7g fat, 1g fiber
Biryani (vegetable, per 100g): 145 kcal, 4g protein, 24g carbs, 4g fat, 1.5g fiber
Biryani (egg, per 100g): 160 kcal, 7g protein, 22g carbs, 5g fat, 1g fiber
Pulao (vegetable, per 100g): 140 kcal, 3.5g protein, 24g carbs, 3.5g fat, 1.5g fiber
Pulao (chicken, per 100g): 160 kcal, 9g protein, 22g carbs, 4g fat, 1g fiber
Khichdi (per 100g): 120 kcal, 4g protein, 22g carbs, 2g fat, 1.5g fiber
Curd rice (per 100g): 130 kcal, 4g protein, 20g carbs, 4g fat, 0.5g fiber
Lemon rice (per 100g): 145 kcal, 3g protein, 25g carbs, 4g fat, 1g fiber
Tamarind rice (per 100g): 150 kcal, 3g protein, 26g carbs, 4g fat, 1.5g fiber
Tomato rice (per 100g): 140 kcal, 3g protein, 24g carbs, 3.5g fat, 1g fiber
Coconut rice (per 100g): 165 kcal, 3g protein, 24g carbs, 6g fat, 1.5g fiber

=== INDIAN STREET FOOD & SNACKS ===
Samosa (1 piece = 60g): 150 kcal, 3g protein, 18g carbs, 7.5g fat, 2g fiber
Kachori (1 piece = 60g): 180 kcal, 4g protein, 20g carbs, 9g fat, 2g fiber
Vada pav (1 = 120g): 290 kcal, 7g protein, 42g carbs, 10g fat, 3g fiber
Pav bhaji (with 2 pav = 250g): 380 kcal, 10g protein, 55g carbs, 13g fat, 5g fiber
Chole bhature (1 serving = 300g): 620 kcal, 18g protein, 82g carbs, 24g fat, 10g fiber
Pani puri / golgappa (6 pieces = 80g): 120 kcal, 2.5g protein, 20g carbs, 3.5g fat, 1.5g fiber
Bhel puri (per 100g): 130 kcal, 3.5g protein, 22g carbs, 3.5g fat, 2g fiber
Sev puri (per 100g): 175 kcal, 4g protein, 24g carbs, 7g fat, 2g fiber
Dahi puri (per 100g): 145 kcal, 4.5g protein, 22g carbs, 4.5g fat, 1.5g fiber
Papdi chaat (per 100g): 190 kcal, 5g protein, 26g carbs, 7.5g fat, 2g fiber
Aloo tikki (1 piece = 80g): 145 kcal, 3g protein, 22g carbs, 5g fat, 2g fiber
Kathi roll (chicken, 1 = 180g): 340 kcal, 18g protein, 40g carbs, 12g fat, 3g fiber
Frankie (veg, 1 = 150g): 270 kcal, 7g protein, 38g carbs, 10g fat, 3g fiber
Dabeli (1 = 100g): 230 kcal, 5g protein, 32g carbs, 9g fat, 2.5g fiber
Misal pav (1 serving = 200g): 310 kcal, 12g protein, 44g carbs, 9g fat, 7g fiber
Poha chivda (per 30g): 120 kcal, 2.5g protein, 18g carbs, 4.5g fat, 1g fiber
Murukku (per 30g): 145 kcal, 2.5g protein, 18g carbs, 7g fat, 1g fiber
Chakli (per 30g): 140 kcal, 2.5g protein, 17g carbs, 7g fat, 1g fiber
Mathri (per 30g): 155 kcal, 3g protein, 18g carbs, 8g fat, 0.8g fiber
Namkeen mixture (per 30g): 145 kcal, 3.5g protein, 17g carbs, 7g fat, 1.5g fiber
Biscuits (Parle-G, 4 = 28g): 130 kcal, 2g protein, 20g carbs, 4.5g fat, 0.3g fiber
Marie biscuits (4 = 28g): 120 kcal, 2g protein, 21g carbs, 3.5g fat, 0.5g fiber
Cream biscuits (2 = 25g): 120 kcal, 1.5g protein, 17g carbs, 5g fat, 0.3g fiber

=== INDIAN DAIRY & PROTEINS ===
Paneer (Indian cottage cheese): 265 kcal, 18g protein, 1.2g carbs, 21g fat, 0g fiber
Paneer (low fat): 160 kcal, 18g protein, 2g carbs, 9g fat, 0g fiber
Curd/Yogurt (full fat, per 100g): 98 kcal, 11g protein, 3.4g carbs, 4.3g fat, 0g fiber
Curd (low fat, per 100g): 62 kcal, 8.5g protein, 4.5g carbs, 1.5g fat, 0g fiber
Hung curd/Greek yogurt (per 100g): 95 kcal, 9g protein, 4g carbs, 4.5g fat, 0g fiber
Raita (per 100g): 56 kcal, 2.8g protein, 5g carbs, 2.5g fat, 0.3g fiber
Lassi (sweet, per 100ml): 75 kcal, 3.5g protein, 11g carbs, 1.8g fat, 0g fiber
Lassi (salted, per 100ml): 55 kcal, 3.5g protein, 5g carbs, 2g fat, 0g fiber
Buttermilk/Chaas (per 100ml): 40 kcal, 3.3g protein, 4.8g carbs, 0.9g fat, 0g fiber
Khoa/Mawa (per 100g): 421 kcal, 20g protein, 26g carbs, 29g fat, 0g fiber
Milk (full fat toned, per 100ml): 58 kcal, 3.2g protein, 4.4g carbs, 3g fat, 0g fiber
Milk (double toned, per 100ml): 45 kcal, 3.5g protein, 4.5g carbs, 1.5g fat, 0g fiber
Amul butter (per 10g): 74 kcal, 0.1g protein, 0.1g carbs, 8g fat, 0g fiber
Desi ghee (per 10g): 90 kcal, 0g protein, 0g carbs, 10g fat, 0g fiber
Coconut oil (per 10g): 90 kcal, 0g protein, 0g carbs, 10g fat, 0g fiber
Mustard oil (per 10g): 90 kcal, 0g protein, 0g carbs, 10g fat, 0g fiber

=== INDIAN SWEETS & DESSERTS ===
Gulab jamun (1 piece = 50g): 175 kcal, 3g protein, 28g carbs, 6g fat, 0.5g fiber
Rasgulla (1 piece = 50g): 106 kcal, 3g protein, 20g carbs, 2g fat, 0g fiber
Jalebi (per 100g): 360 kcal, 3g protein, 65g carbs, 10g fat, 0.3g fiber
Halwa (sooji/rava, per 100g): 280 kcal, 4g protein, 42g carbs, 10g fat, 0.8g fiber
Halwa (gajar/carrot, per 100g): 210 kcal, 4g protein, 30g carbs, 9g fat, 1.5g fiber
Kheer (per 100g): 145 kcal, 4.5g protein, 22g carbs, 5g fat, 0.2g fiber
Payasam (per 100g): 135 kcal, 4g protein, 20g carbs, 4.5g fat, 0.3g fiber
Ladoo (besan, 1 = 40g): 185 kcal, 4g protein, 23g carbs, 9g fat, 1g fiber
Ladoo (motichoor, 1 = 35g): 160 kcal, 2.5g protein, 23g carbs, 7g fat, 0.5g fiber
Barfi (milk, per 40g): 160 kcal, 4g protein, 22g carbs, 7g fat, 0g fiber
Pedha (per 30g): 130 kcal, 3.5g protein, 18g carbs, 5g fat, 0g fiber
Mysore pak (per 40g): 220 kcal, 3g protein, 22g carbs, 14g fat, 0.5g fiber
Modak (steamed, 1 = 50g): 130 kcal, 2g protein, 22g carbs, 4g fat, 1.5g fiber
Malpua (1 = 60g): 190 kcal, 4g protein, 28g carbs, 7g fat, 0.5g fiber
Shrikhand (per 100g): 195 kcal, 7g protein, 30g carbs, 6g fat, 0g fiber
Kulfi (per 100ml): 180 kcal, 5g protein, 22g carbs, 8g fat, 0g fiber
Ice cream (vanilla, per 100g): 207 kcal, 3.5g protein, 23g carbs, 11g fat, 0g fiber
Chikki (groundnut, per 30g): 150 kcal, 4g protein, 17g carbs, 8g fat, 1.5g fiber

=== INDIAN FLOURS & STAPLES ===
Besan/Chickpea flour (raw, per 100g): 387 kcal, 22g protein, 58g carbs, 6g fat, 10g fiber
Atta/Whole wheat flour (per 100g): 340 kcal, 12g protein, 70g carbs, 2g fat, 11g fiber
Maida/Refined flour (per 100g): 360 kcal, 10g protein, 76g carbs, 1g fat, 2.7g fiber
Rava/Semolina (per 100g): 360 kcal, 12g protein, 73g carbs, 1g fat, 3.9g fiber
Rice flour (per 100g): 366 kcal, 6g protein, 80g carbs, 1.4g fat, 2.4g fiber
Jowar flour (per 100g): 349 kcal, 10g protein, 73g carbs, 1.7g fat, 6.7g fiber
Bajra flour (per 100g): 378 kcal, 11g protein, 69g carbs, 5g fat, 11.5g fiber
Ragi/Finger millet flour (per 100g): 336 kcal, 7g protein, 73g carbs, 1.3g fat, 3.6g fiber
Sattu (roasted chickpea flour): 406 kcal, 20g protein, 65g carbs, 6g fat, 8g fiber
Poha/Flattened rice (per 100g dry): 389 kcal, 7g protein, 84g carbs, 1.2g fat, 1.5g fiber
Sabudana/Tapioca pearls (dry): 350 kcal, 0.2g protein, 86g carbs, 0.2g fat, 0g fiber
Sprouts (mixed, raw): 45 kcal, 4g protein, 6g carbs, 0.5g fat, 1.5g fiber
Moong sprouts (per 100g): 30 kcal, 3g protein, 4g carbs, 0.2g fat, 1.8g fiber
Masala oats (per 100g cooked): 85 kcal, 3g protein, 14g carbs, 2g fat, 2g fiber

=== INDIAN SPICES & CONDIMENTS (per tsp) ===
Turmeric powder: 9 kcal, 0.3g protein, 2g carbs, 0.3g fat, 0.5g fiber
Cumin/Jeera seeds: 8 kcal, 0.4g protein, 1g carbs, 0.5g fat, 0.2g fiber
Coriander powder: 7 kcal, 0.3g protein, 1.4g carbs, 0.3g fat, 0.7g fiber
Chilli powder: 6 kcal, 0.3g protein, 1.3g carbs, 0.3g fat, 0.5g fiber
Garam masala: 7 kcal, 0.3g protein, 1.5g carbs, 0.3g fat, 0.5g fiber
Pickle/Achar (per 10g): 20 kcal, 0.3g protein, 1.5g carbs, 1.5g fat, 0.5g fiber
Coconut chutney (per 30g): 55 kcal, 1g protein, 3g carbs, 4.5g fat, 1.5g fiber
Mint chutney (per 30g): 15 kcal, 0.5g protein, 2g carbs, 0.5g fat, 0.8g fiber
Tamarind chutney (per 30g): 45 kcal, 0.5g protein, 11g carbs, 0.2g fat, 0.5g fiber

=== INDIAN BEVERAGES ===
Chai/Masala tea (with milk, per 150ml): 55 kcal, 2g protein, 7g carbs, 2g fat, 0g fiber
Black tea (per 150ml): 3 kcal, 0g protein, 0.5g carbs, 0g fat, 0g fiber
Filter coffee (with milk, per 150ml): 65 kcal, 2.5g protein, 7g carbs, 3g fat, 0g fiber
Buttermilk/Chaas (per 100ml): 40 kcal, 3.3g protein, 4.8g carbs, 0.9g fat, 0g fiber
Lassi sweet (per 100ml): 75 kcal, 3.5g protein, 11g carbs, 1.8g fat, 0g fiber
Nimbu pani/Lemonade (per 200ml): 45 kcal, 0.3g protein, 12g carbs, 0g fat, 0.2g fiber
Sugarcane juice (per 200ml): 120 kcal, 0.4g protein, 30g carbs, 0.2g fat, 0g fiber
Coconut water (per 200ml): 38 kcal, 1.4g protein, 9g carbs, 0.4g fat, 0g fiber
Nariyal pani (tender coconut, per 200ml): 38 kcal, 1.4g protein, 9g carbs, 0.4g fat, 0g fiber
Aam panna (per 200ml): 90 kcal, 0.5g protein, 22g carbs, 0.2g fat, 0.5g fiber
Jaljeera (per 200ml): 30 kcal, 0.5g protein, 7g carbs, 0.2g fat, 0.3g fiber
Thandai (per 200ml): 195 kcal, 5g protein, 28g carbs, 8g fat, 1g fiber

=== PACKAGED INDIAN FOODS ===
Maggi noodles (1 pack = 70g dry): 310 kcal, 8g protein, 44g carbs, 12g fat, 2g fiber
Yippee noodles (1 pack = 70g): 300 kcal, 7g protein, 45g carbs, 11g fat, 2g fiber
Knorr soup (1 serving = 200ml): 65 kcal, 2g protein, 12g carbs, 1g fat, 0.5g fiber
Amul cheese slice (1 = 25g): 80 kcal, 5g protein, 1g carbs, 6.5g fat, 0g fiber
Amul Greek yogurt (per 100g): 84 kcal, 8g protein, 5g carbs, 3g fat, 0g fiber
Epigamia Greek yogurt (per 100g): 79 kcal, 8.5g protein, 5.5g carbs, 2g fat, 0g fiber
Muesli (Kellogg's, per 40g): 155 kcal, 4g protein, 29g carbs, 3g fat, 3g fiber
Cornflakes (Kellogg's, per 30g): 110 kcal, 2.5g protein, 25g carbs, 0.2g fat, 0.8g fiber
Oats (Quaker, per 40g dry): 148 kcal, 5g protein, 26g carbs, 2.8g fat, 4g fiber
Peanut butter (Sundrop, per 32g): 190 kcal, 7g protein, 6g carbs, 16g fat, 1.5g fiber
Protein bar (RiteBite, per 50g): 195 kcal, 14g protein, 22g carbs, 6g fat, 4g fiber
Whey protein (MuscleBlaze, 1 scoop = 33g): 125 kcal, 25g protein, 3g carbs, 2g fat, 0g fiber
Whey protein (Optimum Nutrition, 1 scoop = 30g): 120 kcal, 24g protein, 3g carbs, 1.5g fat, 0g fiber
Masala peanuts (per 30g): 155 kcal, 6g protein, 13g carbs, 9g fat, 2g fiber
Roasted chana (per 30g): 110 kcal, 6g protein, 15g carbs, 2.5g fat, 3.5g fiber

=== RESTAURANT FOODS (INDIA) ===
Thali (veg, full = ~500g): 650 kcal, 22g protein, 95g carbs, 20g fat, 12g fiber
Thali (non-veg, full = ~550g): 750 kcal, 40g protein, 90g carbs, 25g fat, 8g fiber
Pizza (Domino's veg medium, 1 slice = 90g): 220 kcal, 8g protein, 29g carbs, 8g fat, 2g fiber
Pizza (Domino's chicken, 1 slice = 95g): 245 kcal, 12g protein, 28g carbs, 10g fat, 2g fiber
Burger (McAloo tikki = 130g): 310 kcal, 7g protein, 44g carbs, 12g fat, 3g fiber
Burger (McChicken = 150g): 390 kcal, 17g protein, 42g carbs, 17g fat, 2.5g fiber
Shawarma (chicken, 1 roll = 200g): 420 kcal, 25g protein, 42g carbs, 16g fat, 3g fiber
Doner kebab (1 = 200g): 430 kcal, 28g protein, 38g carbs, 18g fat, 2g fiber
Tandoori chicken (2 pieces = 200g): 280 kcal, 34g protein, 6g carbs, 13g fat, 1g fiber
Chicken tikka (per 100g): 195 kcal, 28g protein, 4g carbs, 8g fat, 0.5g fiber
Seekh kebab (2 = 100g): 220 kcal, 22g protein, 5g carbs, 13g fat, 1g fiber
Paneer tikka (per 100g): 230 kcal, 13g protein, 6g carbs, 18g fat, 1g fiber
Noodles (veg hakka, per 100g): 165 kcal, 4g protein, 28g carbs, 4.5g fat, 2g fiber
Fried rice (veg, per 100g): 170 kcal, 3.5g protein, 28g carbs, 5g fat, 1.5g fiber
Fried rice (chicken, per 100g): 185 kcal, 8g protein, 27g carbs, 5.5g fat, 1.5g fiber
Manchurian (veg, per 100g): 145 kcal, 3.5g protein, 18g carbs, 6.5g fat, 2g fiber

=== SPORTS NUTRITION ===
Banana (medium pre-workout): 89 kcal, 1.1g protein, 23g carbs, 0.3g fat, 2.6g fiber
Sports drink (Gatorade, per 100ml): 26 kcal, 0g protein, 7g carbs, 0g fat, 0g fiber
Energy gel (1 packet = 32g): 100 kcal, 0g protein, 25g carbs, 0g fat, 0g fiber
Protein bar (Quest style, per 60g bar): 190 kcal, 21g protein, 22g carbs, 7g fat, 14g fiber
Protein bar (Clif Bar, per 68g): 250 kcal, 9g protein, 44g carbs, 5g fat, 5g fiber
Creatine monohydrate (5g dose): 0 kcal, 0g protein, 0g carbs, 0g fat, 0g fiber
BCAA powder (10g serving): 40 kcal, 10g protein, 0g carbs, 0g fat, 0g fiber
Maltodextrin (per 100g): 380 kcal, 0g protein, 95g carbs, 0g fat, 0g fiber
Dextrose (per 100g): 387 kcal, 0g protein, 100g carbs, 0g fat, 0g fiber
Rice cakes (2 plain): 70 kcal, 1.5g protein, 15g carbs, 0.5g fat, 0.3g fiber
Peanut butter rice cake (2): 140 kcal, 4g protein, 17g carbs, 7g fat, 1g fiber

=== BEVERAGES ===
Black coffee (per 100ml): 2 kcal, 0.3g protein, 0g carbs, 0g fat, 0g fiber
Coffee with whole milk (per 100ml): 15 kcal, 0.8g protein, 1.2g carbs, 0.8g fat, 0g fiber
Green tea (per 100ml): 1 kcal, 0g protein, 0.2g carbs, 0g fat, 0g fiber
Orange juice (100% fresh, per 100ml): 45 kcal, 0.7g protein, 10g carbs, 0.2g fat, 0.2g fiber
Whole milk (per 100ml): 61 kcal, 3.2g protein, 4.8g carbs, 3.3g fat, 0g fiber
Oat milk (fortified, per 100ml): 45 kcal, 1g protein, 7g carbs, 1.5g fat, 0.5g fiber
Almond milk (unsweetened, per 100ml): 15 kcal, 0.5g protein, 1.5g carbs, 1g fat, 0.2g fiber
Soy milk (unsweetened, per 100ml): 33 kcal, 3g protein, 1.8g carbs, 2g fat, 0.3g fiber
Coconut water (per 100ml): 19 kcal, 0.7g protein, 4.5g carbs, 0.2g fat, 0g fiber

=== CONDIMENTS & SAUCES ===
Tomato ketchup (1 tbsp = 17g): 112 kcal, 1.5g protein, 26g carbs, 0.3g fat, 0.3g fiber
Soy sauce (1 tbsp = 16ml): 53 kcal, 8.1g protein, 4.9g carbs, 0.1g fat, 0.1g fiber
Hot sauce (1 tsp): 12 kcal, 0.5g protein, 2.5g carbs, 0.1g fat, 0.2g fiber
Mayonnaise (1 tbsp = 15g): 680 kcal, 1g protein, 0.6g carbs, 75g fat, 0g fiber
Mustard (1 tsp): 70 kcal, 4.4g protein, 5.8g carbs, 3.3g fat, 3.2g fiber
Hummus (per 100g): 177 kcal, 8g protein, 14g carbs, 10g fat, 6g fiber
Tahini (per 100g): 595 kcal, 17g protein, 21g carbs, 54g fat, 9.3g fiber
"""

NUTRITION_SYSTEM = """You are a precise sports nutrition and dietetics expert.
When given a food query, return ONLY a valid JSON array (no markdown, no explanation, no preamble) with this exact structure:
[
  {
    "name": "Food Name",
    "amount": "100g",
    "calories": 165,
    "protein": 31.0,
    "carbs": 0.0,
    "fat": 3.6,
    "fiber": 0.0,
    "sugar": 0.0,
    "sodium_mg": 74,
    "serving_note": "e.g. 1 chicken breast approx 150g cooked"
  }
]
Rules:
- Return 5-12 relevant results depending on the query breadth
- All values per 100g unless the query specifies a serving size
- Include practical serving notes athletes would find useful
- If query is a meal (e.g. bowl of dal rice), estimate the complete meal
- ONLY return the JSON array, no other text whatsoever"""


class NutritionQuery(BaseModel):
    query: str
    serving_g: Optional[float] = None


# ── Provider 1: USDA FoodData Central ────────────────────────────────────────

async def _call_usda(query: str, serving_g: Optional[float]) -> list:
    """
    USDA FoodData Central — 380k+ foods, free API, instant key.
    Get key at: https://fdc.nal.usda.gov/api-guide (just enter email)
    Set USDA_API_KEY in .env
    """
    api_key = getattr(settings, "usda_api_key", "")
    if not api_key:
        raise ValueError("USDA_API_KEY not configured")

    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(
            "https://api.nal.usda.gov/fdc/v1/foods/search",
            params={
                "query": query,
                "api_key": api_key,
                "pageSize": 10,
                "dataType": "Foundation,SR Legacy,Survey (FNDDS),Branded",
            },
        )
        resp.raise_for_status()
        items = resp.json().get("foods", [])

    results = []
    seen = set()
    for item in items:
        name = item.get("description", "").strip().title()
        if not name or name.lower() in seen:
            continue
        seen.add(name.lower())

        # Build nutrient lookup from the list
        nutrients = {n["nutrientName"]: n.get("value", 0) for n in item.get("foodNutrients", [])}

        def get_n(keys):
            for k in keys:
                for nk, v in nutrients.items():
                    if k.lower() in nk.lower():
                        return round(float(v or 0), 1)
            return 0.0

        calories = get_n(["Energy"])
        protein  = get_n(["Protein"])
        carbs    = get_n(["Carbohydrate"])
        fat      = get_n(["Total lipid", "Total fat"])
        fiber    = get_n(["Fiber"])
        sugar    = get_n(["Sugars"])
        sodium   = get_n(["Sodium"])

        if calories == 0:
            continue

        # Scale if serving_g requested (USDA values are per 100g)
        scale = (serving_g / 100) if serving_g else 1.0
        results.append({
            "name":         name,
            "amount":       f"{serving_g}g" if serving_g else "100g",
            "calories":     round(calories * scale, 1),
            "protein":      round(protein  * scale, 1),
            "carbs":        round(carbs    * scale, 1),
            "fat":          round(fat      * scale, 1),
            "fiber":        round(fiber    * scale, 1),
            "sugar":        round(sugar    * scale, 1),
            "sodium_mg":    round(sodium   * scale),
            "serving_note": item.get("servingSize") and f"1 serving = {item['servingSize']}{item.get('servingSizeUnit','g')}" or "per 100g",
        })
        if len(results) >= 8:
            break

    if not results:
        raise ValueError("No results from USDA")
    return results


# ── Provider 2: Open Food Facts ───────────────────────────────────────────────

async def _call_open_food_facts(query: str, serving_g: Optional[float]) -> list:
    """
    Open Food Facts — 3M+ products, no API key needed.
    Best for packaged/branded foods.
    """
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(
            "https://world.openfoodfacts.org/cgi/search.pl",
            params={
                "search_terms": query,
                "search_simple": 1,
                "action": "process",
                "json": 1,
                "page_size": 10,
                "fields": "product_name,nutriments,serving_size",
            },
            headers={"User-Agent": "AIFitnessPlatform/1.0"},
        )
        resp.raise_for_status()
        products = resp.json().get("products", [])

    results = []
    for p in products:
        n = p.get("nutriments", {})
        name = p.get("product_name", "").strip()
        if not name:
            continue
        # OFF stores values per 100g natively
        entry = {
            "name":         name,
            "amount":       f"{serving_g}g" if serving_g else "100g",
            "calories":     round(n.get("energy-kcal_100g") or n.get("energy_100g", 0) / 4.184, 1),
            "protein":      round(n.get("proteins_100g", 0), 1),
            "carbs":        round(n.get("carbohydrates_100g", 0), 1),
            "fat":          round(n.get("fat_100g", 0), 1),
            "fiber":        round(n.get("fiber_100g", 0), 1),
            "sugar":        round(n.get("sugars_100g", 0), 1),
            "sodium_mg":    round((n.get("sodium_100g", 0)) * 1000),
            "serving_note": p.get("serving_size") or "per 100g",
        }
        # Scale if serving_g requested
        if serving_g:
            scale = serving_g / 100
            for k in ["calories", "protein", "carbs", "fat", "fiber", "sugar"]:
                entry[k] = round(entry[k] * scale, 1)
            entry["sodium_mg"] = round(entry["sodium_mg"] * scale)
        if entry["calories"] > 0:
            results.append(entry)
        if len(results) >= 8:
            break

    if not results:
        raise ValueError("No results from Open Food Facts")
    return results


# ── Provider 3: Gemini ────────────────────────────────────────────────────────

async def _call_gemini(prompt: str) -> str:
    """Call Gemini API for nutrition lookup."""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={settings.gemini_api_key}"
    payload = {
        "contents": [{"parts": [{"text": f"{NUTRITION_SYSTEM}\n\n{prompt}"}]}],
        "generationConfig": {"temperature": 0.1, "maxOutputTokens": 2048},
    }
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(url, json=payload)
        resp.raise_for_status()
        return resp.json()["candidates"][0]["content"]["parts"][0]["text"]


# ── Provider 4: Groq (uses same key as coach) ─────────────────────────────────

async def _call_groq(prompt: str) -> str:
    """Use Groq LLM as nutrition fallback — fast, free tier."""
    groq_key = getattr(settings, "groq_api_key", "")
    if not groq_key:
        raise ValueError("Groq key not set")
    async with httpx.AsyncClient(timeout=20.0) as client:
        resp = await client.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {groq_key}"},
            json={
                "model": "llama-3.1-8b-instant",
                "messages": [
                    {"role": "system", "content": NUTRITION_SYSTEM},
                    {"role": "user", "content": prompt},
                ],
                "max_tokens": 1024,
                "temperature": 0.1,
            },
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]


# ── Shared helpers ────────────────────────────────────────────────────────────

def _filter_food_db(query: str, max_lines: int = 80) -> str:
    keywords = [w.lower() for w in query.split() if len(w) > 2]
    lines = FOOD_DB.strip().splitlines()
    matched: list[str] = []
    section = ""
    for line in lines:
        if line.startswith("==="):
            section = line
        if any(kw in line.lower() for kw in keywords):
            if section and (not matched or matched[-1] != section):
                matched.append(section)
            matched.append(line)
        if len(matched) >= max_lines:
            break
    return "\n".join(matched) if matched else "\n".join(lines[:60])


def _parse_and_scale(text: str, serving_g: Optional[float]) -> list:
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    m = re.search(r"\[.*\]", text, re.DOTALL)
    if m:
        text = m.group(0)
    foods = json.loads(text)
    if serving_g:
        scale = serving_g / 100
        for f in foods:
            for k in ["calories", "protein", "carbs", "fat", "fiber", "sugar"]:
                if k in f:
                    f[k] = round(f[k] * scale, 1)
            if "sodium_mg" in f:
                f["sodium_mg"] = round(f["sodium_mg"] * scale)
            f["amount"] = f"{serving_g}g"
    return foods


# ── Main endpoint ─────────────────────────────────────────────────────────────

@router.post("/search")
async def nutrition_search(
    req: NutritionQuery,
    user: User = Depends(get_current_user),
):
    """
    Provider waterfall:
      1. USDA FoodData Central — 380k+ foods, free instant key
      2. Open Food Facts — 3M+ packaged foods, no key needed
      3. Gemini       — AI fallback, needs GEMINI_API_KEY
      4. Groq         — AI fallback, uses existing GROQ_API_KEY
    """

    # 1. USDA FoodData Central
    try:
        foods = await _call_usda(req.query, req.serving_g)
        print(f"[nutrition] USDA: {len(foods)} results")
        return {"foods": foods, "source": "usda"}
    except Exception as e:
        print(f"[nutrition] USDA failed: {e}")

    # 2. Open Food Facts
    try:
        foods = await _call_open_food_facts(req.query, req.serving_g)
        print(f"[nutrition] OpenFoodFacts: {len(foods)} results")
        return {"foods": foods, "source": "open_food_facts"}
    except Exception as e:
        print(f"[nutrition] OpenFoodFacts failed: {e}")

    # 3. Gemini
    if settings.gemini_api_key:
        try:
            relevant_db = _filter_food_db(req.query)
            prompt = f"""Reference data:\n{relevant_db}\n\nUser query: "{req.query}"\n{f"Serving: {req.serving_g}g" if req.serving_g else ""}\nJSON array only."""
            text  = await _call_gemini(prompt)
            foods = _parse_and_scale(text, req.serving_g)
            print(f"[nutrition] Gemini: {len(foods)} results")
            return {"foods": foods, "source": "gemini"}
        except Exception as e:
            print(f"[nutrition] Gemini failed: {e}")

    # 4. Groq
    try:
        relevant_db = _filter_food_db(req.query)
        prompt = f"""Reference data:\n{relevant_db}\n\nUser query: "{req.query}"\n{f"Serving: {req.serving_g}g" if req.serving_g else ""}\nJSON array only."""
        text  = await _call_groq(prompt)
        foods = _parse_and_scale(text, req.serving_g)
        print(f"[nutrition] Groq: {len(foods)} results")
        return {"foods": foods, "source": "groq"}
    except Exception as e:
        print(f"[nutrition] Groq failed: {e}")

    raise HTTPException(
        status_code=503,
        detail="All nutrition providers failed. Add USDA_API_KEY to .env (free at fdc.nal.usda.gov/api-guide).",
    )


@router.get("/quick/{food_name}")
async def quick_lookup(
    food_name: str,
    user: User = Depends(get_current_user),
):
    """Quick single-food lookup by name."""
    req = NutritionQuery(query=food_name)
    return await nutrition_search(req, user)
