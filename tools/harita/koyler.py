import json
X0,Y0=137,107
# eski haritadaki köy noktaları (orijinal piksel)
K={"Acıpayam":(842,616),"Yukarı":(824.5,642),"Akalan":(839.2,748),"Alaattin":(775.5,521.3),"Apa":(839.5,453.6),
"Bademli":(1161.1,658.7),"Mevlütler":(741.6,710.9),"Pınaryazı":(853.5,687.7),"Darıveren":(1025.8,961.3),"Dedebağı":(993.9,915.1),
"Eskiköy":(817.7,1103.6),"Yeşilyuva":(968.4,304.9),"Güneyköy":(666,1021.9),"Karahüyük":(926.7,455.2),"Karaismailler":(467.6,1271.1),
"Kurtlar":(1152.5,544.4),"Kuzören":(843,1031.5),"Köke":(892.5,815.3),"Ovayurt":(825.7,443.5),"Yassıhüyük":(797.9,443.7),
"Suçatı":(469.9,1407),"Uçarı":(968.5,518.8),"Yazır":(1196,766.5),"Yeniköy":(975.5,654.4),"Yumrutaş":(1070.5,706.1),
"Yeşildere":(1069.5,664.1),"Çakırköy":(817.4,922.1),"Örenköy":(707.1,870.8),"Sırçalık":(1074,437.3),"Pınarbaşı":(1139.5,416.9),
"Corum":(1058.2,523.5),"Oğuzköy":(816.5,562.3),"Gedikli":(913,599.6),"Gümüş":(1193.6,787.8),"Çubukçular":(709.5,786.3),
"Bedirbey":(970.1,790.1),"Kumafşarı":(1125,847.7),"Kelekçi":(750.8,1034.2),"Olukbaşı":(618,1075.1),"Akşar":(692.2,1105.2),
"Aliveren":(962.9,1097.7),"Benlik":(565.1,1125.6),"Gölcük":(605.7,1196.7),"Alcı":(546.8,1245),"Çiftlikköy":(552.6,1216.7),
"Sandalcık":(384.5,1350.9),"Yolçatı":(411.3,1365.5),"Kuyucak":(908.2,336.1),"Avşar":(991.8,401),"Kırca":(824,518.2),
"Dodurgalar":(1193.8,721.7),"Boğazdere":(752.1,1098.9),"Hacıkurtlar":(759.1,1152.7),"Hisarköy":(482.3,1182.9)}
json.dump({k:[round(x-X0,1),round(y-Y0,1)] for k,(x,y) in K.items()},open('/home/user/acipayam-site/data/harita-koyler.json','w'),ensure_ascii=False,indent=0)
print(len(K))
