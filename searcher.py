import json
import re


def get_matched(word, names):
    regex = re.compile(word.lower())

    matched = []
    for name in names:
        match = regex.search(name.lower())
        if match is not None:
            matched.append(name)
    return matched
            

if __name__ == '__main__':
    user_id = 99649314
    with open('channels.json', 'r') as f:
        users_channels = json.load(f)

    channels = users_channels[str(user_id)]
    chan_names = channels.keys()

    word = 'диет'

    matched = get_matched(word, chan_names)
    print(matched)
