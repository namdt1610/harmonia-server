import requests
import base64

# Điền Client ID và Secret của bạn
CLIENT_ID = "0c5c8c9bdba24c4a962a93fc7a040846"
CLIENT_SECRET = "e3cf377c30c845eba0958e4887b13e55"

def get_spotify_token():
    url = "https://accounts.spotify.com/api/token"
    headers = {
        "Authorization": "Basic " + base64.b64encode(f"{CLIENT_ID}:{CLIENT_SECRET}".encode()).decode(),
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {"grant_type": "client_credentials"}
    
    response = requests.post(url, headers=headers, data=data)
    return response.json().get("access_token")

token = get_spotify_token()
print("Your Spotify Token:", token)
