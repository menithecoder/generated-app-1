import os
import sqlite3
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from contextlib import contextmanager
import json

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database setup
DB_PATH = "./app.db"

@contextmanager
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def init_db():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS pianos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                brand TEXT NOT NULL,
                price REAL NOT NULL,
                type TEXT NOT NULL,
                keys INTEGER NOT NULL,
                description TEXT,
                image_url TEXT,
                in_stock BOOLEAN DEFAULT 1
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cart (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                piano_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL,
                FOREIGN KEY (piano_id) REFERENCES pianos (id)
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL,
                phone TEXT NOT NULL,
                address TEXT NOT NULL,
                total_price REAL NOT NULL,
                items TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Check if pianos table is empty
        cursor.execute('SELECT COUNT(*) FROM pianos')
        if cursor.fetchone()[0] == 0:
            sample_pianos = [
                ('Steinway & Sons D-274', 'Steinway & Sons', 98000, 'Grand Piano', 88, 'Premium concert grand piano with exceptional sound quality and touch', 'https://images.unsplash.com/photo-1510915361894-db8b60106cb1?w=500&h=400&fit=crop', 1),
                ('Yamaha CFX', 'Yamaha', 78500, 'Grand Piano', 88, 'Professional grand piano ideal for concert halls and studios', 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=500&h=400&fit=crop', 1),
                ('Roland FP-90X', 'Roland', 3995, 'Digital Piano', 88, 'Portable digital piano with realistic sound engine and weighted keys', 'https://images.unsplash.com/photo-1514525253161-7a46d19cd819?w=500&h=400&fit=crop', 1),
                ('Kawai K-300', 'Kawai', 45000, 'Upright Piano', 88, 'Professional upright piano for teaching and performance', 'https://images.unsplash.com/photo-1493225457124-a3eb161ffa5f?w=500&h=400&fit=crop', 1),
                ('Casio Privia PX-870', 'Casio', 1299, 'Digital Piano', 88, 'Compact digital piano with excellent sound and portability', 'https://images.unsplash.com/photo-1511379938547-c1f69b13d835?w=500&h=400&fit=crop', 1),
                ('Bosendorfer 290 Imperial', 'Bosendorfer', 125000, 'Grand Piano', 97, 'Legendary Austrian grand piano with unique sound character', 'https://images.unsplash.com/photo-1487180144351-b8472da7d491?w=500&h=400&fit=crop', 1),
                ('Korg Kross 2', 'Korg', 2499, 'Synthesizer Piano', 88, 'Advanced synthesizer with piano sounds and synthesis capabilities', 'https://images.unsplash.com/photo-1459749411175-04bf5292ceea?w=500&h=400&fit=crop', 1),
                ('Schimmel K122', 'Schimmel', 35000, 'Upright Piano', 88, 'German-crafted upright piano for studios and schools', 'https://images.unsplash.com/photo-1519412666065-38cd8083d218?w=500&h=400&fit=crop', 1),
            ]
            cursor.executemany(
                'INSERT INTO pianos (name, brand, price, type, keys, description, image_url, in_stock) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
                sample_pianos
            )
        conn.commit()

init_db()

@app.get("/")
async def read_root():
    return FileResponse("index.html")

@app.get("/api/pianos")
async def get_pianos():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM pianos')
        pianos = [dict(row) for row in cursor.fetchall()]
    return pianos

@app.get("/api/pianos/{piano_id}")
async def get_piano(piano_id: int):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM pianos WHERE id = ?', (piano_id,))
        piano = cursor.fetchone()
    if piano:
        return dict(piano)
    return {"error": "Piano not found"}

@app.post("/api/cart/add")
async def add_to_cart(item: dict):
    piano_id = item.get("piano_id")
    quantity = item.get("quantity", 1)
    
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM cart WHERE piano_id = ?', (piano_id,))
        existing = cursor.fetchone()
        
        if existing:
            cursor.execute('UPDATE cart SET quantity = quantity + ? WHERE piano_id = ?', (quantity, piano_id))
        else:
            cursor.execute('INSERT INTO cart (piano_id, quantity) VALUES (?, ?)', (piano_id, quantity))
        conn.commit()
    
    return {"status": "success", "message": "Added to cart"}

@app.get("/api/cart")
async def get_cart():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT c.id, p.id as piano_id, p.name, p.price, p.image_url, c.quantity
            FROM cart c
            JOIN pianos p ON c.piano_id = p.id
        ''')
        items = [dict(row) for row in cursor.fetchall()]
    return items

@app.delete("/api/cart/{cart_id}")
async def remove_from_cart(cart_id: int):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM cart WHERE id = ?', (cart_id,))
        conn.commit()
    return {"status": "success", "message": "Removed from cart"}

@app.post("/api/cart/clear")
async def clear_cart():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM cart')
        conn.commit()
    return {"status": "success", "message": "Cart cleared"}

@app.post("/api/orders")
async def create_order(order: dict):
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Get cart items
        cursor.execute('''
            SELECT c.id, p.id as piano_id, p.name, p.price, c.quantity
            FROM cart c
            JOIN pianos p ON c.piano_id = p.id
        ''')
        items = [dict(row) for row in cursor.fetchall()]
        
        if not items:
            return {"error": "Cart is empty"}
        
        # Calculate total
        total_price = sum(item['price'] * item['quantity'] for item in items)
        
        # Create order
        cursor.execute('''
            INSERT INTO orders (name, email, phone, address, total_price, items)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            order.get('name'),
            order.get('email'),
            order.get('phone'),
            order.get('address'),
            total_price,
            json.dumps(items)
        ))
        conn.commit()
        
        # Clear cart
        cursor.execute('DELETE FROM cart')
        conn.commit()
        
        order_id = cursor.lastrowid
    
    return {"status": "success", "message": "Order created", "order_id": order_id, "total_price": total_price}

@app.get("/api/orders/{order_id}")
async def get_order(order_id: int):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM orders WHERE id = ?', (order_id,))
        order = cursor.fetchone()
    
    if order:
        order_dict = dict(order)
        order_dict['items'] = json.loads(order_dict['items'])
        return order_dict
    return {"error": "Order not found"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)