from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import pandas as pd
from math import radians, cos, sin, sqrt, atan2

# FastAPI app
app = FastAPI()

# Pydantic model to validate input data
class UserInput(BaseModel):
    user_id: str
    latitude: float
    longitude: float
    cuisine: str
    veg_or_nonveg: str
    sweetness: int
    sourness: int
    spice_level: int
    followers: int

# Function to calculate haversine distance between two lat/lon points
def haversine(lat1, lon1, lat2, lon2):
    R = 6371  # Radius of the Earth in kilometers
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    distance = R * c  # Distance in kilometers
    return distance

# Function to calculate similarity score
def calculate_similarity(user_input, post_row):
    score = 0

    # Cuisine Preference
    if user_input['cuisine'] == post_row['cuisine']:
        score += 50  # Higher priority for cuisine match

    # Veg/Non-Veg Preference
    if user_input['veg_or_nonveg'] == post_row['veg_or_nonveg']:
        score += 30  # Veg/Non-Veg match

    # Location Proximity - Calculate the inverse of the distance
    distance = haversine(user_input['latitude'], user_input['longitude'], post_row['latitude'], post_row['longitude'])
    score += (1 / (distance + 1)) * 100  # Inverse weight for distance

    # Taste Preferences (Sweetness, Sourness, Spiciness)
    taste_diff = abs(user_input['sweetness'] - post_row['sweetness']) + \
                 abs(user_input['sourness'] - post_row['sourness']) + \
                 abs(user_input['spice_level'] - post_row['spice_level'])
    taste_similarity = max(0, 100 - taste_diff)  # Inverse similarity for taste preferences
    score += taste_similarity

    # Number of Likes (add points based on post popularity)
    score += post_row['no_of_likes']  # Add likes as a direct weight

    return score

# Endpoint to recommend top posts
@app.post("/recommend_posts")
async def recommend_posts(user_input: UserInput):
    # Load the posts dataset (assuming post.csv contains relevant data)
    try:
        posts_df = pd.read_csv('post.csv')
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Posts data not found")

    # Convert user input to a dictionary
    user_input_data = user_input.dict()

    # Calculate similarity scores for all posts
    posts_df['similarity_score'] = posts_df.apply(lambda row: calculate_similarity(user_input_data, row), axis=1)

    # Recommend top 30 posts based on the similarity score
    top_30_posts = posts_df.nlargest(30, 'similarity_score')

    return top_30_posts.to_dict(orient='records')

# To run the app, use: uvicorn main:app --reload
