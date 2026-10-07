import tkinter as tk
from modeles.portfolio_sujet import PortfolioSujet
from observateurs.csv_observer import CsvObserver
from observateurs.observateur import Observateur

INTERVALLE_MS = 30000

POLICE = ("Segoe UI", 10)
POLICE_TITRE = ("Segoe UI", 16, "bold")
POLICE_VALEUR = ("Segoe UI", 13, "bold")

def formater_prix(prix, ouverture):
    variation = (prix - ouverture) / ouverture * 100
    symbole = "▲" if variation >= 0 else "▼"
    couleur = "green" if variation >= 0 else "red"
    return f"{prix:.2f} $  {symbole} {abs(variation):.2f}%", couleur


class PrixObserver(Observateur):
    def __init__(self, parent_frame):
        self.frame_prix = parent_frame
        self.labels_prix = {}
        self.frames_prix = {}

    def actualiser(self, sujet) -> None:
        donnees = sujet.get_donnees()
        prix_dict = donnees.get("prix", {})


        tickers_actuels = set(prix_dict.keys())
        tickers_a_supprimer = set(self.frames_prix.keys()) - tickers_actuels
        for ticker in tickers_a_supprimer:
            self.frames_prix[ticker].destroy()
            del self.frames_prix[ticker]
            del self.labels_prix[ticker]


        for ticker, (prix, ouverture) in prix_dict.items():
            if ticker not in self.labels_prix:
                frame = tk.Frame(self.frame_prix)
                frame.pack(fill=tk.X, pady=2)
                tk.Label(frame, text=f"{ticker}:", width=8, font=("Segoe UI", 10, "bold"), anchor="w").pack(side=tk.LEFT)
                label = tk.Label(frame, text="")
                label.pack(side=tk.LEFT)
                self.labels_prix[ticker] = label
                self.frames_prix[ticker] = frame

            texte, couleur = formater_prix(prix, ouverture)
            self.labels_prix[ticker].config(text=texte, fg=couleur)


class ValeurObserver(Observateur):
    def __init__(self, label_valeur, label_variation):
        self.label_valeur = label_valeur
        self.label_variation = label_variation

    def actualiser(self, sujet) -> None:
        donnees = sujet.get_donnees()
        titres = donnees.get("titres", {})
        prix_dict = donnees.get("prix", {})

        if not prix_dict:
            self.label_valeur.config(text="Valeur totale : 0.00 $")
            self.label_variation.config(text="")
            return

        valeur_totale = sum(prix * titres[t]["quantite"] for t, (prix, _) in prix_dict.items() if t in titres)
        valeur_ouverture = sum(ouv * titres[t]["quantite"] for t, (_, ouv) in prix_dict.items() if t in titres)
        variation = valeur_totale - valeur_ouverture

        self.label_valeur.config(text=f"Valeur totale : {valeur_totale:.2f} $")
        symbole = "▲" if variation >= 0 else "▼"
        self.label_variation.config(
            text=f"{symbole} {abs(variation):.2f} $ depuis l'ouverture",
            fg="green" if variation >= 0 else "red",
        )


class AlerteObserver(Observateur):
    def __init__(self, label_alertes):
        self.label_alertes = label_alertes

    def actualiser(self, sujet) -> None:
        donnees = sujet.get_donnees()
        titres = donnees.get("titres", {})
        prix_dict = donnees.get("prix", {})

        alertes = []
        for ticker, (prix, _) in prix_dict.items():
            if ticker in titres:
                seuil_haut = titres[ticker]["seuil_haut"]
                seuil_bas = titres[ticker]["seuil_bas"]
                if prix >= seuil_haut:
                    alertes.append(f"⚠️ {ticker} dépasse le seuil haut ({prix:.2f} $ ≥ {seuil_haut:.2f} $)")
                elif prix <= seuil_bas:
                    alertes.append(f"⚠️ {ticker} sous le seuil bas ({prix:.2f} $ ≤ {seuil_bas:.2f} $)")

        self.label_alertes.config(
            text="\n".join(alertes) if alertes else "Aucune alerte",
            fg="red" if alertes else "gray"
        )




