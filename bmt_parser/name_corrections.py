import re




def are_initials(string):
    match = re.search('^((Dr\.?) ?)?([A-z])(\.| )+([A-z]\.? +)*'
                      '([A-z]\.? *)$', string)
    return True if match else False


def fix_initials(string):
    matches = re.findall('Dr\.? ?|[A-z]\.? *', string)
    result = ' '.join([m.strip() if re.search('\.', m) else (m.strip() + '.')
                       for m in matches])
    return result


def get_initials(string):
    matches = re.findall('\w+\.? *', string)
    matches = [(m.strip()[0] + '.') for m in matches]
    initial = ' '.join(matches)
    return initial


addon = '( [a-z][a-z]+\.)?'
TITLES = [
    '[Pp]rof\.?',
    '[Dd]r\.?'
]
LONGFORMS = {
    '[Dd]o[kc]tor': 'Dr.',
    '[Pp]rofess?or': 'Prof.'
}

TITLES.extend(LONGFORMS.keys())
TITLES = [''.join([t, addon]) for t in TITLES]


def get_title_and_rest(string):
    match = re.match('|'.join(TITLES), string)
    if match:
        title = string[match.start():match.end()]
        # shortening longform
        for l_re in LONGFORMS.keys():
            match_longform = re.match(l_re, title)
            if match_longform:
                longform = title[match_longform.start():match_longform.end()]
                title = title.replace(longform, LONGFORMS[l_re])
                break

        # adding dots
        title = ' '.join([(substr + '.') if not re.search('\.', substr)
                         else substr for substr in title.split(' ')])
        title = title.capitalize()
        return (title, string[match.end():].strip())
    else:
        return ('', string)
