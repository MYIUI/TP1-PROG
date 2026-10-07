from observers.observer import Observer

class CsvObserver(Observer):
    def __init__(self, chemin_fichier="portfolio.csv"):
        self.chemin_fichier = chemin_fichier

    def actualiser(self, sujet) -> None:
        donnees = sujet.get_donnees()
        horodatage = donnees.get("horodatage")
        prix_dict = donnees.get("prix", {})

        if not prix_dict:
            return

        with open(self.chemin_fichier, "a", encoding="utf-8") as f:
            for ticker, (prix, ouverture) in prix_dict.items():
                f.write(f"{horodatage},{ticker},{prix:.2f},{ouverture:.2f}\n")