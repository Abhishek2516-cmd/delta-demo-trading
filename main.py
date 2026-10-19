from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests

app = FastAPI()

# Enable CORS so Vercel Frontend can talk to Render Backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2 Demo Users Database (Virtual $10,000 USD each)
USERS_DB = {
    "user1": {"password": "password123", "virtual_balance": 10000.0, "positions": []},
    "user2": {"password": "password456", "virtual_balance": 10000.0, "positions": []}
}

class LoginRequest(BaseModel):
    username: str
    password: str

class OrderRequest(BaseModel):
    username: str
    symbol: str
    side: str
    quantity: float

@app.get("/")
def home():
    return {"status": "Delta Demo Trading Backend Running"}

@app.post("/api/login")
def login(data: LoginRequest):
    if data.username in USERS_DB and USERS_DB[data.username]["password"] == data.password:
        return {
            "status": "success", 
            "username": data.username, 
            "balance": USERS_DB[data.username]["virtual_balance"]
        }
    raise HTTPException(status_code=400, detail="Invalid Username or Password")

@app.get("/api/price/{symbol}")
def get_live_price(symbol: str):
    try:
        url = f"https://api.delta.exchange/v2/tickers/{symbol}"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            price = float(response.json()['result']['close'])
            return {"symbol": symbol, "price": price}
    except Exception:
        pass
    
    dummy_prices = {"BTCUSD": 82748.0, "ETHUSD": 2430.5, "NVDAUSD": 140.2, "TSLAUSD": 220.5}
    return {"symbol": symbol, "price": dummy_prices.get(symbol, 100.0)}

@app.post("/api/trade")
def place_trade(order: OrderRequest):
    if order.username not in USERS_DB:
        raise HTTPException(status_code=404, detail="User not found")
    
    price_res = get_live_price(order.symbol)
    current_price = price_res["price"]
    
    user = USERS_DB[order.username]
    trade_cost = current_price * order.quantity
    
    if order.side == "BUY" and user["virtual_balance"] < trade_cost:
        raise HTTPException(status_code=400, detail="Insufficient Demo Balance")
    
    if order.side == "BUY":
        user["virtual_balance"] -= trade_cost
    
    position = {
        "symbol": order.symbol,
        "side": order.side,
        "entry_price": current_price,
        "quantity": order.quantity
    }
    user["positions"].append(position)
    
    return {
        "status": "success",
        "message": f"Demo {order.side} Order Executed @ ${current_price}",
        "new_balance": user["virtual_balance"],
        "positions_list": user["positions"]
    }

@app.get("/api/user/{username}")
def get_user_data(username: str):
    if username in USERS_DB:
        return USERS_DB[username]
    raise HTTPException(status_code=404, detail="User not found")
