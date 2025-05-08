
prediction_url="https://ai-ls-vqr-qna.cognitiveservices.azure.com/"
key="5spR1Gi9VIWkMpAyrjaudgROneena0e5fTe09nCqyew9aihjMumvJQQJ99BEACYeBjFXJ3w3AAAaACOGdE4P"

curl -X POST $prediction_url -H "Ocp-Apim-Subscription-Key: $key" -H "Content-Type: application/json" -d "{'question': 'What is a learning Path?' }"

