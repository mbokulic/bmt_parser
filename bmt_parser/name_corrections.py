import re


def remove_strange_chars(string):
    return re.sub('[\x98\x9c]', '', string)


def capitalize(string):
    if are_initials(string):
        return string
    elif any([s.isupper() for s in string.split(' ')]):

        result = ''
        rest = string
        regex = '[\\( -]'
        m = re.search(regex, rest)
        while m:
            result = result + rest[:m.end()].capitalize()
            rest = rest[m.end():]
            m = re.search(regex, rest)
        result = result + rest.capitalize()

        return result
    else:
        return string


def split_and_capitalize(string, sep):
    res = []
    for s in string.split(sep):
        capital = s[0].upper() + s[1:].lower()
        res.append(capital)
    return sep.join(res)


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
    matches = re.findall("[\w']+\.? *", string)
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

# common substitutions: ú=u... do that?


def strip_year(string):
    return re.sub('[, ]+[0-9\?\.\(\)]*-[0-9\?\.\(\)]*.*$', '', string)


def order_names(string):
    '''orders a "surname, name" to "name surname" (removes the comma), or
    returns the string if there is no comma
    '''
    match = re.search(',', string)
    if match:
        split = re.split(',', string)
        split.reverse()
        return ' '.join([s.strip() for s in split])
    else:
        return string
    return string
