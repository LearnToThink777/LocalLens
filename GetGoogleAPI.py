import requests
import json


#def main():
def get_place_reviews(place_id, api_key):

    url = f"https://places.googleapis.com/v1/places/{place_id}?fields=displayName,reviews&languageCode=ko&key={api_key}"

    try:
        payload = {}
        headers = {}
        response = requests.request("GET", url, headers=headers, data=payload)
        response.raise_for_status()  # HTTP 오류 발생 시 예외 발생
        data = response.json()
        index = 1
        for review in data['reviews']:
            print(f"review {index}-----------------")
            print(review['text']['text'].replace("\n", " "))
            index +=1

    except requests.exceptions.RequestException as e:
        print(f"API 요청 오류: {e}")
        return None

def get_place_id(place_name, api_key):
    url = 'https://places.googleapis.com/v1/places:searchText'
    headers = {
        'Content-Type': 'application/json',
        'X-Goog-Api-Key': f"{api_key}",  # API 키
        'X-Goog-FieldMask': 'places.displayName,places.id',
        'languageCode' : 'ko' #잘 작동안함
    }
    data = {
        'textQuery': f'{place_name}'
    }

    response = requests.post(url, headers=headers, data=json.dumps(data))

    if response.status_code == 200:
        data= response.json()
        for place in data['places']:
            return place["id"]
    else:
        print(f'Error: {response.status_code}')
        print(response.text)

if __name__ == "__main__":
    with open("config.json", "r") as f:
        config = json.load(f)
    api_key = config["api_key"]
    place_name = input("리뷰를 검색할 장소를 입력하세요\n")
    place_id = get_place_id(place_name,api_key)
    get_place_reviews(place_id,api_key)