class Application:
    def __init__(self):
        self.fenetre = tk.Tk()
        self.fenetre.title("Portfolio Tracker (Patron Observateur)")
        self.fenetre.resizable(False, False)
        self.fenetre.option_add("*Font", POLICE)

        # 1. Modèle Sujet
        titres_initiaux = {
            "AAPL":  {"quantite": 10, "seuil_haut": 200.0, "seuil_bas": 150.0},
            "GOOGL": {"quantite": 5,  "seuil_haut": 160.0, "seuil_bas": 120.0},
            "MSFT":  {"quantite": 8,  "seuil_haut": 430.0, "seuil_bas": 380.0},
        }
        self.portfolio_sujet = PortfolioSujet(titres_initiaux)


        tk.Label(self.fenetre, text="Portfolio Tracker", font=POLICE_TITRE).pack(pady=10)

        self.frame_prix = tk.LabelFrame(self.fenetre, text="Prix en temps réel", padx=10, pady=10)
        self.frame_prix.pack(fill=tk.X, padx=10, pady=5)

        self._construire_gestion()

        frame_portfolio = tk.LabelFrame(self.fenetre, text="Mon portfolio", padx=10, pady=10)
        frame_portfolio.pack(fill=tk.X, padx=10, pady=5)
        label_valeur = tk.Label(frame_portfolio, text="Valeur totale : calcul en cours...", font=POLICE_VALEUR)
        label_valeur.pack()
        label_variation = tk.Label(frame_portfolio, text="")
        label_variation.pack()

        frame_alertes = tk.LabelFrame(self.fenetre, text="Alertes", padx=10, pady=10)
        frame_alertes.pack(fill=tk.X, padx=10, pady=5)
        label_alertes = tk.Label(frame_alertes, text="Aucune alerte", fg="gray", justify=tk.LEFT, wraplength=380)
        label_alertes.pack(anchor="w")

        self.label_maj = tk.Label(self.fenetre, text="", font=("Segoe UI", 9), fg="gray")
        self.label_maj.pack(pady=5)


        self.prix_obs = PrixObserver(self.frame_prix)
        self.valeur_obs = ValeurObserver(label_valeur, label_variation)
        self.alerte_obs = AlerteObserver(label_alertes)
        self.csv_obs = CsvObserver("portfolio.csv")

        self.portfolio_sujet.abonner(self.prix_obs)
        self.portfolio_sujet.abonner(self.valeur_obs)
        self.portfolio_sujet.abonner(self.alerte_obs)
        self.portfolio_sujet.abonner(self.csv_obs)

        # Lancement
        self.rafraichir()
        self.fenetre.mainloop()

    def _construire_gestion(self):
        frame = tk.LabelFrame(self.fenetre, text="Gérer les titres", padx=10, pady=10)
        frame.pack(fill=tk.X, padx=10, pady=5)

  
        ligne_ajout = tk.Frame(frame)
        ligne_ajout.pack(fill=tk.X)
        self.entry_ticker = self._champ(ligne_ajout, "Ticker", width=8)
        self.entry_quantite = self._champ(ligne_ajout, "Qté", width=5, valeur_defaut="1")
        self.entry_seuil_bas_ajout = self._champ(ligne_ajout, "Alerte basse", width=7)
        self.entry_seuil_haut_ajout = self._champ(ligne_ajout, "Alerte haute", width=7)
        tk.Button(ligne_ajout, text="Ajouter", command=self.ajouter_titre).pack(side=tk.LEFT)


        ligne_liste = tk.Frame(frame)
        ligne_liste.pack(fill=tk.X, pady=(5, 0))
        self.listbox_titres = tk.Listbox(ligne_liste, height=4, exportselection=False)
        self.listbox_titres.pack(side=tk.LEFT, fill=tk.X, expand=True)
        for ticker in self.portfolio_sujet.titres:
            self.listbox_titres.insert(tk.END, ticker)
        tk.Button(ligne_liste, text="Retirer", command=self.retirer_titre).pack(side=tk.LEFT, padx=(5, 0), anchor="n")


        ligne_modif = tk.Frame(frame)
        ligne_modif.pack(fill=tk.X, pady=(8, 0))
        tk.Label(ligne_modif, text="Sélection →").pack(side=tk.LEFT)
        self.entry_nouvelle_quantite = self._champ(ligne_modif, "Qté", width=5)
        self.entry_nouveau_seuil_bas = self._champ(ligne_modif, "Alerte basse", width=7)
        self.entry_nouveau_seuil_haut = self._champ(ligne_modif, "Alerte haute", width=7)
        tk.Button(ligne_modif, text="Modifier sélection", command=self.modifier_selection).pack(side=tk.LEFT)

        self.label_statut_titres = tk.Label(frame, text="", font=("Segoe UI", 9), fg="gray")
        self.label_statut_titres.pack(anchor="w", pady=(5, 0))

    def _champ(self, parent, texte, width, valeur_defaut=""):
        tk.Label(parent, text=f"{texte}:").pack(side=tk.LEFT)
        entry = tk.Entry(parent, width=width)
        if valeur_defaut:
            entry.insert(0, valeur_defaut)
        entry.pack(side=tk.LEFT, padx=(2, 8))
        return entry

    def _statut(self, texte, couleur):
        self.label_statut_titres.config(text=texte, fg=couleur)

    def ajouter_titre(self):
        ticker = self.entry_ticker.get().strip().upper()
        if not ticker:
            return
        if ticker in self.portfolio_sujet.titres:
            self._statut(f"{ticker} est déjà dans le portfolio.", "orange")
            return
        try:
            quantite = int(self.entry_quantite.get().strip())
            if quantite <= 0:
                raise ValueError
        except ValueError:
            self._statut("La quantité doit être un entier positif.", "red")
            return

        texte_bas = self.entry_seuil_bas_ajout.get().strip()
        texte_haut = self.entry_seuil_haut_ajout.get().strip()
        seuil_bas = float(texte_bas) if texte_bas else None
        seuil_haut = float(texte_haut) if texte_haut else None

        try:
            self.portfolio_sujet.ajouter_titre(ticker, quantite, seuil_bas, seuil_haut)
            self.listbox_titres.insert(tk.END, ticker)
            self._statut(f"{ticker} ajouté au portfolio.", "green")
        except Exception as e:
            self._statut(f"Erreur lors de l'ajout de {ticker}: {e}", "red")

    def retirer_titre(self):
        selection = self.listbox_titres.curselection()
        if not selection:
            self._statut("Sélectionnez un titre à retirer.", "orange")
            return
        index = selection[0]
        ticker = self.listbox_titres.get(index)

        self.portfolio_sujet.retirer_titre(ticker)
        self.listbox_titres.delete(index)
        self._statut(f"{ticker} retiré.", "gray")

    def modifier_selection(self):
        selection = self.listbox_titres.curselection()
        if not selection:
            self._statut("Sélectionnez un titre à modifier.", "orange")
            return
        ticker = self.listbox_titres.get(selection[0])

        texte_qte = self.entry_nouvelle_quantite.get().strip()
        texte_bas = self.entry_nouveau_seuil_bas.get().strip()
        texte_haut = self.entry_nouveau_seuil_haut.get().strip()

        qte = int(texte_qte) if texte_qte else None
        s_bas = float(texte_bas) if texte_bas else None
        s_haut = float(texte_haut) if texte_haut else None

        self.portfolio_sujet.modifier_titre(ticker, qte, s_bas, s_haut)
        self._statut(f"{ticker} mis à jour.", "green")

    def rafraichir(self):
        try:
            self.portfolio_sujet.mettre_a_jour_prix()
            horodatage = self.portfolio_sujet.get_donnees().get("horodatage")
            self.label_maj.config(text=f"Dernière mise à jour : {horodatage}", fg="gray")
        except Exception as e:
            self.label_maj.config(text=f"Erreur : {e}", fg="red")

        self.fenetre.after(INTERVALLE_MS, self.rafraichir)


if __name__ == "__main__":
    Application()