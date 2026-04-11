import os
import yaml
from PIL import Image
from google import genai
from google.genai import types
from wrapper import NutritionWrapper
from pydantic import BaseModel, Field
from supabase import create_client

script_path = os.path.dirname(os.path.abspath(__file__))
config_path = os.path.join(script_path, "config.yaml")
image_path = os.path.join(script_path, "test_food.jpeg")

with open(config_path, "r") as file:
    config = yaml.safe_load(file)

gemini_key = config['keys']['gemini']
calories_ninjas_key = config['keys']['calories_ninjas']
supabase_url = config['keys']['supabase_url']
supabase_key = config['keys']['supabase_key']

supabase = create_client(supabase_url, supabase_key)

class FoodMacros(BaseModel):
    name: str = Field(description="Name of the food")
    calories: int = Field(description="Calories of the food")
    carbs: int = Field(description="Carbs of the food")
    protein: int = Field(description="Protein of the food")
    fat: int = Field(description="Fat of the food")

def food_analyzer(image_path: str):
    client = genai.Client(api_key=gemini_key)
    image = Image.open(image_path)
    prompt = """You are a professional food nutrition analyst.
    By using the image provided, identify the food and it's estimated portion size.
    Return only with a descriptive string with simple, comma-separated list of ingredients.
    Rules you must follow:
    1. Use only integer and API friendly units (examples include oz, tbsp, slice, piece)
    2. Do not use fractions or decimals (use 8 oz instead of 1/2 lb)
    3. Do not use ranges (use '1' instead of '1-2')
    4. Do not use slashes (use 'ketchup' instead of 'ketchup/sauce')
    Output example: '1 bun, 8 oz beef patty, 1 slice cheese, 2 tbspn ketchup, 3 slices pickle, 1 leaf lettuce'.
    """
    print(f"Sending {image_path} to LLM for analysis")

    try:
        response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=[image, prompt],
        config=types.GenerateContentConfig(
            temperature=0.0,
        )
        )

        return response.text.strip()
    
    except Exception as e:
        print(f"LLM error {e}")
        return None

if __name__ == "__main__":
    result = food_analyzer(image_path)
    
    if result:
        print(f"LLM identified the ingredients as: {result}")

        wrapper = NutritionWrapper(calories_ninjas_key)
        nutrition_data = wrapper.nutrition_analysis(result)

        if nutrition_data and 'items' in nutrition_data and len(nutrition_data['items']) > 0:
            cals_sum = sum(item['calories'] for item in nutrition_data['items'])
            carbs_sum = sum(item['carbohydrates_total_g'] for item in nutrition_data['items'])
            protein_sum = sum(item['protein_g'] for item in nutrition_data['items'])
            fat_sum = sum(item['fat_total_g'] for item in nutrition_data['items'])

            final_result = FoodMacros(
            name = result,
            calories = int(cals_sum),
            carbs = int(carbs_sum),
            protein = int(protein_sum),
            fat = int(fat_sum)
            )

            print("--- AI Analysis Complete ---")
            print(f"Ingredient Identified: {final_result.name}")
            print(f"Calories: {final_result.calories} kcal")
            print(f"Carbs: {final_result.carbs}g")
            print(f"Protein: {final_result.protein}g")
            print(f"Fat: {final_result.fat}g")

            supabase.table("meals").insert({
                "image_url": image_path,
                "status": "analyzed",
                "total_calories": final_result.calories,
                "total_carbs": final_result.carbs,
                "total_protein": final_result.protein,
                "total_fat": final_result.fat
            }).execute()
            print("Saved to Supabase database.")
    else:
        print("Could not find nutrition data for food image")