"""
generate_data.py
----------------
Purpose:
    Generates a realistic, synthetic raw customer transaction dataset for a retail/e-commerce
    business with intentional data quality defects (duplicates, whitespace, mixed dates,
    category typos, missing values, and outliers).
    
    Ensures complete reproducibility through fixed random seeds.

Output:
    data/raw/customer_purchases_raw.csv
"""

from datetime import datetime, timedelta
import os
from typing import Dict, List, Tuple
import numpy as np
import pandas as pd

# Valid taxonomy and geographic mappings
VALID_CITIES: Dict[str, str] = {
    "Delhi": "North",
    "Noida": "North",
    "Jaipur": "North",
    "Mumbai": "West",
    "Pune": "West",
    "Ahmedabad": "West",
    "Bangalore": "South",
    "Hyderabad": "South",
    "Chennai": "South",
    "Kolkata": "East",
    "Bhubaneswar": "East",
}

VALID_CATEGORIES: Dict[str, List[Tuple[str, float, float]]] = {
    "Electronics": [
        ("Wireless Headphones", 1500.0, 4500.0),
        ("Smartwatch", 2200.0, 8000.0),
        ("Bluetooth Speaker", 1200.0, 3500.0),
        ("Power Bank", 800.0, 2000.0),
        ("USB-C Hub", 600.0, 1500.0),
    ],
    "Clothing": [
        ("Cotton T-Shirt", 400.0, 1200.0),
        ("Slim Fit Jeans", 1200.0, 3000.0),
        ("Casual Jacket", 2000.0, 5000.0),
        ("Formal Shirt", 900.0, 2200.0),
        ("Athletic Shorts", 500.0, 1200.0),
    ],
    "Home & Kitchen": [
        ("Coffee Maker", 1800.0, 4500.0),
        ("Electric Blender", 1500.0, 3200.0),
        ("Non-Stick Frying Pan", 800.0, 2000.0),
        ("Stainless Steel Knife Set", 600.0, 1800.0),
        ("Ceramic Mug Set", 400.0, 1000.0),
    ],
    "Beauty & Personal Care": [
        ("Moisturizing Cream", 350.0, 950.0),
        ("Sunscreen SPF 50", 450.0, 1100.0),
        ("Herbal Shampoo", 300.0, 750.0),
        ("Perfume Spray", 1200.0, 3500.0),
        ("Face Cleanser", 250.0, 650.0),
    ],
    "Sports & Fitness": [
        ("Yoga Mat", 600.0, 1500.0),
        ("Adjustable Dumbbells", 1500.0, 4500.0),
        ("Resistance Bands Set", 400.0, 1100.0),
        ("Water Bottle 1L", 300.0, 800.0),
        ("Running Shoes", 2000.0, 5500.0),
    ],
    "Books": [
        ("Data Analytics Handbook", 600.0, 1200.0),
        ("Business Strategy Guide", 450.0, 950.0),
        ("Psychology of Money", 350.0, 700.0),
        ("Python Programming", 550.0, 1100.0),
        ("Atomic Habits", 400.0, 800.0),
    ],
}

CATEGORY_TYPOS = {
    "Electronics": ["Electrnics", "ELECTRONICS", "electronicss", "Electonics"],
    "Clothing": ["Cloting", "CLOTHING", "clothng", "Clothings"],
    "Home & Kitchen": ["Home and Kitchen", "Home & kitchen", "Home&Kitchen", "Home Kitchen"],
    "Beauty & Personal Care": ["Beauty & Personal", "beauty & personal care", "Beauty & Care"],
    "Sports & Fitness": ["Sports & Fitnes", "Sports and Fitness", "Sport & Fitness"],
    "Books": ["Boks", "BOOKS", "Bookss"],
}

FIRST_NAMES = [
    "Aarav", "Aditi", "Rohan", "Pooja", "Vikram", "Sneha", "Rahul", "Ananya",
    "Karan", "Priya", "Amit", "Neha", "Varun", "Kavya", "Siddharth", "Meera",
    "Ravi", "Divya", "Arjun", "Tanvi", "Nikhil", "Riya", "Manish", "Shreya",
]

LAST_NAMES = [
    "Sharma", "Verma", "Gupta", "Patel", "Mehta", "Singh", "Kumar", "Iyer",
    "Reddy", "Nair", "Joshi", "Chopra", "Deshmukh", "Bose", "Mukherjee", "Das",
]

OCCUPATIONS = [
    "Software Engineer", "Data Analyst", "Marketing Specialist", "Product Manager",
    "Doctor", "Teacher", "Consultant", "Financial Analyst", "Architect", "Designer",
    "Student", "Accountant", "Entrepreneur", "Sales Executive",
]

