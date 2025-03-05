from fastapi import FastAPI, HTTPException, Query
import requests
import os
import uvicorn
from typing import Optional, List, Dict, Any

app = FastAPI(
    title="DexScreener API",
    description="API for retrieving DeFi data including DEX pairs, tokens, and market information",
    version="1.0.0"
)

BASE_URL = "https://api.dexscreener.com/latest"

@app.get("/")
def home():
    return {"message": "✅ DexScreener API is running!", "version": "1.0.0"}

# Helper function to send requests to DexScreener
async def fetch_from_dexscreener(endpoint: str, params: Optional[Dict[str, Any]] = None):
    url = f"{BASE_URL}{endpoint}"
    
    print(f"🔍 Sending request to: {url}")
    print(f"🔍 With params: {params}")
    
    try:
        response = requests.get(url, params=params)
        
        print(f"✅ Response status: {response.status_code}")
        
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 400:
            print(f"❌ Bad Request: {response.text}")
            raise HTTPException(status_code=400, detail=f"❌ Bad Request: {response.text}")
        elif response.status_code == 429:
            print(f"❌ Too Many Requests: {response.text}")
            raise HTTPException(status_code=429, detail="❌ Rate limit exceeded. Please try again later.")
        else:
            print(f"⚠ Unexpected Error: {response.text}")
            raise HTTPException(status_code=response.status_code, detail=f"⚠ Unexpected Error: {response.text[:200]}")
    except requests.RequestException as e:
        print(f"❌ Request error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"❌ Connection Error: {str(e)}")

# 1️⃣ Search for pairs by token address
@app.get("/pairs/token/{tokenAddress}")
async def get_pairs_by_token(
    tokenAddress: str,
    limit: Optional[int] = Query(10, description="Number of results to return (max 100)")
):
    """
    Search for DEX pairs by token address
    """
    result = await fetch_from_dexscreener(f"/dex/search?q={tokenAddress}")
    
    # Limit the number of pairs returned
    if "pairs" in result and isinstance(result["pairs"], list):
        result["pairs"] = result["pairs"][:min(limit, 100)]
    
    return result

# 2️⃣ Get pairs by DEX and token address (e.g., uniswap, pancakeswap)
@app.get("/pairs/dex/{dexId}/{tokenAddress}")
async def get_pairs_by_dex_and_token(
    dexId: str,
    tokenAddress: str,
    limit: Optional[int] = Query(10, description="Number of results to return (max 100)")
):
    """
    Get pairs for a specific DEX and token address
    """
    result = await fetch_from_dexscreener(f"/dex/pairs/{dexId}/{tokenAddress}")
    
    # Limit the number of pairs returned
    if "pairs" in result and isinstance(result["pairs"], list):
        result["pairs"] = result["pairs"][:min(limit, 100)]
    
    return result

# 3️⃣ Get all pairs from a specific DEX
@app.get("/pairs/dex/{dexId}")
async def get_pairs_by_dex(
    dexId: str,
    limit: Optional[int] = Query(10, description="Number of results to return (max 100)")
):
    """
    Get all pairs for a specific DEX
    """
    result = await fetch_from_dexscreener(f"/dex/pairs/{dexId}")
    
    # Limit the number of pairs returned
    if "pairs" in result and isinstance(result["pairs"], list):
        result["pairs"] = result["pairs"][:min(limit, 100)]
    
    return result

# 4️⃣ Get pair by pair address
@app.get("/pairs/address/{pairAddress}")
async def get_pair_by_address(pairAddress: str):
    """
    Get detailed information about a specific trading pair by its address
    """
    return await fetch_from_dexscreener(f"/dex/pairs/{pairAddress}")

# 5️⃣ Get trending pairs
@app.get("/pairs/trending")
async def get_trending_pairs(
    chain: Optional[str] = Query(None, description="Chain filter (e.g., ethereum, bsc)"),
    limit: Optional[int] = Query(10, description="Number of results to return (max 100)")
):
    """
    Get currently trending pairs
    """
    endpoint = "/dex/pairs/trending"
    if chain:
        endpoint = f"{endpoint}/{chain}"
    
    result = await fetch_from_dexscreener(endpoint)
    
    # Limit the number of pairs returned
    if "pairs" in result and isinstance(result["pairs"], list):
        result["pairs"] = result["pairs"][:min(limit, 100)]
    
    return result

# 6️⃣ Search for pairs by token symbol or name
@app.get("/search")
async def search_pairs(
    query: str = Query(..., description="Token name or symbol to search for"),
    limit: Optional[int] = Query(10, description="Number of results to return (max 100)")
):
    """
    Search for pairs by token name or symbol
    """
    result = await fetch_from_dexscreener(f"/dex/search?q={query}")
    
    # Limit the number of pairs returned
    if "pairs" in result and isinstance(result["pairs"], list):
        result["pairs"] = result["pairs"][:min(limit, 100)]
    
    return result

# 7️⃣ Get top gainers
@app.get("/pairs/gainers")
async def get_top_gainers(
    chain: Optional[str] = Query(None, description="Chain filter (e.g., ethereum, bsc)"),
    period: str = Query("1d", description="Time period (1h, 6h, 24h, 7d, 30d)"),
    limit: Optional[int] = Query(10, description="Number of results to return (max 100)")
):
    """
    Get top gaining pairs for a specific time period
    """
    # Convert period to the format expected by DexScreener
    period_map = {
        "1h": "h1",
        "6h": "h6", 
        "24h": "h24",
        "1d": "h24",  # 1d is the same as 24h
        "7d": "d7",
        "30d": "d30"
    }
    
    dex_period = period_map.get(period, "h24")
    
    # Construct the endpoint
    endpoint = f"/dex/gainers/{dex_period}"
    if chain:
        endpoint = f"{endpoint}/{chain}"
    
    result = await fetch_from_dexscreener(endpoint)
    
    # Limit the number of pairs returned
    if "pairs" in result and isinstance(result["pairs"], list):
        result["pairs"] = result["pairs"][:min(limit, 100)]
    
    return result

# 8️⃣ Get top losers
@app.get("/pairs/losers")
async def get_top_losers(
    chain: Optional[str] = Query(None, description="Chain filter (e.g., ethereum, bsc)"),
    period: str = Query("1d", description="Time period (1h, 6h, 24h, 7d, 30d)"),
    limit: Optional[int] = Query(10, description="Number of results to return (max 100)")
):
    """
    Get top losing pairs for a specific time period
    """
    # Convert period to the format expected by DexScreener
    period_map = {
        "1h": "h1",
        "6h": "h6", 
        "24h": "h24",
        "1d": "h24",  # 1d is the same as 24h
        "7d": "d7",
        "30d": "d30"
    }
    
    dex_period = period_map.get(period, "h24")
    
    # Construct the endpoint
    endpoint = f"/dex/losers/{dex_period}"
    if chain:
        endpoint = f"{endpoint}/{chain}"
    
    result = await fetch_from_dexscreener(endpoint)
    
    # Limit the number of pairs returned
    if "pairs" in result and isinstance(result["pairs"], list):
        result["pairs"] = result["pairs"][:min(limit, 100)]
    
    return result

# 9️⃣ Get all supported chains
@app.get("/chains")
async def get_chains():
    """
    Get a list of all supported chains
    """
    return {"chains": [
        "ethereum", "bsc", "polygon", "avalanche", "fantom", "arbitrum", 
        "celo", "harmony", "cronos", "optimism", "moonriver", "moonbeam",
        "metis", "aurora", "kava", "base", "linea", "mantle", "zksync",
        "scroll", "bnbchain", "solana", "polygon_zkevm", "arbitrum_nova"
    ]}

# Run the server
if __name__ == "__main__":
    port = int(os.getenv("PORT", 8086))  # Using port 8086 to avoid conflicts with other APIs
    print(f"🚀 Starting DexScreener API server on port {port}...")
    uvicorn.run(app, host="0.0.0.0", port=port)
