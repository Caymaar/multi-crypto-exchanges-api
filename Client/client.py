import requests
from datetime import datetime
import json

class SimpleAPIClient:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.token = None
    
    def login(self, username: str, password: str) -> bool:
        """Login and get JWT token"""
        try:
            response = requests.post(
                f"{self.base_url}/login",
                json={"username": username, "password": password}
            )
            
            # Try to parse response as JSON
            try:
                response_data = response.json()
            except json.JSONDecodeError:
                print(f"Server returned invalid JSON. Status code: {response.status_code}")
                print(f"Response text: {response.text}")
                return False
            
            if response.status_code == 200:
                self.token = response_data["access_token"]
                return True
                
            error_detail = response_data.get('detail', 'Unknown error')
            print(f"Login failed: {error_detail}")
            return False
            
        except requests.exceptions.ConnectionError:
            print(f"Connection error: Could not connect to {self.base_url}")
            return False
        except Exception as e:
            print(f"Login error: {str(e)}")
            return False
    
    def get_secure_data(self):
        """Access protected endpoint"""
        if not self.token:
            print("Not logged in!")
            return None
        
        try:
            response = requests.get(
                f"{self.base_url}/secure",
                headers={"Authorization": f"Bearer {self.token}"}
            )
            if response.status_code != 200:
                print(f"Error accessing secure endpoint. Status code: {response.status_code}")
                try:
                    error_detail = response.json().get('detail', 'Unknown error')
                    print(f"Error detail: {error_detail}")
                except:
                    print(f"Response text: {response.text}")
                return None
                
            return response.json()
            
        except requests.exceptions.ConnectionError:
            print(f"Connection error: Could not connect to {self.base_url}")
            return None
        except Exception as e:
            print(f"Error accessing secure endpoint: {str(e)}")
            return None

def test_api():
    client = SimpleAPIClient()
    
    print("\n1. Testing with valid credentials...")
    if client.login("admin", "admin123"):
        print("Login successful!")
        data = client.get_secure_data()
        print(f"Secure data: {data}")
    
    print("\n2. Testing with invalid credentials...")
    if not client.login("alice", "wrong_password"):
        print("Login correctly failed!")
    
    print("\n3. Testing secure endpoint without login...")
    new_client = SimpleAPIClient()
    data = new_client.get_secure_data()
    print(f"Secure endpoint without token: {data}")

if __name__ == "__main__":
    test_api()