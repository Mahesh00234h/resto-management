from flask import Flask, render_template, request, session, redirect, url_for, flash
from flask_socketio import SocketIO, emit

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_TYPE'] = 'filesystem'
socketio = SocketIO(app)

# Sample restaurant menu
menu = {
    "Pizza": 249.99,
    "Burger": 199.99,
    "Pasta": 149.99,
    "Salad": 79.99,
    "Grilled Chicken": 399.99,
    "Sushi Roll": 99.99,
    
    "Tacos": 49.49,
    "Garlic Bread": 49.99,
    
    "French Fries": 79.49,
    "Fish and Chips": 179.99,
    "Miso Soup": 129.99,
    "Chocolate Cake": 250.49,
    "Ice Cream": 65.99,
    "Coffee": 30.99,
    "Tea": 10.99,
    "Smoothie": 69.49,
    "Orange Juice": 49.99,
    "Cheesecake": 199.99
}

# Store selected items per user session
selected_items = {}
orders = []  # To hold all orders

# Sample admin credentials
admin_credentials = {
    "my": "5"  # Admin username and password
}

def is_admin():
    """Check if the current user is an admin."""
    return session.get('role') == 'admin'

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        username = request.form['username']
        session['username'] = username  # Store username in session
        session['role'] = 'user'  # Default role for users
        return redirect(url_for('menu_page'))
    return render_template('index.html')

@app.route('/menu')
def menu_page():
    username = session.get('username')  # Retrieve username from session
    return render_template('menu.html', menu=menu, username=username)

@app.route('/kitchen')
def kitchen_page():
    if not is_admin():
        return redirect(url_for('menu_page'))  # Redirect non-admins
    return render_template('kitchen.html', orders=orders)  # Pass orders to kitchen page

@app.route('/admin')
def admin_page():
    if not is_admin():
        return redirect(url_for('menu_page'))  # Redirect non-admins
    return render_template('admin.html', orders=orders)
    
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username in admin_credentials and admin_credentials[username] == password:
            session['username'] = username  # Store username in session
            session['role'] = 'admin'  # Set role to admin
            return redirect(url_for('admin_page'))  # Redirect to admin page after login
        else:
            return render_template('401.html')
    return render_template('admin_login.html')

@socketio.on('select_item')
def handle_select_item(item):
    username = session.get('username')  # Use username as user ID
    if username not in selected_items:
        selected_items[username] = []
    
    selected_items[username].append(item)
    emit('update_selection', selected_items[username], room=request.sid)

@socketio.on('get_total')
def handle_get_total():
    username = session.get('username')  # Use username as user ID
    total = sum(menu[item] for item in selected_items.get(username, []))
    emit('update_total', total, room=request.sid)

@socketio.on('place_order')
def handle_place_order(table_number):
    username = session.get('username')
    order_items = list(selected_items.get(username, []))  # Ensure order_items is a list
    
    if not order_items:  # Handle case when no items are selected
        emit('order_error', {'message': 'No items selected!'}, room=request.sid)
        return
    
    total = sum(menu[item] for item in order_items)  # Calculate total amount
    order_details = {
        'username': username,
        'table_number': table_number,
        'items': order_items,  # Confirmed to be a list
        'total': total  # Include total in order details
    }
    
    # Debugging: Print order details to ensure correctness
    print(f"Placing order: {order_details}")
    
    orders.append(order_details)  # Store the order
    selected_items[username] = []  # Clear the user's selected items after placing the order
    # Emit the new order to all connected clients
    socketio.emit('new_order', order_details)
    emit('order_placed', {'message': 'Order placed successfully!', 'table_number': table_number, 'items': order_items, 'total': total}, room=request.sid)

@socketio.on('disconnect')
def handle_disconnect():
    pass

if __name__ == '__main__':
    socketio.run(app, port=2000, debug=True)