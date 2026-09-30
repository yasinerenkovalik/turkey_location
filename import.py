import json
import urllib.request
import ssl
import certifi

# --------------------------------------------------
# AYARLAR
# --------------------------------------------------

PROVINCE_URL = (
    "https://raw.githubusercontent.com/"
    "open-admin-data/turkey-administrative-divisions/"
    "master/data/all-province.json"
)

DISTRICT_URL = (
    "https://raw.githubusercontent.com/"
    "open-admin-data/turkey-administrative-divisions/"
    "master/data/all-district.json"
)

OUTPUT_FILE = "turkey_locations.sql"


# --------------------------------------------------
# VERİ İNDİRME
# --------------------------------------------------

def download_json(url):
    print(f"İndiriliyor: {url}")

    context = ssl.create_default_context(
        cafile=certifi.where()
    )

    with urllib.request.urlopen(url, context=context) as response:
        return json.load(response)


# --------------------------------------------------
# SQL TEXT ESCAPE
# --------------------------------------------------

def escape_sql(value):
    return str(value).replace("'", "''")


# --------------------------------------------------
# VERİLERİ AL
# --------------------------------------------------

print("Türkiye il ve ilçe verileri alınıyor...")

provinces = download_json(PROVINCE_URL)
districts = download_json(DISTRICT_URL)

print()
print(f"İl sayısı: {len(provinces)}")
print(f"İlçe sayısı: {len(districts)}")
print()


# --------------------------------------------------
# İL ID EŞLEŞMESİ
#
# TUR001 -> 1
# TUR002 -> 2
# ...
# TUR081 -> 81
# --------------------------------------------------

province_map = {}

for index, city in enumerate(provinces, start=1):
    original_id = city["id"]

    province_map[original_id] = index


# --------------------------------------------------
# SQL OLUŞTUR
# --------------------------------------------------

sql = []

sql.append("-- =============================================")
sql.append("-- HappyDay Türkiye İl / İlçe Verileri")
sql.append("-- 81 İl + 973 İlçe")
sql.append("-- =============================================")
sql.append("")
sql.append("BEGIN;")
sql.append("")


# --------------------------------------------------
# CITIES
# --------------------------------------------------

sql.append("-- =============================================")
sql.append("-- CITIES")
sql.append("-- =============================================")
sql.append("")

for index, city in enumerate(provinces, start=1):

    city_name = city["name"]["local"]
    city_name = escape_sql(city_name)

    sql.append(
        f'INSERT INTO "Cities" ("Id", "CityName") '
        f"VALUES ({index}, '{city_name}') "
        f'ON CONFLICT ("Id") DO UPDATE SET '
        f'"CityName" = EXCLUDED."CityName";'
    )


sql.append("")


# --------------------------------------------------
# DISTRICTS
# --------------------------------------------------

sql.append("-- =============================================")
sql.append("-- DISTRICTS")
sql.append("-- =============================================")
sql.append("")


district_id = 1

for district in districts:

    district_name = district["name"]["local"]
    district_name = escape_sql(district_name)

    original_city_id = district["parent"]["id"]

    city_id = province_map.get(original_city_id)

    if city_id is None:
        print(
            f"UYARI: Şehir bulunamadı: "
            f"{original_city_id} - {district_name}"
        )
        continue

    sql.append(
        f'INSERT INTO "Districts" '
        f'("Id", "DistrictName", "CityId") '
        f"VALUES "
        f"({district_id}, '{district_name}', {city_id}) "
        f'ON CONFLICT ("Id") DO UPDATE SET '
        f'"DistrictName" = EXCLUDED."DistrictName", '
        f'"CityId" = EXCLUDED."CityId";'
    )

    district_id += 1


# --------------------------------------------------
# BİTİR
# --------------------------------------------------

sql.append("")
sql.append("COMMIT;")
sql.append("")

sql.append("-- =============================================")
sql.append("-- KONTROL")
sql.append("-- =============================================")
sql.append("")

sql.append('SELECT COUNT(*) AS city_count FROM "Cities";')
sql.append('SELECT COUNT(*) AS district_count FROM "Districts";')


# --------------------------------------------------
# DOSYAYI YAZ
# --------------------------------------------------

with open(
    OUTPUT_FILE,
    "w",
    encoding="utf-8"
) as file:

    file.write("\n".join(sql))


# --------------------------------------------------
# SONUÇ
# --------------------------------------------------

print("---------------------------------------------")
print("BAŞARILI")
print("---------------------------------------------")
print(f"İl     : {len(provinces)}")
print(f"İlçe   : {len(districts)}")
print(f"Dosya  : {OUTPUT_FILE}")
print("---------------------------------------------")