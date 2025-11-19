# Create a new user named 'Anya' with email 'anya@example.com'
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{"name": "Anya Forger", "email": "anya@example.com"}' \
  http://localhost:5000/users

# Read the user with ID 1
curl http://localhost:5000/users/1

# Read all users
curl http://localhost:5000/users

# Update the name for the user with ID 1
curl -X PUT \
  -H "Content-Type: application/json" \
  -d '{"name": "Twilight"}' \
  http://localhost:5000/users/1

# Delete the user with ID 1
curl -X DELETE \
  http://localhost:5000/users/1