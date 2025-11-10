import streamlit as st
import pandas as pd
from Generate_Recommendations import Generator
from random import uniform as rnd
from ImageFinder.ImageFinder import get_images_links as find_image
from streamlit_echarts import st_echarts

# ------------------ Page Setup ------------------ #
st.set_page_config(page_title="Generate Diet Recommendations", page_icon="💪", layout="wide")

# ------------------ Welcome Message ------------------ #
st.markdown("<h1 style='text-align:center; color:#1E90FF;'>Hello, Welcome to Diet Recommendation</h1>", unsafe_allow_html=True)

# ------------------ Nutrition Values ------------------ #
nutritions_values = [
    'Calories','FatContent','SaturatedFatContent','CholesterolContent',
    'SodiumContent','CarbohydrateContent','FiberContent','SugarContent','ProteinContent'
]

# ------------------ Streamlit State Initialization ------------------ #
if 'person' not in st.session_state:
    st.session_state.generated = False
    st.session_state.recommendations = None
    st.session_state.person = None
    st.session_state.weight_loss_option = None

# ------------------ Person Class ------------------ #
class Person:
    def __init__(self, age, height, weight, gender, activity, meals_calories_perc, weight_loss):
        self.age = age
        self.height = height
        self.weight = weight
        self.gender = gender
        self.activity = activity
        self.meals_calories_perc = meals_calories_perc
        self.weight_loss = weight_loss

    def calculate_bmi(self):
        bmi = round(self.weight / ((self.height / 100) ** 2), 2)
        return bmi

    def display_result(self):
        bmi = self.calculate_bmi()
        bmi_string = f'{bmi} kg/m²'
        if bmi < 18.5:
            category = 'Underweight'
            color = 'Red'
        elif 18.5 <= bmi < 25:
            category = 'Normal'
            color = 'Blue'
        elif 25 <= bmi < 30:
            category = 'Overweight'
            color = 'Orange'
        else:
            category = 'Obesity'    
            color = 'Red'
        return bmi_string, category, color

    def calculate_bmr(self):
        if self.gender == 'Male':
            bmr = 10*self.weight + 6.25*self.height - 5*self.age + 5
        else:
            bmr = 10*self.weight + 6.25*self.height - 5*self.age - 161
        return bmr

    def calories_calculator(self):
        activities = ['Little/no exercise', 'Light exercise', 'Moderate exercise (3-5 days/wk)',
                      'Very active (6-7 days/wk)', 'Extra active (very active & physical job)']
        weights = [1.2, 1.375, 1.55, 1.725, 1.9]
        activity_factor = weights[activities.index(self.activity)]
        maintain_calories = self.calculate_bmr() * activity_factor
        return maintain_calories

    def generate_recommendations(self):
        total_calories = self.weight_loss * self.calories_calculator()
        recommendations = []
        for meal in self.meals_calories_perc:
            meal_calories = self.meals_calories_perc[meal] * total_calories
            # Generate random nutrition values
            if meal == 'breakfast':
                recommended_nutrition = [meal_calories, rnd(10,30), rnd(0,4), rnd(0,30), rnd(0,400), rnd(40,75), rnd(4,10), rnd(0,10), rnd(30,100)]
            elif meal == 'lunch':
                recommended_nutrition = [meal_calories, rnd(20,40), rnd(0,4), rnd(0,30), rnd(0,400), rnd(40,75), rnd(4,20), rnd(0,10), rnd(50,175)]
            elif meal == 'dinner':
                recommended_nutrition = [meal_calories, rnd(20,40), rnd(0,4), rnd(0,30), rnd(0,400), rnd(40,75), rnd(4,20), rnd(0,10), rnd(50,175)]
            else:
                recommended_nutrition = [meal_calories, rnd(10,30), rnd(0,4), rnd(0,30), rnd(0,400), rnd(40,75), rnd(4,10), rnd(0,10), rnd(30,100)]
            generator = Generator(recommended_nutrition)
            recommended_recipes = generator.generate().json()['output']
            recommendations.append(recommended_recipes)
        for recommendation in recommendations:
            for recipe in recommendation:
                recipe['image_link'] = find_image(recipe['Name'])
        return recommendations

