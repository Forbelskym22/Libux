from modules import utils

def run():
    print("\n--- Spouštím konfiguraci Firewallu (iptables) ---")

    if utils.is_service_installed("iptables"):
        print("\n[OK] iptables nalezeny. Spouštím konfiguraci...")
        input("Stiskni Enter pro návrat do hlavního menu...")
    else:
        print("\n[CHYBA] Nástroj 'iptables' není na tomto systému nainstalovaný!")
        input("Stiskni Enter pro návrat do hlavního menu...")