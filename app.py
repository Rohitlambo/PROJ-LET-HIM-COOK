import sqlite3
from flask import render_template, request, Flask, redirect, url_for, session

app = Flask(__name__)
app.secret_key = "secret_key"




# Home page route
@app.route('/')
def home():
    email = session.get('email')
    food_items = session.get('food_items', [])
    return render_template('home.html', email=email, food_items=food_items,)


# Menu page route
@app.route('/menu')
def menu():
    conn = sqlite3.connect('Lethimcook.db')
    c = conn.cursor()
    c.execute("SELECT name, price FROM Food")
    food_items = c.fetchall()
    conn.close()
    session['food_items'] = food_items
    return render_template('menu.html', food_items=food_items)

#deals page route
@app.route('/deals')
def deals():
    return render_template('deals.html')

#signup page route
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'GET':
        return render_template('signup.html')

    if request.method == 'POST':
        # get email and password from the form
        email = request.form['email']
        password = request.form['password']

        # insert the user into the database
        conn = sqlite3.connect('Lethimcook.db')
        c = conn.cursor()
        c.execute('''INSERT INTO Users (email, password) VALUES (?,?)''', (email, password,))
        conn.commit()
        conn.close()

        session['email'] = email

        return redirect(url_for("home"))

#login page route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')

    if request.method == 'POST':
        # get email and password from the form
        email = request.form['email']
        password = request.form['password']

        # check if the user exists in the database
        conn = sqlite3.connect('Lethimcook.db')
        c = conn.cursor()
        c.execute('''SELECT * FROM Users WHERE email=? AND password=?''', (email, password,))
        user = c.fetchone()
        conn.close()

        if user:
            session['email'] = email
            return redirect(url_for("home"))
        else:
            return render_template('login.html', message="Invalid email or password")

#logout page route
@app.route('/logout')
def logout():
    session.pop('email', None)
    session.pop('cart_items', None)
    return redirect(url_for('signup'))

#cart page route
@app.route('/cart')
def cart():
    cart_items = session.get('cart_items', [])
    return render_template('cart.html', cart_items=cart_items)

#insert food data from textfile to database
def InsertFood():
    conn = sqlite3.connect('Lethimcook.db')
    file = open('Food.txt', 'r')
    # Connect to the database
    c = conn.cursor()
    # Loop through each line in the file
    for line in file:
        # Split the line into name, price, and quantity
        name, price, quantity = line.strip().split(', ')
        # Insert the data into the Food table
        c.execute('''INSERT INTO Food (name, price, quantity) VALUES (?,?,?)''', (name, price, quantity))
    conn.commit()
    conn.close()


@app.route('/add_to_cart/<item>', methods=['GET', 'POST'])
def add_to_cart(item):
    if 'email' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        quantity = int(request.form.get('quantity'))
    else:
        quantity = 1

    if 'cart_items' not in session:
        cart_items = []
    else:
        cart_items = session["cart_items"]

    for cart_item in cart_items:
        if cart_item['item'] == item:
            cart_item['quantity'] += quantity
            break
    else:
        cart_items.append({'item': item, 'quantity': quantity})

    session["cart_items"] = cart_items

    return redirect(url_for('cart'))




@app.route('/clear_cart', methods=['POST'])
def clear_cart():
    session.pop('cart_items', None)
    return redirect(url_for('cart'))


@app.route('/checkout')
def checkout():
    if 'email' not in session:
        return redirect(url_for('login'))

    cart_items = session.get('cart_items', [])
    if not cart_items:
        return redirect(url_for('cart'))

    # Add items to the Orders table in the database
    conn = sqlite3.connect('Lethimcook.db')
    c = conn.cursor()
    total_cost = 0
    for item in cart_items:
        c.execute('''SELECT price FROM Food WHERE name=?''', (item['item'],))
        price = c.fetchone()[0]
        total_cost += price * item['quantity']

        # Update quantity of item in Food table
        c.execute('''UPDATE Food SET quantity=quantity-? WHERE name=?''', (item['quantity'], item['item'],))

        # Add item to Orders table
        c.execute('''INSERT INTO Orders (email, item, quantity, price) VALUES (?,?,?,?)''', (session['email'], item['item'], item['quantity'], price,))
    conn.commit()
    conn.close()

    # Clear cart session
    session.pop('cart_items', None)

    return redirect(url_for('cart'))



if __name__ == '__main__':
    app.run()