# ------------------ Display Class ------------------ #
class Display:
    def __init__(self):
        self.plans = ["Maintain weight", "Mild weight loss", "Weight loss", "Extreme weight loss"]
        self.weights = [1, 0.9, 0.8, 0.6]
        self.losses = ['-0 kg/week','-0.25 kg/week','-0.5 kg/week','-1 kg/week']

    def display_bmi(self, person):
        st.header('BMI CALCULATOR')
        bmi_string, category, color = person.display_result()
        st.metric(label="Body Mass Index (BMI)", value=bmi_string)
        st.markdown(f"<p style='color:{color}; font-size:25px;'>{category}</p>", unsafe_allow_html=True)
        st.markdown("Healthy BMI range: 18.5 kg/m² - 25 kg/m².")

    def display_calories(self, person):
        st.header('CALORIES CALCULATOR')        
        maintain_calories = person.calories_calculator()
        st.write('Estimated daily calorie intake for different weight plans:')
        for plan, weight, loss, col in zip(self.plans, self.weights, self.losses, st.columns(4)):
            with col:
                st.metric(label=plan, value=f'{round(maintain_calories*weight)} Calories/day', delta=loss, delta_color="inverse")

    def display_recommendation(self, person, recommendations):
        st.header('DIET RECOMMENDATIONS')  
        meals = person.meals_calories_perc
        for meal_name, column, recommendation in zip(meals, st.columns(len(meals)), recommendations):
            with column:
                st.markdown(f'##### {meal_name.upper()}')    
                for recipe in recommendation:
                    recipe_name = recipe['Name']
                    expander = st.expander(recipe_name)
                    recipe_img = f'<div><center><img src="{recipe["image_link"]}" alt="{recipe_name}"></center></div>'
                    expander.markdown(recipe_img, unsafe_allow_html=True)
                    nutritions_df = pd.DataFrame({value:[recipe[value]] for value in nutritions_values})
                    expander.markdown('<h5 style="text-align:center;">Nutritional Values (g):</h5>', unsafe_allow_html=True)
                    expander.dataframe(nutritions_df)
                    expander.markdown('<h5 style="text-align:center;">Ingredients:</h5>', unsafe_allow_html=True)
                    for ingredient in recipe['RecipeIngredientParts']:
                        expander.markdown(f"- {ingredient}")
                    expander.markdown('<h5 style="text-align:center;">Instructions:</h5>', unsafe_allow_html=True)
                    for instruction in recipe['RecipeInstructions']:
                        expander.markdown(f"- {instruction}")
                    expander.markdown(f"""
                        - Cook Time       : {recipe['CookTime']} min
                        - Preparation Time: {recipe['PrepTime']} min
                        - Total Time      : {recipe['TotalTime']} min
                    """)

    def display_meal_choices(self, person, recommendations):
        st.subheader('Choose your meal composition:')
        total_nutrition_values = {n: 0 for n in nutritions_values}
        choices = []
        # Meal choice selection
        columns = st.columns(len(recommendations))
        for i, rec in enumerate(recommendations):
            with columns[i]:
                choice = st.selectbox(f"Choose meal {i+1}:", [r['Name'] for r in rec])
                choices.append(choice)
        # Calculate total nutrition
        for choice, meals_ in zip(choices, recommendations):
            for meal in meals_:
                if meal['Name'] == choice:
                    for n in nutritions_values:
                        total_nutrition_values[n] += meal[n]
        # Display graphs
        st.markdown('<h5 style="text-align:center;">Nutritional Values:</h5>', unsafe_allow_html=True)
        nutritions_graph_options = {
            "tooltip": {"trigger": "item"},
            "legend": {"top": "5%", "left": "center"},
            "series": [{
                "name": "Nutritional Values",
                "type": "pie",
                "radius": ["40%", "70%"],
                "data": [{"value": round(total_nutrition_values[n]), "name": n} for n in total_nutrition_values]
            }]
        }
        st_echarts(options=nutritions_graph_options, height="500px")

# ------------------ Main Page ------------------ #
display = Display()

st.markdown("<h2 style='text-align:center;'>Fill your details below:</h2>", unsafe_allow_html=True)

with st.form("recommendation_form"):
    age = st.number_input('Age', min_value=2, max_value=120, step=1)
    height = st.number_input('Height (cm)', min_value=50, max_value=300, step=1)
    weight = st.number_input('Weight (kg)', min_value=10, max_value=300, step=1)
    gender = st.radio('Gender', ('Male','Female'))
    activity = st.select_slider('Activity', options=[
        'Little/no exercise', 'Light exercise', 'Moderate exercise (3-5 days/wk)',
        'Very active (6-7 days/wk)', 'Extra active (very active & physical job)'
    ])
    option = st.selectbox('Choose your weight loss plan:', display.plans)
    st.session_state.weight_loss_option = option
    weight_loss = display.weights[display.plans.index(option)]
    number_of_meals = st.slider('Meals per day', 3, 5, value=3)
    if number_of_meals == 3:
        meals_calories_perc = {'breakfast':0.35, 'lunch':0.40, 'dinner':0.25}
    elif number_of_meals == 4:
        meals_calories_perc = {'breakfast':0.30, 'morning snack':0.05, 'lunch':0.40, 'dinner':0.25}
    else:
        meals_calories_perc = {'breakfast':0.30, 'morning snack':0.05, 'lunch':0.40, 'afternoon snack':0.05, 'dinner':0.20}
    
    generated = st.form_submit_button("Generate")

if generated:
    st.session_state.generated = True
    person = Person(age, height, weight, gender, activity, meals_calories_perc, weight_loss)
    with st.container():
        display.display_bmi(person)
    with st.container():
        display.display_calories(person)
    with st.spinner('Generating recommendations...'):     
        recommendations = person.generate_recommendations()
        st.session_state.recommendations = recommendations
        st.session_state.person = person

if st.session_state.generated:
    with st.container():
        display.display_recommendation(st.session_state.person, st.session_state.recommendations)
        st.success('Recommendation Generated Successfully!', icon="✅")
    with st.container():
        display.display_meal_choices(st.session_state.person, st.session_state.recommendations)