# Fu-Lin lisans anahtarı üretici (SATILAN bilgisayara verilmez, sende kalır)
# Kullanim: python lisans_uret.py "KURULUM KODU"
import sys
from klinik.lisans import lisans_anahtari_uret

kod = " ".join(sys.argv[1:]).strip() if len(sys.argv) > 1 else input("Kurulum kodu: ").strip()
if not kod:
    print("Kurulum kodu gerekli.")
else:
    print("Kod     :", kod.upper())
    print("Anahtar :", lisans_anahtari_uret(kod))
