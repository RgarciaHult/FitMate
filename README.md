# FitMate

FitMate is your nutritionist. The app provides you with more than 100 different recipes that align with your fitness goals, from low-carb to keto, vegan, and many more options to choose from! You are the main character. We care about you and your health; hence, we provide you with recipes that fit your daily routine, as we have recipes for the three meals of the day. We are here to help anywhere, anytime; we help you transform into the best version of yourself.

The options in this app have no limits. We offer a variety of categories that range from fitness goals (such as losing weight or gaining muscle), nutritional specifications (meals with small quantities of carbohydrates or high amounts of protein), and even lifestyles such as vegan, vegetarian, and KETO options. We also give you general alternatives if you just want to improve your overall health.

This app is perfect for college students because many want to start a healthy and fitness-oriented path; however, they do not know how to make a diet plan or have meals that help them achieve their goals. That is why we are here—to guide you and give you recommendations on what to buy at the supermarket and the step-by-step process of building a meal plan that is right for you. Also, a busy schedule shouldn’t be an impediment to starting a healthy diet. We offer you the “Save-Time” option that gives you quick and easy recipes you can make in the shortest time possible and take with you wherever you go.

The app is your MATE. Talk to it about your goals, and it will give you a hand on how to achieve them, at least in terms of food—that’s what friends are for.

First, we have a data folder containing an Excel file with all the information for our meals. This makes data handling much easier. Then, we have the database itself, which includes all of the meals, their information, and user-related details such as personal data, passwords, and favorite meals.

We also have a static folder, which contains the CSS code responsible for the visual aspects of the app; the icons folder contains PNGs of all the icons we used, and the images folder includes both the logo and all the images for the meals. As you can see, every meal image has a three-letter identifier that we use to match it with its respective meal.

We also have templates that correspond to every different page the user can visit through our app—from the login page, the meal details, creating the meal plan, personal account or personal info, reviewing the meal plans, and so on. For some parts, such as meal changes or the dashboard, we have multiple versions depending on certain criteria. Other files, such as base.html or index.html, form the foundation of the app by handling general elements like the top menu.

Next, we have our main code. We have categories.py, which is a dictionary containing all the categories we use to filter the meals. We also have a file called import_meals.py, which we used to extract the information from Excel and populate our database.

We also have our test file, which contains certain functions we use in the main code. Finally, we have our primary code inside the document project.py.

We are also including the requirements in a text file; here, we can see all the libraries required throughout the project. By using pip, we can install these libraries into our system and run the app.

In terms of design, we started by creating the logo and icons. We wanted a friendly and healthy image, which is why we chose a green and beige combination with neutral fonts. Using the color scheme from the logo—and with the help of ChatGPT—we designed the style.css document, which contains all the visual styles for the app and its different sections. We didn’t have many debates regarding the design because we knew we wanted the app to have a friendly and intuitive interface. The most challenging part was finding all the different pictures we needed; once we got them, we had to upload them into our project using a unique identifier, as mentioned before.
