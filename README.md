# FitMate

**FitMate is your nutritionist.** The app provides you with more than 100 different recipes that align with your fitness goals, from low-carb to keto, vegan, and many more options to choose from! You are the main character. We care about you and your health; hence we provide you with recipes that align with your daily routine, as we have recipes for the three meals of the day. We are here to help anywhere, anytime; we help you transform into the best version of yourself.

The options in this app have no limits. We offer a variety of categories that go from fitness goals (such as losing weight or gaining muscle), nutritional specifications (meals with small quantities of carbohydrates or high amounts of proteins), and even lifestyles such as vegan, vegetarian, and KETO options. We also give you general alternatives for people who just want to improve their overall health.

This app is perfect for college students as many want to start a healthy and fitness path, however, they do not know how to make a diet or have meals that help them achieve their goals and that is why we are here, to guide you and give you recommendations on what to buy at the supermarket and the step by step of building a meal plan that is right for you. Also, a busy schedule shouldn't be an impediment to not start eating healthy. We offer you the “Save-Time” option that gives you quick and easy recipes that you can make in the shortest time possible and take with you wherever you want.

The app is your MATE, talk to it about your goals, and it will give you a hand on how to achieve them, at least in terms of food; that's what friends are for.

First, we have a data folder containing an Excel file with all the information for our meals. This makes data handling way easier. Then, we have the database itself, which includes all of the meals, their info, and user-related information such as personal information, password, and their favorite meals.

We also have a static folder, which contains the CSS code that does the visual part of the code, the icon folder contains PNGs of all the icons we used, and the image folder includes both the logo and all the images for the meals. As you can see every image of a meal has a three-letter identification that we are using to pair it up with the respective meal.

We also have templates that correspond to every different page the user can visit through our app, from the login, the meal details, creating the meal plan, the personal account, or personal info, reviewing the meal plans, etc. Some parts such as the meal change or the dashboard we have multiple versions depending on certain criteria. Other files such as the base.html or index.html are the foundations of the app as they handle general parts of the app such as the top menu.

Then we have our main codes.  We have the categories.py which is a dictionary that contains all of the categories. We are using this to filter the meals through the categories.  We also have a file called import_meals.py which is the file we used to take the information out of the Excel and populate our database.

We also have our test file which contains certain functions we are using on the main code and finally, we have our main code inside the document project.py.

We are also including the requirements as a text file, in here we can see all of the libraries required throughout the project. Using pip we can install these libraries into our system and run the app.

In terms of design, we started by doing the logo and icons, we wanted a friendly and healthy image, that is why we opted for a green and beige combination with neutral fonts. With the color scheme from the logo, and with the help of ChatGPT, we designed the style.css document with all the visual styles for the app and the different sides. We didn’t really have many debates in terms of the design. We knew we wanted the app to have a friendly and intuitive interface. The toughest part was looking for all the different pictures that we needed, once we got them we had to upload them all into our project using a unique identificator as mentioned before.

---

## 🚀 Instructions to run the app

1. Create and Activate a Virtual Environment:

On macOS/Linux:

python3 -m venv venv  
source venv/bin/activate  

	On Windows:  
python -m venv venv  
venv\Scripts\activate  

2. Install Requirements:  
pip install -r requirements.txt  

3. Run the app to create the Table (you can stop the code immediately):  
python project.py  

3. Import Meal Data:  
python import_meals.py  

4. Run the Application:  
python project.py