PAYMENT_METHODS = ["UPI", "Credit Card", "Debit Card", "Net Banking", "Cash on Delivery"]
PURCHASE_CHANNELS = ["Online", "In-Store", "Mobile App"]
LOYALTY_TIERS = ["Gold", "Silver", "Platinum", "Regular"]


def generate_raw_dataset(
    num_customers: int = 150,
    total_transactions: int = 1200,
    seed: int = 42,
    output_path: str = "data/raw/customer_purchases_raw.csv",
) -> pd.DataFrame:
    """
    Generate synthetic customer purchase transactions with realistic imperfections.
    
    Parameters:
        num_customers: Number of unique customer profiles to simulate.
        total_transactions: Target number of purchase transaction rows.
        seed: Random seed for reproducibility.
        output_path: Destination CSV filepath.
        
    Returns:
        pd.DataFrame containing the generated raw transactions.
    """
    np.random.seed(seed)
    
    # 1. Generate base customer profiles
    customers = []
    cities_list = list(VALID_CITIES.keys())
    
    for i in range(1, num_customers + 1):
        cid = f"C{i:04d}"
        fname = np.random.choice(FIRST_NAMES)
        lname = np.random.choice(LAST_NAMES)
        
        # Inject messy formatting into customer name
        name_variant = np.random.choice(["clean", "spaces", "lower", "upper", "multi_space"])
        if name_variant == "clean":
            cust_name = f"{fname} {lname}"
        elif name_variant == "spaces":
            cust_name = f"  {fname}   {lname}  "
        elif name_variant == "lower":
            cust_name = f"{fname.lower()} {lname.lower()}"
        elif name_variant == "upper":
            cust_name = f"{fname.upper()} {lname.upper()}"
        else:
            cust_name = f"{fname}     {lname}"
            
        age = int(np.random.randint(18, 72))
        gender = np.random.choice(["Male", "Female", "Other"], p=[0.48, 0.48, 0.04])
        city = np.random.choice(cities_list)
        region = VALID_CITIES[city]
        occupation = np.random.choice(OCCUPATIONS)
        loyalty = np.random.choice(LOYALTY_TIERS, p=[0.20, 0.35, 0.10, 0.35])
        
        customers.append({
            "Customer_ID": cid,
            "Customer_Name": cust_name,
            "Age": age,
            "Gender": gender,
            "City": city,
            "Region": region,
            "Occupation": occupation,
            "Loyalty_Status": loyalty,
        })
    
    df_cust = pd.DataFrame(customers)
    
    # 2. Generate transactions linked to customers
    # Distribute transaction counts following a power-law / Pareto-like pattern
    # 20% high-frequency buyers, 50% medium, 30% single-order buyers
    weights = np.random.exponential(scale=2.0, size=num_customers)
    weights = weights / weights.sum()
    chosen_customer_indices = np.random.choice(len(customers), size=total_transactions, p=weights)
    
    categories = list(VALID_CATEGORIES.keys())
    base_date = datetime(2024, 1, 1)
    end_date = datetime(2024, 12, 31)
    date_range_days = (end_date - base_date).days
    
    rows = []
    for idx in chosen_customer_indices:
        cust = customers[idx]
        cat = np.random.choice(categories)
        prod_tuple = VALID_CATEGORIES[cat][np.random.choice(len(VALID_CATEGORIES[cat]))]
        prod_name = prod_tuple[0]
        unit_price = round(float(np.random.uniform(prod_tuple[1], prod_tuple[2])), 2)
        qty = int(np.random.choice([1, 2, 3, 4, 5], p=[0.55, 0.25, 0.12, 0.05, 0.03]))
        
        # Discounts: 0%, 5%, 10%, 15%, 20%
        discount = float(np.random.choice([0.0, 0.05, 0.10, 0.15, 0.20], p=[0.40, 0.20, 0.20, 0.10, 0.10]))
        total_val = round(qty * unit_price * (1.0 - discount), 2)
        
        # Transaction date
        random_days = int(np.random.randint(0, date_range_days + 1))
        tx_dt = base_date + timedelta(days=random_days)
        
        # Mixed date representations
        date_format_type = np.random.choice(["iso", "slash_dmy", "dash_mdy", "text", "bad"], p=[0.60, 0.20, 0.12, 0.06, 0.02])
        if date_format_type == "iso":
            dt_str = tx_dt.strftime("%Y-%m-%d")
        elif date_format_type == "slash_dmy":
            dt_str = tx_dt.strftime("%d/%m/%Y")
        elif date_format_type == "dash_mdy":
            dt_str = tx_dt.strftime("%m-%d-%Y")
        elif date_format_type == "text":
            dt_str = tx_dt.strftime("%d %b %Y")
        else:
            dt_str = "INVALID_DATE"
            
        # Category typo injection (~8% chance)
        if np.random.rand() < 0.08:
            cat_str = np.random.choice(CATEGORY_TYPOS[cat])
        else:
            cat_str = cat
            
        pay_method = np.random.choice(PAYMENT_METHODS, p=[0.40, 0.25, 0.15, 0.10, 0.10])
        channel = np.random.choice(PURCHASE_CHANNELS, p=[0.60, 0.25, 0.15])
        
        rows.append({
            "Customer_ID": cust["Customer_ID"],
            "Customer_Name": cust["Customer_Name"],
            "Age": cust["Age"],
            "Gender": cust["Gender"],
            "City": cust["City"],
            "Region": cust["Region"],
            "Occupation": cust["Occupation"],
            "Product_Category": cat_str,
            "Product_Name": prod_name,
            "Purchase_Date": dt_str,
            "Quantity_Purchased": qty,
            "Unit_Price": unit_price,
            "Total_Purchase_Value": total_val,
            "Payment_Method": pay_method,
            "Purchase_Channel": channel,
            "Customer_Segment": "Standard",  # Will be refined in segmentation
            "Loyalty_Status": cust["Loyalty_Status"],
            "Discount_Used": discount,
            "Purchase_Frequency": 1,         # Intentionally placeholder/unaligned
            "Last_Purchase_Date": dt_str,    # Intentionally placeholder/unaligned
        })
        
    df_raw = pd.DataFrame(rows)
    
    # 3. Inject missing values
    # Missing Customer_ID in 10 rows
    null_cust_idx = np.random.choice(len(df_raw), size=10, replace=False)
    df_raw.loc[null_cust_idx, "Customer_ID"] = np.nan
    
    # Missing Purchase_Date in 8 rows
    null_date_idx = np.random.choice(len(df_raw), size=8, replace=False)
    df_raw.loc[null_date_idx, "Purchase_Date"] = np.nan
    
    # Missing Age in 25 rows
    null_age_idx = np.random.choice(len(df_raw), size=25, replace=False)
    df_raw.loc[null_age_idx, "Age"] = np.nan
    
    # Missing Gender in 15 rows
    null_gender_idx = np.random.choice(len(df_raw), size=15, replace=False)
    df_raw.loc[null_gender_idx, "Gender"] = np.nan
    
    # Missing Unit_Price in 20 rows (where Total_Purchase_Value exists)
    null_price_idx = np.random.choice(len(df_raw), size=20, replace=False)
    df_raw.loc[null_price_idx, "Unit_Price"] = np.nan
    
    # Missing Total_Purchase_Value in 25 rows (where Unit_Price exists)
    null_tot_idx = np.random.choice(len(df_raw), size=25, replace=False)
    df_raw.loc[null_tot_idx, "Total_Purchase_Value"] = np.nan
    
    # Missing Discount_Used in 30 rows
    null_disc_idx = np.random.choice(len(df_raw), size=30, replace=False)
    df_raw.loc[null_disc_idx, "Discount_Used"] = np.nan
    
    # 4. Inject Outliers (~10 bulk purchase orders)
    outlier_idx = np.random.choice(len(df_raw), size=10, replace=False)
    for oi in outlier_idx:
        qty = int(np.random.randint(20, 45))
        df_raw.loc[oi, "Quantity_Purchased"] = qty
        u_price = float(df_raw.loc[oi, "Unit_Price"]) if pd.notna(df_raw.loc[oi, "Unit_Price"]) else 3500.0
        disc = float(df_raw.loc[oi, "Discount_Used"]) if pd.notna(df_raw.loc[oi, "Discount_Used"]) else 0.0
        df_raw.loc[oi, "Total_Purchase_Value"] = round(qty * u_price * (1.0 - disc), 2)
        
    # 5. Inject exact duplicates (replicate 35 rows)
    dup_rows = df_raw.sample(n=35, random_state=seed)
    df_raw = pd.concat([df_raw, dup_rows], ignore_index=True)
    
    # Save raw CSV
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df_raw.to_csv(output_path, index=False)
    print(f"Generated raw dataset: {df_raw.shape[0]} rows, {df_raw.shape[1]} columns -> {output_path}")
    return df_raw


if __name__ == "__main__":
    generate_raw_dataset()
