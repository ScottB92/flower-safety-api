import requests

while True:
    flower = input("Enter flower name (or 'quit'): ")
    if flower.lower() == "quit":
        break

    response = requests.post(
        "http://127.0.0.1:5000/flower-check",
        json={"flower": flower}
    )
    print("Bot:", response.json()["response"])
