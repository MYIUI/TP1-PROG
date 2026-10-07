from observateurs.observateur import Observateur


class AlerteObserver(Observateur):
    def __init__(self, label_alertes):
        self.label_alertes = label_alertes

    def actualiser(self, sujet):
        donnees = sujet.get_donnees()
        alertes = []

        for ticker, (prix, _) in donnees["prix"].items():
            seuil_haut = donnees["titres"][ticker]["seuil_haut"]
            seuil_bas = donnees["titres"][ticker]["seuil_bas"]

            if prix >= seuil_haut:
                alertes.append(f"⚠️ {ticker} dépasse le seuil haut ({prix:.2f} $ ≥ {seuil_haut:.2f} $)")
            elif prix <= seuil_bas:
                alertes.append(f"⚠️ {ticker} sous le seuil bas ({prix:.2f} $ ≤ {seuil_bas:.2f} $)")

        self.label_alertes.config(
            text="\n".join(alertes) if alertes else "Aucune alerte",
            fg="red" if alertes else "gray",
        )