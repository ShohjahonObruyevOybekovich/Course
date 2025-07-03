from django.core.management.base import BaseCommand
from idioms.models import Idioms

class Command(BaseCommand):
    help = "Seed idioms into the database"

    def handle(self, *args, **kwargs):
        ideom = [
            {"text": "Yangi kun – yangi imkoniyatlar! Keling, bugunni foydali boshlaylik!", "time": "09:00"},
            {"text": "Erta turgan – maqsadga yaqin! Bugun o‘z ustimizda ishlashni unutmang!", "time": "09:00"},
            {"text": "Tongda qilgan kichik mashg‘ulot – katta natijaga olib boradi!", "time": "09:00"},
            {"text": "Harakat bugundan boshlanadi! Qadam tashlaylik!", "time": "09:00"},
            {"text": "Miya eng faol payti – hozir! Vaqtingni to‘g‘ri ishlat!", "time": "09:00"},
            {"text": "Tonggi rejang: 1. Ko‘z ochish. 2. O‘rganish. 3. G‘alaba qilish!", "time": "09:00"},
            {"text": "Sekin harakat ham yomon emas. Har kuni oz-ozdan – kuchliroq bo‘lasan!", "time": "09:00"},
            {"text": "Ich sag nur eins (Men faqat bitta gap aytaman): Bugun 3 ta yangi so‘z – keyin TikTokga ruxsat!",
             "time": "09:00"},

            {"text": "Bir oz dam olding, endi esa fikring tiniq – o‘rganish uchun ajoyib vaqt!", "time": "12:00"},
            {"text": "Kichik mashqlar katta o‘zgarishlarga olib keladi!", "time": "12:00"},
            {"text": "Bugun yana bir yangi narsa o‘zlashtirib olishing mumkin!", "time": "12:00"},
            {"text": "Ishlar orasida o‘zingga vaqt ajrat – maqsading yo‘qolib qolmasin!", "time": "12:00"},
            {"text": "Kundalik odatlar – yutuqlarning asosidir!", "time": "12:00"},
            {"text": "Obeddan keyin: 'Bir soat dam olaman' deyish – Netflixcha 5 soat 😅", "time": "12:00"},
            {"text": "Sen: dars qilaman. Telefon: keling, tiktok qilib ko‘ramiz!", "time": "12:00"},
            {"text": "Ekranga qaradingmi? Demak dars ham qilishing mumkin.", "time": "12:00"},

            {"text": "Kechani foyda bilan yakunlashni unutmang – bugungi rejalaringizni yodda tuting!",
             "time": "19:00"},
            {"text": "Kun tugayapti, lekin maqsad hali kuchli! Oxirigacha bardavom bo‘ling!", "time": "19:00"},
            {"text": "Yotishdan oldin miyani biroz faollashtirib olaylik!", "time": "19:00"},
            {"text": "Bir kun – bir yutuq! Bugunni ortda qoldirmay, kichik mashq qil!", "time": "19:00"},
            {"text": "Bugun qilgan kichik mehnating – ertangi osonlik garovi!", "time": "19:00"},
            {"text": "Kechqurun dars qilding – ertaga o‘zingga rahmat aytasan! Ishon!", "time": "19:00"},
            {"text": "Yotganingda vijdon: bugun hech narsa o‘rganmading…", "time": "19:00"}
        ]

        count = 0
        for item in ideom:
            Idioms.objects.create(text=item["text"], time=item["time"])
            count += 1

        self.stdout.write(self.style.SUCCESS(f"✅ {count} idioms created."))
