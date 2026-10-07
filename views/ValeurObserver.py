from observateurs.observateur import Observateur


class ValeurObserver(Observateur):
    def __init__(self, label_valeur, label_variation):
        self.label_valeur = label_valeur
        self.label_variation = label_variation

    def actualiser(self, sujet):
        donnees = sujet.get_donnees()
        titres = donnees["titres"]

        valeur_totale = 0
        valeur_ouverture = 0
        for ticker, (prix, ouverture) in donnees["prix"].items():
            quantite = titres[ticker]["quantite"]
            valeur_totale += prix * quantite
            valeur_ouverture += ouverture * quantite
        variation = valeur_totale - valeur_ouverture

        self.label_valeur.config(text=f"Valeur totale : {valeur_totale:.2f} $")
        symbole = "▲" if variation >= 0 else "▼"
        self.label_variation.config(
            text=f"{symbole} {abs(variation):.2f} $ depuis l'ouverture",
            fg="green" if variation >= 0 else "red",
        )