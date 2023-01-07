from flask import render_template, request, redirect, url_for, session
from app import app, mysql
from flask_bcrypt import Bcrypt
from datetime import date
from flask_mysqldb import MySQLdb

bcrypt = Bcrypt(app)

@app.route('/', methods=['GET', 'POST'])
def home():
	return render_template('home.html')

@app.route('/home', methods=['GET', 'POST'])
def laterhome():
	return render_template('home.html')

@app.route('/registerUser', methods=['GET', 'POST'])
def registerUser():
	name = None
	if request.method == "POST":
		details = request.form
		firstName = details['fname']
		lastName = details['lname']
		name = firstName + ' ' + lastName
		email = details['email']
		cur = mysql.connection.cursor()
		cur.execute("SELECT user_id FROM user WHERE email LIKE %s", [email])
		user_id = cur.fetchone()
		cur.close()
		if (user_id != None):
			# email already exists
			return render_template('registerUser.html', name=None, error=True)
		# email doesn't exist
		hashedPW = bcrypt.generate_password_hash(details['password']).decode('utf-8')
		cur = mysql.connection.cursor()
		cur.execute("INSERT INTO user(first_name, last_name, email, password) VALUES (%s, %s, %s, %s)", (firstName, lastName, email, hashedPW))
		mysql.connection.commit()
		cur.execute("SELECT user_id FROM user where first_name LIKE %s and last_name LIKE %s and email LIKE %s and password LIKE %s", (firstName, lastName, email, hashedPW))
		session['user'] = cur.fetchone()[0]
		cur.close()
		return render_template('registerUser.html', name=name, error=False)
	return render_template('registerUser.html', name=None, error=False)

@app.route('/loginUser', methods=['GET', 'POST'])
def loginUser():
	name = None
	if request.method == "POST":
		details = request.form
		email = details['email']
		password = details['password']
		cur = mysql.connection.cursor()
		cur.execute("SELECT first_name, last_name, password, user_id FROM user WHERE email LIKE %s", [email])
		row = cur.fetchone()
		cur.close()
		if row == None:
			# email doesn't exist -> error 1
			return render_template('loginUser.html', name=None, error=1)
		# email exists -> check password
		if (bcrypt.check_password_hash(row[2], password) == False):
			# password is wrong -> error 2
			return render_template('loginUser.html', name=None, error=2)
		name = row[0] + ' ' + row[1]
		session['user'] = row[3]
		return render_template('loginUser.html', name=name, error=0)
	return render_template('loginUser.html', name=None, error=0)

@app.route('/logoutUser')
def logout():
	session.pop('user', None)
	return redirect(url_for('loginUser'))

@app.route('/updatePassword', methods=['GET', 'POST'])
def updatePassword():
	if 'user' not in session:
		return redirect(url_for('home'))
	if request.method == "POST":
		user = session['user']
		details = request.form
		cur = mysql.connection.cursor()
		cur.execute("SELECT password FROM user WHERE user_id LIKE %s", [user])
		row = cur.fetchone()
		cur.close()
		if (bcrypt.check_password_hash(row[0], details['oldpw']) == False):
			# password is wrong -> error -1
			return render_template('updatePassword.html', error=-1)
		# change password
		cur = mysql.connection.cursor()
		hashedPW = bcrypt.generate_password_hash(details['newpw']).decode('utf-8')
		cur.execute("UPDATE user SET password = %s WHERE user_id LIKE %s", (hashedPW, user))
		mysql.connection.commit()
		cur.close()
		return render_template('updatePassword.html', error=1)
	return render_template('updatePassword.html', error=0)

@app.route('/deleteUser', methods=['GET', 'POST'])
def deleteUser():
	if 'user' not in session:
		return redirect(url_for('home'))
	if request.method == "POST":
		user = session['user']
		details = request.form
		cur = mysql.connection.cursor()
		cur.execute("SELECT password, email FROM user WHERE user_id LIKE %s", [user])
		row = cur.fetchone()
		cur.close()
		if (bcrypt.check_password_hash(row[0], details['password']) == False):
			# password is wrong -> error -1
			return render_template('deleteUser.html', error=-1)
		# delete user
		cur = mysql.connection.cursor()
		cur.execute("DELETE FROM user WHERE email LIKE %s", [row[1]])
		mysql.connection.commit()
		cur.close()
		session.pop('user', None)
		return render_template('deleteUser.html', error=1)
	return render_template('deleteUser.html', error=0)

@app.route('/searchRecipesByTag', methods=['GET', 'POST'])
def searchRecipesByTag():
	recipes = None
	if request.method == "POST":
		details = request.form
		tag = details['tag']
		cur = mysql.connection.cursor()
		cur.execute("SELECT r.recipe_id, r.recipe_name FROM recipe r JOIN recipe_tags t ON r.recipe_id = t.recipe_id \
		WHERE t.tag_name LIKE %s and cooking_method NOT LIKE %s", [tag, "see later"])
		recipes = cur.fetchall()
		cur.close()
	return render_template('searchRecipesByTag.html', recipes=recipes)

