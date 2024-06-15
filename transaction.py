import requests

# Example transaction
result = requests.post('http://127.0.0.1:5000/transactions/new', json={
                    'sender': 'sdkjfbsdlfknsdld',
                    'recipient': 'our_node_id',
                    'amount': 100
                })

print(result.status_code)
print(result.json())
