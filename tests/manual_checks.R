library(stringr)
library(magrittr)
library(tibble)

options(stringsAsFactors=FALSE)

data = read.csv('output.csv', sep='\t', stringsAsFactors=F)

issue =  data[
    str_detect(data$date, '1925-10') & data$title!='[Advertisement]',
    c('authors', 'title', 'Copy', 'section_id')
]
issue = as_tibble(issue)
issue = issue[order(issue$authors), ]
print(issue, n=nrow(issue))

test = rbind(
    c('Walter Krug', 'Aktive Handelsbilanz'),
    c('Pierre Flouquet', '[Ohne Titel]'),
    c('Otto Nebel', 'Seestück'),
    c('Pierre Flouquet', '[Ohne Titel]'),
    c('Anton Schnack', 'Das Fort'),
    c('Herwarth Walden', 'Der Hilfsregisseur'),
    c('Constantin Brancusi', 'Der Vogel nach'),
    c('Constantin Brancusi', 'Weisse Negerin zwischen'),
    c('Constantin Brancusi', 'Torso eines jungen Menschen zwischen'),
    c('Victor Bourgeois', 'Brüssel ‚Rue le Cubisme‘ vor'),
    c('Hans Arp', 'Weisst du schwarzt du'),
    c('Hans Arp', 'Er nimmt zwei vögel ab'),
    c('Hans Arp', 'hinter jedem erdteil sitzt ein grosser vogel'),
    c('Hans Arp', 'Das mündliche Gerät nimmt nicht notiz …'),
    c('Herwarth Walden', 'Gespräche in Berlin bei Nacht'),
    c('Thomas Ring', 'Riesin Weltstärke'),
    c('Hans Arp', '[Ohne Titel]'),
    c('Otto Nebel', 'Blüh kreis'),
    c('Herwarth Walden', 'Steuerliches'),
    c('Hans Arp', '[Ohne Titel]'),
    c('Walther G. Oschilewski', 'Gedichte'),
    c('Walther G. Oschilewski', 'Die Strasse glänzt …'),
    c('Walther G. Oschilewski', 'Die Nacht singt leis auf …'),
    c('Kurt Liebmann', 'Eingestampt'),
    c('Rudolf Blümner', 'Traum')
)
test = as.data.frame(test)
names(test) = c('author', 'title')

not_issue = test$author %in% issue$authors
test$author[!not_issue]

test = rbind(
    c('Walter Krug', 'Aktive Handelsbilanz'), --
    c('Pierre Flouquet', '[Ohne Titel]'),  --
    c('Otto Nebel', 'Seestück'),
    c('Pierre Flouquet', '[Ohne Titel]'),
    c('Anton Schnack', 'Das Fort'),
    c('Herwarth Walden', 'Der Hilfsregisseur'),
    c('Constantin Brancusi', 'Der Vogel nach'),
    c('Constantin Brancusi', 'Weisse Negerin zwischen'),
    c('Constantin Brancusi', 'Torso eines jungen Menschen zwischen'),
    c('Victor Bourgeois', 'Brüssel ‚Rue le Cubisme‘ vor'),
    c('Hans Arp', 'Weisst du schwarzt du'),
    c('Hans Arp', 'Er nimmt zwei vögel ab'),
    c('Hans Arp', 'hinter jedem erdteil sitzt ein grosser vogel'),
    c('Hans Arp', 'Das mündliche Gerät nimmt nicht notiz …'),
    c('Herwarth Walden', 'Gespräche in Berlin bei Nacht'),
    c('Thomas Ring', 'Riesin Weltstärke'),
    c('Hans Arp', '[Ohne Titel]'),
    c('Otto Nebel', 'Blüh kreis'),
    c('Herwarth Walden', 'Steuerliches'),
    c('Hans Arp', '[Ohne Titel]'),
    c('Walther G. Oschilewski', 'Gedichte'),
    c('Walther G. Oschilewski', 'Die Strasse glänzt …'),
    c('Walther G. Oschilewski', 'Die Nacht singt leis auf …'),
    c('Kurt Liebmann', 'Eingestampt'),
    c('Rudolf Blümner', 'Traum')
)

issue[issue$authors=='Otto Nebel' & issue$title=='Seestück',]$Copy
issue[issue$authors=='Hans Arp' & issue$title=='weisst du schwärzt du',]$Copy
issue[issue$authors=='Kurt Liebmann', ]$section_id