@app.route('/searchRecipesByUser', methods=['GET', 'POST'])
def searchRecipesByUser():
	recipes = None
	if request.method == "POST":
		details = request.form
		first_name = details['fname']
		last_name = details['lname']
		cur = mysql.connection.cursor()
		cur.execute("SELECT rec.recipe_id, rec.recipe_name \
		FROM recipe rec JOIN user u ON rec.user_id = u.user_id WHERE \
		u.first_name LIKE %s and u.last_name LIKE %s and cooking_method NOT LIKE %s", [first_name, last_name, "see later"])
		recipes = cur.fetchall()
		cur.close()
	return render_template('searchRecipesByUser.html', recipes=recipes)

@app.route('/searchRecipesByName', methods=['GET', 'POST'])
def searchRecipesByName():
	recipes = None
	if request.method == "POST":
		details = request.form
		name = details['recipe_name'] + "%"
		cur = mysql.connection.cursor()
		cur.execute("SELECT r.recipe_id, r.recipe_name FROM recipe r WHERE recipe_name LIKE %s and cooking_method not LIKE %s", [name, "see later"])
		recipes = cur.fetchall()
		cur.close()
	return render_template('searchRecipesByName.html', recipes=recipes)

@app.route('/myRecipes', methods=['GET', 'POST'])
def myRecipes():
	if 'user' not in session:
		return redirect(url_for('home'))
	user = session['user']
	recipes = None
	if request.method == "GET":
		cur = mysql.connection.cursor()
		cur.execute("SELECT r.recipe_id, r.recipe_name FROM recipe r WHERE user_id LIKE %s and cooking_method not LIKE %s", [user, "see later"])
		recipes = cur.fetchall()
		cur.close()
	print(user)
	return render_template('myRecipes.html', recipes=recipes, deleted=0)

@app.route('/addReview/<int:recipe_id>', methods=['GET', 'POST'])
def addReview(recipe_id):
	if 'user' not in session:
		return redirect(url_for('home'))
	user = session['user']
	today = date.today()
	cur = mysql.connection.cursor()
	cur.execute("SELECT recipe_name FROM recipe WHERE recipe_id LIKE %s", [recipe_id])
	recipe_name = cur.fetchone()[0]
	cur.close()
	if request.method == "POST":
		details = request.form
		comment = details['Comment']
		rating = float(details['stars'])
		cur = mysql.connection.cursor()
		try:
			cur.execute("INSERT INTO reviewers(user_id, recipe_id, review_date, stars, review) VALUES (%s, %s, %s, %s, %s)", (user, recipe_id, today, rating, comment))
			mysql.connection.commit()
		except (MySQLdb.Error, MySQLdb.Warning) as e:
			print(e)
			cur.close()
			return render_template('addReview.html', recipe_name=recipe_name, error=-1)
		cur.close()
		return render_template('addReview.html', recipe_name=recipe_name, error=1)
	return render_template('addReview.html', recipe_name=recipe_name, error=0)

@app.route('/searchRecipesByIngredient', methods=['GET', 'POST'])
def searchRecipesByIngredients():
	recipes = None
	if request.method == "POST":
		details = request.form
		ingredient = "%" + details['ingredient'] + "%"
		cur = mysql.connection.cursor()
		cur.execute("SELECT r.recipe_id, r.recipe_name \
		FROM recipe r JOIN recipe_ingredients t ON r.recipe_id = t.recipe_id WHERE \
		t.name LIKE %s and cooking_method NOT LIKE %s", [ingredient, "see later"])
		recipes = cur.fetchall()
		cur.close()
	return render_template('searchRecipesByIngredient.html', recipes=recipes)

@app.route("/recipe/<int:recipe_id>", methods=['GET', 'POST'])
def recipe(recipe_id):
	recipe = None
	if request.method == "POST":
		cur = mysql.connection.cursor()
		cur.execute("SELECT recipe_name, cooking_method, cuisine, image, prep_time, serves, i.name \
		FROM recipe r JOIN recipe_ingredients i ON r.recipe_id = i.recipe_id JOIN recipe_tags t ON r.recipe_id = t.recipe_id \
		WHERE r.recipe_id LIKE %s", [recipe_id])
		recipe = cur.fetchone()
		if recipe == None:
			cur.close()
			return render_template('recipe.html', recipe=None, recid=recipe_id)
		recipe = list(recipe)
		if recipe[1] != None:
			directions = recipe[1].lstrip('[').rstrip(']')
			directions = directions.split("', '")
			directions[0] = directions[0].lstrip("'")
			directions[-1] = directions[-1].rstrip("'")
			recipe[1] = directions
		if recipe[2] != None:
			cuisine = recipe[2].lstrip('[').rstrip(']')
			cuisine = cuisine.split("', '")
			cuisine[0] = cuisine[0].lstrip("'")
			cuisine[-1] = cuisine[-1].rstrip("'")
			recipe[2] = cuisine
		cur = mysql.connection.cursor()
		cur.execute("SELECT rating FROM recipe_ratings WHERE recipe_id LIKE %s", [recipe_id])
		stars = cur.fetchone()
		if stars == None:
			stars = "N/A"
		else:
			stars = stars[0]
		cur.close()
	return render_template('recipe.html', recipe=recipe, recid=recipe_id, rating=stars)

