from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import sqlite3
import os
import json
from datetime import datetime

app = FastAPI(title="Yamaha Piano Store")

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database setup
def get_db():
    conn = sqlite3.connect("./app.db")
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    
    # Create pianos table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pianos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            model TEXT NOT NULL,
            category TEXT NOT NULL,
            price REAL NOT NULL,
            description TEXT,
            features TEXT,
            image_url TEXT,
            in_stock INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Create orders table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_name TEXT NOT NULL,
            email TEXT NOT NULL,
            phone TEXT NOT NULL,
            address TEXT NOT NULL,
            piano_id INTEGER NOT NULL,
            quantity INTEGER DEFAULT 1,
            total_price REAL NOT NULL,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (piano_id) REFERENCES pianos (id)
        )
    """)
    
    # Create contact messages table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS contacts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            subject TEXT,
            message TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Insert sample Yamaha pianos if table is empty
    cursor.execute("SELECT COUNT(*) FROM pianos")
    if cursor.fetchone()[0] == 0:
        sample_pianos = [
            ("Yamaha CFX Concert Grand", "CFX", "Grand Piano", 179999.99, 
             "The Yamaha CFX is our flagship 9' concert grand piano, a full, rich tone with a wide palette of tonal colors.",
             '["Full concert grand size", "Hand-crafted in Japan", "Premium Spruce soundboard", "88 keys", "Polished Ebony finish"]',
             "https://images.unsplash.com/photo-1520523839897-bd0b52f945a0?w=800", 1),
            
            ("Yamaha C7X Grand Piano", "C7X", "Grand Piano", 89999.99,
             "The C7X delivers powerful bass and a clear treble, making it ideal for professional performances.",
             '["7\'6\" semi-concert grand", "A.R.E. treated soundboard", "German Röslau strings", "Slow-close fallboard"]',
             "https://images.unsplash.com/photo-1552422535-c45813c61732?w=800", 1),
            
            ("Yamaha C3X Grand Piano", "C3X", "Grand Piano", 54999.99,
             "The C3X offers the perfect balance of size and sound for home and studio use.",
             '["6\'1\" conservatory grand", "Duplex scaling", "Sostenuto pedal", "Premium hammer felts"]',
             "https://images.unsplash.com/photo-1514119412350-e174d90d280e?w=800", 1),
            
            ("Yamaha U3 Upright Piano", "U3", "Upright Piano", 14999.99,
             "The U3 is the world's best-selling professional upright piano with exceptional tonal depth.",
             '["52\" professional upright", "Spruce soundboard", "131cm height", "Soft-close fallboard"]',
             "https://images.unsplash.com/photo-1577002216534-0a0c36c8cb58?w=800", 1),
            
            ("Yamaha U1 Upright Piano", "U1", "Upright Piano", 11999.99,
             "The U1 delivers professional-level sound in a more compact size, perfect for home practice.",
             '["48\" upright", "Acoustic optimizer", "Premium hammers", "3 pedals"]',
             "https://images.unsplash.com/photo-1571974599782-87624638275e?w=800", 1),
            
            ("Yamaha CLP-795GP Clavinova", "CLP-795GP", "Digital Piano", 8999.99,
             "Experience the grandeur of a grand piano with the convenience of digital technology.",
             '["CFX and Bösendorfer samples", "GrandTouch-S keyboard", "Binaural sampling", "Bluetooth connectivity"]',
             "https://images.unsplash.com/photo-1549490349-8643362247b5?w=800", 1),
            
            ("Yamaha CLP-745 Clavinova", "CLP-745", "Digital Piano", 3499.99,
             "Premium digital piano with authentic grand piano touch and tone.",
             '["GrandTouch-S keyboard", "Virtual Resonance Modeling", "303 Voices", "USB Audio Recording"]',
             "https://images.unsplash.com/photo-1461784121038-f088ca1e7714?w=800", 1),
            
            ("Yamaha P-515 Portable Piano", "P-515", "Digital Piano", 1499.99,
             "Top-of-the-line portable piano with Natural Wood X keyboard and CFX/Bösendorfer sounds.",
             '["Natural Wood X keyboard", "CFX & Bösendorfer samples", "Bluetooth Audio", "40 Voices"]',
             "https://images.unsplash.com/photo-1516916759473-600c07bc12d4?w=800", 1),
            
            ("Yamaha GB1K Baby Grand", "GB1K", "Grand Piano", 16999.99,
             "The perfect entry point into Yamaha grand piano ownership.",
             '["5\' baby grand", "Yamaha action", "Polished Ebony finish", "Made in Indonesia"]',
             "https://images.unsplash.com/photo-1511379938547-c1f69419868d?w=800", 1),
            
            ("Yamaha AvantGrand N3X", "N3X", "Hybrid Piano", 19999.99,
             "The ultimate hybrid piano combining acoustic action with digital sound technology.",
             '["Real grand piano action", "Spatial Acoustic Speaker System", "CFX & Bösendorfer samples", "Tactile Response System"]',
             "https://images.unsplash.com/photo-1507838153414-b4b713384a76?w=800", 1),
        ]
        
        cursor.executemany("""
            INSERT INTO pianos (name, model, category, price, description, features, image_url, in_stock)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, sample_pianos)
    
    conn.commit()
    conn.close()

