import tempfile
import streamlit as st
import os
import sys
from PIL import Image
from tzlocal import get_localzone
import pandas as pd

current_directory = os.path.dirname(os.path.abspath(__file__))

backend_directory = os.path.join(os.path.dirname(current_directory), "Backend")

sys.path.append(backend_directory)

from API import backend_call, get_history

st.title("AI Calories Tracker")
tab1, tab2 = st.tabs(["Analyze Meal Nutrition", "Nutritional Data History"])
with tab1:
    st.markdown(
        """ 
        Please capture the photo of your meal:
        """
    )
    camera_image = st.camera_input("Take picture")
    upload_image = st.file_uploader("Choose Photo to Upload", type=["jpg", "png", "jpeg"])
    food_image = camera_image or upload_image
    if food_image is not None:
        image = Image.open(food_image)
        st.image(image, caption="Image Provided", width="stretch")
        if st.button("Analyze Nutritional Information", type = "primary"):
            with tempfile.NamedTemporaryFile(delete = False, suffix = ".jpg") as temp:
                temp.write(food_image.getvalue())
                temp_path = temp.name
            
            with st.spinner("Analyzing ingredients..."):
                result = backend_call(temp_path)
            
            if result:
                st.success("Analysis done!")
                data1, data2, data3, data4 = st.columns(4)
                data1.metric("Calories", f"{result.calories} kcal")
                data2.metric("Carbs", f"{result.carbs} g")
                data3.metric("Protein", f"{result.protein} g")
                data4.metric("Fat", f"{result.fat} g")
            else:
                st.error("Problem analyzing the provided image")

with tab2:
    st.subheader("Meal History")
    history = get_history()
    if history:
        df = pd.DataFrame(history)
        df = df[["created_at", "total_calories", "total_carbs", "total_protein", "total_fat"]]
        df["created_at"] = pd.to_datetime(df["created_at"], utc = True).dt.tz_convert(get_localzone()).dt.strftime("%b %d, %Y %I:%M %p")
        df.columns = ["Date", "Calories (kcal)", "Carbs (g)", "Protein (g)", "Fat (g)"]
        st.dataframe(df)
    else:
        st.info("No meals analyzed, start off by taking photos or uploading meals in the Analyze Meal Nutrition tab")
                