@app.route('/createRecipe', methods=['GET', 'POST'])
def createRecipe():
	if 'user' not in session:
		return redirect(url_for('home'))
	user = session['user']
	if request.method == "POST":
		details = request.form
		cur = mysql.connection.cursor()
		try:
			cur.execute("INSERT INTO recipe(recipe_name, cooking_method, cuisine, image, prep_time, serves, user_id) VALUES (%s, %s, %s, %s, %s, %s, %s)", (details['title'], details['cooking_method'], details['cuisine'], None, details['prep_time'], details['serves'], user))
			mysql.connection.commit()
			recipe_id = cur.lastrowid
			# add tags
			tags = details['tags'].split(', ')
			for tag in tags:
				cur.execute("INSERT INTO recipe_tags(recipe_id, tag_name) VALUES (%s, %s)", (recipe_id, tag))
				mysql.connection.commit()
			# add ingredients
			ingredients = details['ingredients'].split(', ')
			for ingredient in ingredients:
				cur.execute("INSERT INTO recipe_ingredients(recipe_id, name) VALUES (%s, %s)", (recipe_id, ingredient))
				mysql.connection.commit()
		except (MySQLdb.Error, MySQLdb.Warning) as e:
			print(e)
			cur.close()
			return render_template('createRecipe.html', error=-1)
		cur.close()
		return render_template('createRecipe.html', error=1)
	return render_template('createRecipe.html', error=0)

# @app.route('/editRecipe/<int:recipe_id>', methods=['GET', 'POST'])
# def editRecipe(recipe_id):
# 	if 'user' not in session:
# 		return redirect(url_for('home'))
# 	user = session['user']
# 	if request.method == "POST":
# 		print("hi")
# 		details = request.form
# 		print(details['title'] == None)
# 		cur = mysql.connection.cursor()
# 		try:
# 			if (details['title'] != None):
# 				cur.execute("UPDATE recipe SET recipe_name = %s WHERE recipe_id LIKE %s", (details['title'], recipe_id))
# 			if (details['cooking_method'] != None):
# 				cur.execute("UPDATE recipe SET cooking_method = %s WHERE recipe_id LIKE %s", (details['cooking_method'], recipe_id))
# 			if (details['cuisine'] != None):
# 				cur.execute("UPDATE recipe SET cuisine = %s WHERE recipe_id LIKE %s", (details['cuisine'], recipe_id))
# 			if (details['prep_time'] != None):
# 				cur.execute("UPDATE recipe SET prep_time = %s WHERE recipe_id LIKE %s", (details['prep_time'], recipe_id))
# 			if (details['serves'] != None):
# 				cur.execute("UPDATE recipe SET serves = %s WHERE recipe_id LIKE %s", (details['serves'], recipe_id))
# 			mysql.connection.commit()
# 		except (MySQLdb.Error, MySQLdb.Warning) as e:
# 			print(e)
# 			return render_template('editRecipe.html', error=-1)
# 		return render_template('editRecipe.html', error=1)
# 	return render_template('editRecipe.html', error=0)

@app.route('/deleteRecipe/<int:recipe_id>', methods=['GET', 'POST'])
def deleteRecipe(recipe_id):
	if 'user' not in session:
		return redirect(url_for('home'))
	# make sure user is recipe creator
	user = session['user']
	cur = mysql.connection.cursor()
	cur.execute("SELECT user_id FROM recipe WHERE recipe_id LIKE %s", [recipe_id])
	user_id = cur.fetchone()[0]
	cur.close()
	if (user != user_id):
		return redirect(url_for('home'))
	if request.method == "POST":
		cur = mysql.connection.cursor()
		cur.execute("DELETE FROM recipe WHERE recipe_id LIKE %s", [recipe_id])
		mysql.connection.commit()
		cur.close()
		return redirect(url_for('myRecipes', recipes=None, deleted=1))
	return redirect(url_for('myRecipes', recipes=None, deleted=0))
@app.route('/imFeelingLucky', methods=['GET', 'POST'])
def imFeelingLucky():
	if 'user' not in session:
		return redirect(url_for('home'))
	user = session['user']
	recipes = None
	if request.method == "GET":
		cur = mysql.connection.cursor()
		# put stored procedure here
		
		cur.callproc('recommender', (user,))
		recipes = cur.fetchall()
		# for r in recipes:
		# 	print(r)
		cur.close()


	# print(user)
	return render_template('imFeelingLucky.html', recipes=recipes)
