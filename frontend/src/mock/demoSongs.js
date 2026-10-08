// Generated from backend/apps/catalog/seed/{demo_songs,reference}.yaml.
// Design prototype only: replaced by the real API in stage 4.
export const RELATED_GENRES = {
  "Pop": [
    "Electronic",
    "R&B/Soul",
    "Disco/Funk"
  ],
  "Rock": [
    "Metal",
    "Folk",
    "Jazz/Blues"
  ],
  "Metal": [
    "Rock"
  ],
  "Hip-Hop": [
    "R&B/Soul"
  ],
  "R&B/Soul": [
    "Pop",
    "Hip-Hop",
    "Disco/Funk",
    "Jazz/Blues"
  ],
  "Electronic": [
    "Pop",
    "Disco/Funk"
  ],
  "Disco/Funk": [
    "Pop",
    "R&B/Soul",
    "Electronic"
  ],
  "Country": [
    "Folk"
  ],
  "Folk": [
    "Rock",
    "Country"
  ],
  "Latin": [
    "Reggae"
  ],
  "Reggae": [
    "Latin"
  ],
  "Jazz/Blues": [
    "Rock",
    "R&B/Soul"
  ],
  "Classical/Soundtrack": []
}
export const STYLE_GENRE = {
  "Dance-Pop": "Pop",
  "Synth-Pop": "Pop",
  "Electropop": "Pop",
  "Teen Pop": "Pop",
  "Indie Pop": "Pop",
  "K-Pop": "Pop",
  "Pop Ballad": "Pop",
  "Rock and Roll": "Rock",
  "Classic Rock": "Rock",
  "Hard Rock": "Rock",
  "Glam Rock": "Rock",
  "Soft Rock": "Rock",
  "Pop Rock": "Rock",
  "Punk Rock": "Rock",
  "New Wave": "Rock",
  "Alternative Rock": "Rock",
  "Grunge": "Rock",
  "Indie Rock": "Rock",
  "Progressive Rock": "Rock",
  "Heavy Metal": "Metal",
  "Glam Metal": "Metal",
  "Thrash Metal": "Metal",
  "Nu Metal": "Metal",
  "Pop Rap": "Hip-Hop",
  "Gangsta Rap": "Hip-Hop",
  "Trap": "Hip-Hop",
  "Boom Bap": "Hip-Hop",
  "Soul": "R&B/Soul",
  "Motown": "R&B/Soul",
  "Contemporary R&B": "R&B/Soul",
  "Neo Soul": "R&B/Soul",
  "House": "Electronic",
  "Techno": "Electronic",
  "Trance": "Electronic",
  "Eurodance": "Electronic",
  "EDM": "Electronic",
  "Drum and Bass": "Electronic",
  "Disco": "Disco/Funk",
  "Funk": "Disco/Funk",
  "Nu-Disco": "Disco/Funk",
  "Classic Country": "Country",
  "Country Pop": "Country",
  "Country Rock": "Country",
  "Folk Rock": "Folk",
  "Singer-Songwriter": "Folk",
  "Indie Folk": "Folk",
  "Latin Pop": "Latin",
  "Reggaeton": "Latin",
  "Salsa": "Latin",
  "Bachata": "Latin",
  "Bossa Nova": "Latin",
  "Roots Reggae": "Reggae",
  "Ska": "Reggae",
  "Dancehall": "Reggae",
  "Vocal Jazz": "Jazz/Blues",
  "Swing": "Jazz/Blues",
  "Blues": "Jazz/Blues",
  "Blues Rock": "Jazz/Blues",
  "Film Score": "Classical/Soundtrack",
  "Musical Theatre": "Classical/Soundtrack",
  "Classical Crossover": "Classical/Soundtrack"
}
export const THEME_GROUP = {
  "Falling in Love": "Love",
  "Breakup / Heartbreak": "Love",
  "Passion / Desire": "Love",
  "Jealousy / Infidelity": "Love",
  "Party / Dancing": "Fun",
  "Freedom / Carefree": "Fun",
  "Summer / Holiday": "Fun",
  "Nostalgia / Memories": "Life & Feelings",
  "Loneliness / Sadness": "Life & Feelings",
  "Motivation / Strength": "Life & Feelings",
  "Growing Up / Self-Discovery": "Life & Feelings",
  "Protest / Politics": "Society",
  "War / Peace": "Society",
  "Social Issues": "Society",
  "Money / Success": "Society",
  "Story / Character": "Stories",
  "City / Place": "Stories",
  "Road / Journey": "Stories",
  "Religion / Spirituality": "Special",
  "Death / Loss": "Special",
  "Fantasy / Surreal": "Special"
}
export const SONGS = [
  {
    "id": 1,
    "title": "Bohemian Rhapsody",
    "artist": "Queen",
    "featured": [],
    "members": [
      "Brian May",
      "Freddie Mercury",
      "John Deacon",
      "Roger Taylor"
    ],
    "aliases": [
      "Bohemian Rapsody"
    ],
    "year": 1975,
    "genre": "Rock",
    "styles": [
      "Progressive Rock",
      "Hard Rock"
    ],
    "vocal": "male",
    "themes": [
      "Story / Character",
      "Death / Loss"
    ],
    "country": "United Kingdom",
    "region": "Europe",
    "language": "English",
    "youtube": "fJ9rUzIMcZQ",
    "hints": [
      "It has no chorus at all: it moves from a ballad through an operatic passage to a hard rock section.",
      "A 2018 biopic about the band and its frontman shares its name with this song."
    ]
  },
  {
    "id": 2,
    "title": "Billie Jean",
    "artist": "Michael Jackson",
    "featured": [],
    "members": [
      "Michael Jackson"
    ],
    "aliases": [
      "Billy Jean"
    ],
    "year": 1982,
    "genre": "Pop",
    "styles": [
      "Dance-Pop",
      "Funk"
    ],
    "vocal": "male",
    "themes": [
      "Story / Character"
    ],
    "country": "United States",
    "region": "North America",
    "language": "English",
    "youtube": "Zi_XLOBDo_Y",
    "hints": [
      "It was released in January 1983 as the second single from the singer's sixth studio album.",
      "Performing it on the TV special Motown 25, the singer introduced the moonwalk."
    ]
  },
  {
    "id": 3,
    "title": "Smells Like Teen Spirit",
    "artist": "Nirvana",
    "featured": [],
    "members": [
      "Dave Grohl",
      "Krist Novoselic",
      "Kurt Cobain"
    ],
    "aliases": [
      "Smells Like Teenspirit"
    ],
    "year": 1991,
    "genre": "Rock",
    "styles": [
      "Grunge",
      "Alternative Rock"
    ],
    "vocal": "male",
    "themes": [
      "Growing Up / Self-Discovery",
      "Social Issues"
    ],
    "country": "United States",
    "region": "North America",
    "language": "English",
    "youtube": "hTWKbfoikeg",
    "hints": [
      "It is the opening track and lead single of the band's second album, released in 1991.",
      "Its name comes from a deodorant: a riot grrrl singer wrote on a wall that the band's frontman smelled like it."
    ]
  },
  {
    "id": 4,
    "title": "Despacito",
    "artist": "Luis Fonsi",
    "featured": [
      "Daddy Yankee"
    ],
    "members": [
      "Luis Fonsi",
      "Ramón Ayala"
    ],
    "aliases": [
      "Despasito",
      "Деспасито"
    ],
    "year": 2017,
    "genre": "Latin",
    "styles": [
      "Reggaeton",
      "Latin Pop"
    ],
    "vocal": "male",
    "themes": [
      "Passion / Desire"
    ],
    "country": "Puerto Rico",
    "region": "Latin America",
    "language": "Spanish",
    "youtube": "kJQP7kiw5Fk",
    "hints": [
      "Its music video was shot in the La Perla neighbourhood of Old San Juan.",
      "Its video was the most-viewed on YouTube from 2017 to 2020 and the first to reach three billion views."
    ]
  },
  {
    "id": 5,
    "title": "Rolling in the Deep",
    "artist": "Adele",
    "featured": [],
    "members": [
      "Adele Adkins"
    ],
    "aliases": [
      "Rolling in the Deap"
    ],
    "year": 2010,
    "genre": "R&B/Soul",
    "styles": [
      "Soul"
    ],
    "vocal": "female",
    "themes": [
      "Breakup / Heartbreak"
    ],
    "country": "United Kingdom",
    "region": "Europe",
    "language": "English",
    "youtube": "rYEDA3JcQqw",
    "hints": [
      "It was written with producer Paul Epworth in a single afternoon, shortly after a breakup.",
      "At the 2012 Grammys it won both Record of the Year and Song of the Year."
    ]
  },
  {
    "id": 6,
    "title": "Gangnam Style",
    "artist": "PSY",
    "featured": [],
    "members": [
      "Park Jae-sang"
    ],
    "aliases": [
      "Gangam Style",
      "Oppa Gangnam Style"
    ],
    "year": 2012,
    "genre": "Pop",
    "styles": [
      "K-Pop",
      "Dance-Pop"
    ],
    "vocal": "male",
    "themes": [
      "Party / Dancing",
      "Money / Success"
    ],
    "country": "South Korea",
    "region": "Asia",
    "language": "Korean",
    "youtube": "9bZkp7q19f0",
    "hints": [
      "On 21 December 2012 its video became the first on YouTube to reach one billion views.",
      "Its video made the singer's “invisible horse” dance a worldwide craze."
    ]
  },
  {
    "id": 7,
    "title": "Shape of You",
    "artist": "Ed Sheeran",
    "featured": [],
    "members": [
      "Ed Sheeran"
    ],
    "aliases": [
      "Shape of U"
    ],
    "year": 2017,
    "genre": "Pop",
    "styles": [
      "Dance-Pop",
      "Dancehall"
    ],
    "vocal": "male",
    "themes": [
      "Passion / Desire",
      "Falling in Love"
    ],
    "country": "United Kingdom",
    "region": "Europe",
    "language": "English",
    "youtube": "JGwWNGJdvx8",
    "hints": [
      "It was released on 6 January 2017, the same day as another single from the same album.",
      "It comes from the singer-songwriter's album whose title is the division sign, ÷."
    ]
  },
  {
    "id": 8,
    "title": "Dancing Queen",
    "artist": "ABBA",
    "featured": [],
    "members": [
      "Agnetha Fältskog",
      "Anni-Frid Lyngstad",
      "Benny Andersson",
      "Björn Ulvaeus"
    ],
    "aliases": [
      "Dansing Queen"
    ],
    "year": 1976,
    "genre": "Disco/Funk",
    "styles": [
      "Disco"
    ],
    "vocal": "female",
    "themes": [
      "Party / Dancing"
    ],
    "country": "Sweden",
    "region": "Europe",
    "language": "English",
    "youtube": "xFrGuyw1V8s",
    "hints": [
      "It was first performed live on 18 June 1976 at a gala at the Royal Swedish Opera honouring King Carl XVI Gustaf and his bride-to-be.",
      "The band wanted it to be the follow-up single to their hit “Mamma Mia”."
    ]
  },
  {
    "id": 9,
    "title": "Blinding Lights",
    "artist": "The Weeknd",
    "featured": [],
    "members": [
      "Abel Tesfaye"
    ],
    "aliases": [
      "Blinding Light"
    ],
    "year": 2019,
    "genre": "Pop",
    "styles": [
      "Synth-Pop"
    ],
    "vocal": "male",
    "themes": [
      "Loneliness / Sadness",
      "Passion / Desire"
    ],
    "country": "Canada",
    "region": "North America",
    "language": "English",
    "youtube": "4NRXx6U8ABQ",
    "hints": [
      "Released on 29 November 2019, it is a deliberate callback to the sound of 1980s synth-pop.",
      "The singer performed it during his headlining set at the Super Bowl LV halftime show."
    ]
  },
  {
    "id": 10,
    "title": "No Woman, No Cry",
    "artist": "Bob Marley & The Wailers",
    "featured": [],
    "members": [
      "Bob Marley"
    ],
    "aliases": [
      "No Woman No Cry"
    ],
    "year": 1974,
    "genre": "Reggae",
    "styles": [
      "Roots Reggae"
    ],
    "vocal": "male",
    "themes": [
      "Nostalgia / Memories",
      "Motivation / Strength"
    ],
    "country": "Jamaica",
    "region": "Latin America",
    "language": "English",
    "youtube": "IT8XvzIfi4U",
    "hints": [
      "It first came out on a 1974 studio album, but the live recording made at London's Lyceum Theatre in July 1975 became the best-known version.",
      "The lyrics look back on the singer's youth in Trenchtown, the Kingston neighbourhood where he grew up."
    ]
  },
  {
    "id": 11,
    "title": "Take On Me",
    "artist": "a-ha",
    "featured": [],
    "members": [
      "Magne Furuholmen",
      "Morten Harket",
      "Paul Waaktaar-Savoy"
    ],
    "aliases": [
      "Take on Me",
      "Take Me On"
    ],
    "year": 1984,
    "genre": "Pop",
    "styles": [
      "Synth-Pop",
      "New Wave"
    ],
    "vocal": "male",
    "themes": [
      "Falling in Love"
    ],
    "country": "Norway",
    "region": "Europe",
    "language": "English",
    "youtube": "djV11Xbc914",
    "hints": [
      "Its first version, released in October 1984, failed to chart; a re-recorded version became a hit a year later.",
      "Its award-winning video puts the band inside a live-action pencil-sketch animation."
    ]
  },
  {
    "id": 12,
    "title": "Dreams",
    "artist": "Fleetwood Mac",
    "featured": [],
    "members": [
      "Christine McVie",
      "John McVie",
      "Lindsey Buckingham",
      "Mick Fleetwood",
      "Stevie Nicks"
    ],
    "aliases": [],
    "year": 1977,
    "genre": "Rock",
    "styles": [
      "Soft Rock"
    ],
    "vocal": "female",
    "themes": [
      "Breakup / Heartbreak"
    ],
    "country": "United Kingdom",
    "region": "Europe",
    "language": "English",
    "youtube": "Y3ywicffOj4",
    "hints": [
      "It came out in March 1977 as a single from the band's eleventh studio album.",
      "In 2020 it returned to the charts after a viral TikTok of a man skateboarding to work while drinking cran-raspberry juice."
    ]
  },
  {
    "id": 13,
    "title": "Sweet Dreams (Are Made of This)",
    "artist": "Eurythmics",
    "featured": [],
    "members": [
      "Annie Lennox",
      "Dave Stewart"
    ],
    "aliases": [
      "Sweet Dreams"
    ],
    "year": 1983,
    "genre": "Pop",
    "styles": [
      "Synth-Pop",
      "New Wave"
    ],
    "vocal": "female",
    "themes": [
      "Social Issues",
      "Motivation / Strength"
    ],
    "country": "United Kingdom",
    "region": "Europe",
    "language": "English",
    "youtube": "qeMFqkcPYcg",
    "hints": [
      "It was released in January 1983 as the fourth and final single from the duo's second album.",
      "In its video the singer wears cropped orange hair and a man's business suit."
    ]
  },
  {
    "id": 14,
    "title": "One More Time",
    "artist": "Daft Punk",
    "featured": [],
    "members": [
      "Guy-Manuel de Homem-Christo",
      "Thomas Bangalter"
    ],
    "aliases": [],
    "year": 2000,
    "genre": "Electronic",
    "styles": [
      "House"
    ],
    "vocal": "male",
    "themes": [
      "Party / Dancing"
    ],
    "country": "France",
    "region": "Europe",
    "language": "English",
    "youtube": "FGBhQbmPwH8",
    "hints": [
      "It was released in November 2000 as the lead single from the duo's second studio album.",
      "Its music video is part of the 2003 anime film Interstella 5555."
    ]
  },
  {
    "id": 15,
    "title": "Alors on danse",
    "artist": "Stromae",
    "featured": [],
    "members": [
      "Paul Van Haver"
    ],
    "aliases": [
      "Alors On Dance"
    ],
    "year": 2009,
    "genre": "Electronic",
    "styles": [
      "House"
    ],
    "vocal": "male",
    "themes": [
      "Social Issues",
      "Party / Dancing"
    ],
    "country": "Belgium",
    "region": "Europe",
    "language": "French",
    "youtube": "VHoT4N43jK8",
    "hints": [
      "It came out in Belgium in September 2009 and in the rest of Europe in February 2010.",
      "Its title is French for “and so we dance”."
    ]
  },
  {
    "id": 16,
    "title": "Hips Don't Lie",
    "artist": "Shakira",
    "featured": [
      "Wyclef Jean"
    ],
    "members": [
      "Shakira Mebarak",
      "Wyclef Jean"
    ],
    "aliases": [
      "Hips Dont Lie"
    ],
    "year": 2006,
    "genre": "Latin",
    "styles": [
      "Latin Pop",
      "Reggaeton"
    ],
    "vocal": "mixed",
    "themes": [
      "Passion / Desire",
      "Party / Dancing"
    ],
    "country": "Colombia",
    "region": "Latin America",
    "language": "English",
    "youtube": "DUT5rEU6pqM",
    "hints": [
      "It was released in February 2006 as the lead single of the reissue of the singer's seventh studio album.",
      "A remixed version was sung at the closing ceremony of the 2006 FIFA World Cup in Berlin."
    ]
  },
  {
    "id": 17,
    "title": "Africa",
    "artist": "Toto",
    "featured": [],
    "members": [
      "Bobby Kimball",
      "David Paich",
      "Jeff Porcaro",
      "Steve Lukather",
      "Steve Porcaro"
    ],
    "aliases": [],
    "year": 1982,
    "genre": "Rock",
    "styles": [
      "Soft Rock"
    ],
    "vocal": "male",
    "themes": [
      "City / Place",
      "Falling in Love"
    ],
    "country": "United States",
    "region": "North America",
    "language": "English",
    "youtube": "FTQbiNvZqaY",
    "hints": [
      "It is the tenth and final track of the band's fourth studio album, released in 1982.",
      "Since 2019 a solar-powered sound installation in the Namib desert has played it on an endless loop."
    ]
  },
  {
    "id": 18,
    "title": "Somebody That I Used to Know",
    "artist": "Gotye",
    "featured": [
      "Kimbra"
    ],
    "members": [
      "Kimbra Johnson",
      "Wally De Backer"
    ],
    "aliases": [
      "Somebody That I Use to Know"
    ],
    "year": 2011,
    "genre": "Pop",
    "styles": [
      "Indie Pop"
    ],
    "vocal": "mixed",
    "themes": [
      "Breakup / Heartbreak"
    ],
    "country": "Australia",
    "region": "Oceania",
    "language": "English",
    "youtube": "8UVNT4wvIGY",
    "hints": [
      "It was recorded at the songwriter's parents' house on the Mornington Peninsula in Victoria.",
      "In its video the two singers' skin is painted with geometric patterns that blend into the backdrop."
    ]
  },
  {
    "id": 19,
    "title": "99 Luftballons",
    "artist": "Nena",
    "featured": [],
    "members": [
      "Carlo Karges",
      "Gabriele Kerner",
      "Uwe Fahrenkrog-Petersen"
    ],
    "aliases": [
      "99 Red Balloons",
      "Neunundneunzig Luftballons"
    ],
    "year": 1983,
    "genre": "Rock",
    "styles": [
      "New Wave"
    ],
    "vocal": "female",
    "themes": [
      "War / Peace",
      "Protest / Politics"
    ],
    "country": "Germany",
    "region": "Europe",
    "language": "German",
    "youtube": "Fpu5a0Bl8eY",
    "hints": [
      "It was released in West Germany in March 1983.",
      "The idea came to the band's guitarist at a 1982 Rolling Stones concert in West Berlin, where balloons were released."
    ]
  },
  {
    "id": 20,
    "title": "Enter Sandman",
    "artist": "Metallica",
    "featured": [],
    "members": [
      "James Hetfield",
      "Jason Newsted",
      "Kirk Hammett",
      "Lars Ulrich"
    ],
    "aliases": [],
    "year": 1991,
    "genre": "Metal",
    "styles": [
      "Heavy Metal"
    ],
    "vocal": "male",
    "themes": [
      "Fantasy / Surreal"
    ],
    "country": "United States",
    "region": "North America",
    "language": "English",
    "youtube": "CD-E-LDc384",
    "hints": [
      "It is the opening track and lead single of the band's self-titled fifth album.",
      "Its lyrics are about a child's nightmares."
    ]
  }
]