init_db()

# Pydantic models
class OrderCreate(BaseModel):
    customer_name: str
    email: str
    phone: str
    address: str
    piano_id: int
    quantity: int = 1

class ContactCreate(BaseModel):
    name: str
    email: str
    subject: Optional[str] = None
    message: str

# Routes
@app.get("/")
async def serve_home():
    return FileResponse("index.html")

@app.get("/api/pianos")
async def get_pianos(category: Optional[str] = None):
    conn = get_db()
    cursor = conn.cursor()
    
    if category and category != "all":
        cursor.execute("SELECT * FROM pianos WHERE category = ? ORDER BY price DESC", (category,))
    else:
        cursor.execute("SELECT * FROM pianos ORDER BY price DESC")
    
    pianos = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in pianos]

@app.get("/api/pianos/{piano_id}")
async def get_piano(piano_id: int):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM pianos WHERE id = ?", (piano_id,))
    piano = cursor.fetchone()
    conn.close()
    
    if not piano:
        raise HTTPException(status_code=404, detail="Piano not found")
    
    return dict(piano)

@app.post("/api/orders")
async def create_order(order: OrderCreate):
    conn = get_db()
    cursor = conn.cursor()
    
    # Get piano price
    cursor.execute("SELECT price, name FROM pianos WHERE id = ?", (order.piano_id,))
    piano = cursor.fetchone()
    
    if not piano:
        conn.close()
        raise HTTPException(status_code=404, detail="Piano not found")
    
    total_price = piano["price"] * order.quantity
    
    cursor.execute("""
        INSERT INTO orders (customer_name, email, phone, address, piano_id, quantity, total_price)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (order.customer_name, order.email, order.phone, order.address, 
          order.piano_id, order.quantity, total_price))
    
    order_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return {
        "message": "Order placed successfully!",
        "order_id": order_id,
        "piano_name": piano["name"],
        "total_price": total_price
    }

@app.get("/api/orders")
async def get_orders():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT o.*, p.name as piano_name, p.model as piano_model
        FROM orders o
        JOIN pianos p ON o.piano_id = p.id
        ORDER BY o.created_at DESC
    """)
    orders = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in orders]

@app.post("/api/contact")
async def create_contact(contact: ContactCreate):
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO contacts (name, email, subject, message)
        VALUES (?, ?, ?, ?)
    """, (contact.name, contact.email, contact.subject, contact.message))
    
    conn.commit()
    conn.close()
    
    return {"message": "Thank you for your message! We'll get back to you soon."}

@app.get("/api/categories")
async def get_categories():
    return [
        {"id": "all", "name": "All Pianos"},
        {"id": "Grand Piano", "name": "Grand Pianos"},
        {"id": "Upright Piano", "name": "Upright Pianos"},
        {"id": "Digital Piano", "name": "Digital Pianos"},
        {"id": "Hybrid Piano", "name": "Hybrid Pianos"}
    ]

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)