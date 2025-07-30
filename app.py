# Todo: Implement improve user experience

from flask import Flask, session, url_for, render_template, redirect, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, FloatField, IntegerField
from wtforms.validators import DataRequired

app = Flask(__name__)

app.secret_key = 'FirstRealProject'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///hang.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ---------------- Models ----------------

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), nullable=False, unique=True)
    foods = db.relationship('Food', backref='category', lazy=True)

class Food(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30), nullable=False, unique=True)
    price = db.Column(db.Float, nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)

class Cart(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    orders = db.relationship('OrderItem', lazy=True, backref='cart')

class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)
    cart_id = db.Column(db.Integer, db.ForeignKey('cart.id'), nullable=False)

# ---------------- Forms ----------------

class MenuForm(FlaskForm):
    category = StringField('Category', validators=[DataRequired()])
    food = StringField('Food', validators=[DataRequired()])
    price = FloatField('Price', validators=[DataRequired()])
    submit = SubmitField('Add')

class OrderForm(FlaskForm):
    food = StringField('Food', validators=[DataRequired()])
    price = FloatField('Price', validators=[DataRequired()])
    submit = SubmitField('Order')

# ---------------- Routes ----------------

@app.route('/')
def start_menu():
    return render_template('start.html')

@app.route('/menu', methods=['GET', 'POST'])
def menu():
    categories = Category.query.all()
    return render_template('menu.html', categories=categories)

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    form = MenuForm()
    if form.validate_on_submit():
        # Check if category exists, otherwise add
        category = Category.query.filter_by(name=form.category.data).first()
        if not category:
            category = Category(name=form.category.data)
            db.session.add(category)
            db.session.commit()

        # Check if food exists
        if Food.query.filter_by(name=form.food.data).first():
            flash("Food already exists.")
            return redirect(url_for('admin'))

        food = Food(name=form.food.data, price=form.price.data, category=category)
        db.session.add(food)
        db.session.commit()
        flash('Item added!')
        return redirect(url_for('admin'))

    return render_template('admin.html', form=form)

@app.route('/cart', methods=['GET', 'POST'])
def cart():
    # Assuming you store cart in session
    cart_id = session.get("cart_id")
    if not cart_id:
        flash("No cart found.")
        return redirect(url_for("menu"))

    cart = Cart.query.get(cart_id)
    if not cart:
        flash("Invalid cart.")
        return redirect(url_for("menu"))

    if request.method == "POST":
        action = request.form.get("action")

        if action == "place_order":
            # Handle placing the order
            flash("Order placed!")
            # Optionally clear cart here
            for order in cart.orders:
                db.session.delete(order)
            db.session.commit()
            return redirect(url_for("cart"))

        elif action == "clear_cart":
            for order in cart.orders:
                db.session.delete(order)
            db.session.commit()
            flash("Cart cleared.")
            return redirect(url_for("cart"))

        elif action == "remove_item":
            order_id = request.form.get("order_id")
            order = OrderItem.query.get(order_id)
            if order and order.cart_id == cart.id:
                db.session.delete(order)
                db.session.commit()
                flash("Item removed.")
            else:
                flash("Invalid item.")
            return redirect(url_for("cart"))

    total = sum(order.price * order.quantity for order in cart.orders)
    return render_template("cart.html", cart=cart, total=total)


@app.route('/add-to-cart/<int:food_id>', methods=['POST'])
def add_to_cart(food_id):
    cart_id = session.get("cart_id")
    if cart_id:
        cart = Cart.query.get(cart_id)
    else:
        cart = Cart()
        db.session.add(cart)
        db.session.commit()
        session["cart_id"] = cart.id

    food = Food.query.get_or_404(food_id)

    # Check if item already in cart
    order = OrderItem.query.filter_by(cart_id=cart.id, name=food.name).first()
    if order:
        order.quantity += 1
    else:
        order = OrderItem(name=food.name, quantity=1, price=food.price, cart=cart)
        db.session.add(order)

    db.session.commit()
    flash(f'Added {food.name} to cart!')
    return redirect(url_for('menu'))


# ---------------- Create Tables and Run ----------------

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
