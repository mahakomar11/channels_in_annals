from difflib import SequenceMatcher
import json


def get_most_similar(word, names, num_of_best=None):
    if num_of_best is None:
        num_of_best = len(names)

    similarities = {}
    for name in names:
        sm = SequenceMatcher(a=word.lower(), b=name.lower())
        similarities[name] = sm.quick_ratio()

    result = sorted(similarities.items(), key=lambda item: item[1], reverse=True)[:num_of_best]
    return [res[0] for res in result]


if __name__ == '__main__':
    user_id = 99649314
    with open('channels.json', 'r') as f:
        users_channels = json.load(f)

    channels = users_channels[str(user_id)]
    chan_names = channels.keys()

    word = 'диета'

    result = get_most_similar(word, chan_names)
    print(result)
