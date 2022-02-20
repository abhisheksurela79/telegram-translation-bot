import json


class Admin:
    def __init__(self):
        with open("Credentials/credentials.json") as file:
            self.data = json.load(file)

    def credentials(self):
        return self.data

    def ignored_words(self, array: list):
        cache = self.data
        try:
            [self.data["telegram"]['ignored_words'].append(each) for each in array if
             each not in self.data["telegram"]['ignored_words']]
            self.write_json(self.data)
            return {"error_code": 0}

        except Exception as e:
            self.write_json(cache)
            return {"error_code": 1}

    def write_json(self, data):
        with open("Credentials/credentials.json", "w") as out:
            out.write(json.dumps(data, indent=4))

