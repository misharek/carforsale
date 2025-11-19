# database/cars_data.py

MODEL_DATABASE = {
    "AUDI": ["A3", "A4", "A6", "A8", "Q3", "Q5", "Q7", "TT", "E-tron", "Q8", "A5", "S4"],
    "BMW": ["X3", "X5", "X6", "3-Series", "5-Series", "7-Series", "1-Series", "I3", "I4", "I8", "M3", "Z4"],
    "MERCEDES-BENZ": ["C-Class", "E-Class", "S-Class", "GLC", "GLE", "GLS", "A-Class", "B-Class", "CLA", "G-Class", "EQC", "Sprinter"],
    "VOLKSWAGEN": ["Passat", "Golf", "Jetta", "Tiguan", "Touareg", "Polo", "Arteon", "Caddy", "Transporter", "ID.4", "Sharan", "Amarok"],
    "FORD": ["Focus", "Fiesta", "Mondeo", "Kuga", "Explorer", "Edge", "Mustang", "Ranger", "Transit", "Puma", "Fusion", "Escort"],
    "RENAULT": ["Megane", "Clio", "Logan", "Duster", "Captur", "Sandero", "Talisman", "Scenic", "Kadjar", "Koleos", "Zoe", "Twingo"],
    "TOYOTA": ["Camry", "Corolla", "RAV4", "Land Cruiser", "Hilux", "Prius", "Yaris", "Auris", "C-HR", "Highlander", "Avensis", "Sequoia"],
    "SKODA": ["Octavia", "Fabia", "Superb", "Kodiaq", "Karoq", "Rapid", "Scala", "Yeti", "Citigo", "Enyaq"],
    "OPEL": ["Astra", "Vectra", "Corsa", "Insignia", "Zafira", "Mokka", "Crossland", "Grandland", "Vivaro", "Combo"],
    "NISSAN": ["Qashqai", "X-Trail", "Juke", "Leaf", "Micra", "Note", "Patrol", "Navara", "Murano", "Rogue", "Sentra"],
    "HYUNDAI": ["Accent", "Elantra", "Sonata", "Tucson", "Santa Fe", "Kona", "I10", "I20", "I30", "Creta", "Genesis"],
    "KIA": ["Sportage", "Rio", "Ceed", "Optima", "Sorento", "Stinger", "Picanto", "K5", "Carnival", "Niro"],
    "MAZDA": ["Mazda3", "Mazda6", "CX-5", "CX-9", "MX-5", "CX-3", "Mazda2", "Tribute"],
    "PEUGEOT": ["308", "508", "2008", "3008", "5008", "208", "107", "Boxer", "Partner"],
    "CITROEN": ["C4", "C5", "C3", "DS4", "Berlingo", "Jumpy", "C-Elysée", "Picasso"],
    "LAND ROVER": ["Range Rover", "Discovery", "Defender", "Evoque", "Freelander", "Velar", "Sport"],
    "LEXUS": ["RX", "NX", "ES", "IS", "GS", "LS", "GX", "LX", "UX"],
    "PORSCHE": ["Cayenne", "Panamera", "911", "Macan", "Taycan", "Boxster", "Cayman"],
    "MITSUBISHI": ["Lancer", "Outlander", "ASX", "Pajero", "Eclipse", "L200", "Galant"],
    "SUBARU": ["Forester", "Outback", "Legacy", "Impreza", "XV", "WRX", "BRZ"],
    "CHEVROLET": ["Aveo", "Lacetti", "Cruze", "Malibu", "Camaro", "Tahoe", "Spark"],
    "HONDA": ["Civic", "CR-V", "Accord", "Jazz", "HR-V", "Pilot", "Legend"],
    "CHRYSLER": ["300C", "Pacifica", "Voyager", "Sebring", "Town & Country"],
    "FIAT": ["500", "Panda", "Tipo", "Punto", "Doblo", "Ducato", "Linea"],
    "SUZUKI": ["Vitara", "SX4", "Swift", "Jimny", "Grand Vitara", "Ignis"],
    "OTHER": ["Інша модель"]
}

BRAND_MAPPING = {
    "VW": "VOLKSWAGEN",
    "VOLKSWAGEN": "VOLKSWAGEN",
    "MB": "MERCEDES-BENZ",
    "MERCEDES": "MERCEDES-BENZ",
    "MERCEDES-BENZ": "MERCEDES-BENZ",
    "BMW": "BMW",
    "B.M.W.": "BMW",
    "B.M.W": "BMW",
    "AUDI": "AUDI",
    "A.U.D.I.": "AUDI",
}

# Автоматичне заповнення мапінгу
for brand_name in MODEL_DATABASE.keys():
    if brand_name not in BRAND_MAPPING:
        BRAND_MAPPING[brand_name] = brand_name

ALLOWED_COLORS = [
    "Чорний", "Білий", "Сірий", "Синій",
    "Червоний", "Зелений", "Коричневий", "Інший"
]

FUEL_TYPES = ["Бензин", "Дизель", "Газ", "Електро", "Гібрид"]