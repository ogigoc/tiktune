import requests

url = "https://scraptik.p.rapidapi.com/user-posts"

querystring = {"user_id":"7148034888393327622","max_cursor":"0","count":1000} # usernovibeograd
# querystring = {"user_id":"7198556427283579910","max_cursor":"0","count":100} # megahitsrb

headers = {
	"X-RapidAPI-Key": "0451f517a1msh2c9364871a27d44p17a616jsn208f4ae81458",
	"X-RapidAPI-Host": "scraptik.p.rapidapi.com"
}

response = requests.request("GET", url, headers=headers, params=querystring)

print(response.text)