import sys
import time

print("✅ Salut! Mediul tău virtual funcționează perfect.")
print(f"🐍 Versiunea de Python folosită este: {sys.version.split()[0]}")
print(f"📂 Locația executabilului Python: {sys.executable}")

print("\nFacem un mic test de numărătoare...")
for i in range(1, 4):
    print(f"Test {i}...")
    time.sleep(1)

print("\n🚀 Totul e gata! Poți trece la codul principal cu UDP.")