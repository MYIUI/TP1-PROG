import tkinter as tk
from modeles.portfolio_sujet import PortfolioSujet
from observateurs.csv_observer import CsvObserver
from views.PrixObserver import PrixObserver
from views.ValeurObserver import ValeurObserver
from views.AlerteObserver import AlerteObserver

INTERVALLE_MS = 30000  # rafraîchissement des prix (30 secondes)

POLICE = ("Segoe UI", 10)
POLICE_TITRE = ("Segoe UI", 16, "bold")
POLICE_VALEUR = ("Segoe UI", 13, "bold")


def entier_positif(texte):
    """Convertit `texte` en entier strictement positif, ou lève ValueError."""
    valeur = int(texte)
    if valeur <= 0:
        raise ValueError
    return valeur


def flottant_positif(texte):
    """Convertit `texte` en nombre décimal strictement positif, ou lève ValueError."""
    valeur = float(texte)
    if valeur <= 0:
        raise ValueError
    return valeur


class Application:
    def __init__(self):
        self.fenetre = tk.Tk()
        self.fenetre.title("Portfolio Tracker (Patron Observateur)")
        self.fenetre.resizable(False, False)
        self.fenetre.option_add("*Font", POLICE)

        # 1. Sujet, l'état du portfolio   
        titres_initiaux = {
            "AAPL":  {"quantite": 10, "seuil_haut": 200.0, "seuil_bas": 150.0},
            "GOOGL": {"quantite": 5,  "seuil_haut": 160.0, "seuil_bas": 120.0},
            "MSFT":  {"quantite": 8,  "seuil_haut": 430.0, "seuil_bas": 380.0},
        }
        self.portfolio_sujet = PortfolioSujet(titres_initiaux)

        # L'interface
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

        # Observateurs
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
        """Section "Gérer les titres" : ajout, liste (avec retrait) et modification."""
        frame = tk.LabelFrame(self.fenetre, text="Gérer les titres", padx=10, pady=10)
        frame.pack(fill=tk.X, padx=10, pady=5)

        # formulaire d'ajout
        ligne_ajout = tk.Frame(frame)
        ligne_ajout.pack(fill=tk.X)
        self.entry_ticker = self._champ(ligne_ajout, "Ticker", width=8)
        self.entry_quantite = self._champ(ligne_ajout, "Qté", width=5, valeur_defaut="1")
        self.entry_seuil_bas_ajout = self._champ(ligne_ajout, "Alerte basse", width=7)
        self.entry_seuil_haut_ajout = self._champ(ligne_ajout, "Alerte haute", width=7)
        tk.Button(ligne_ajout, text="Ajouter", command=self.ajouter_titre).pack(side=tk.LEFT)

        tk.Label(
            frame,
            text="(Alertes optionnelles : si vides, calculées à ±20% du prix actuel)",
            font=("Segoe UI", 8), fg="gray"
        ).pack(anchor="w", pady=(2, 5))

        # liste des titres + bouton Retirer
        ligne_liste = tk.Frame(frame)
        ligne_liste.pack(fill=tk.X)
        self.listbox_titres = tk.Listbox(ligne_liste, height=4, exportselection=False)
        self.listbox_titres.pack(side=tk.LEFT, fill=tk.X, expand=True)
        for ticker in self.portfolio_sujet.titres:
            self.listbox_titres.insert(tk.END, self._texte_listbox(ticker))
        tk.Button(ligne_liste, text="Retirer", command=self.retirer_titre).pack(side=tk.LEFT, padx=(5, 0), anchor="n")

        # modification du titre sélectionné
        ligne_modif = tk.Frame(frame)
        ligne_modif.pack(fill=tk.X, pady=(8, 0))
        tk.Label(ligne_modif, text="Sélection →").pack(side=tk.LEFT)
        self.entry_nouvelle_quantite = self._champ(ligne_modif, "Qté", width=5)
        self.entry_nouveau_seuil_bas = self._champ(ligne_modif, "Alerte basse", width=7)
        self.entry_nouveau_seuil_haut = self._champ(ligne_modif, "Alerte haute", width=7)
        tk.Button(ligne_modif, text="Modifier sélection", command=self.modifier_selection).pack(side=tk.LEFT)

        # Message de statut (succès ou erreur)
        self.label_statut_titres = tk.Label(frame, text="", font=("Segoe UI", 9), fg="gray")
        self.label_statut_titres.pack(anchor="w", pady=(5, 0))

    def _champ(self, parent, texte, width, valeur_defaut=""):
        """Ajoute un couple Label + Entry à `parent` et retourne l'Entry."""
        tk.Label(parent, text=f"{texte}:").pack(side=tk.LEFT)
        entry = tk.Entry(parent, width=width)
        if valeur_defaut:
            entry.insert(0, valeur_defaut)
        entry.pack(side=tk.LEFT, padx=(2, 8))
        return entry

    def _texte_listbox(self, ticker):
        """Texte affiché dans la liste : ticker, quantité et seuils d'alerte."""
        infos = self.portfolio_sujet.titres[ticker]
        return (
            f"{ticker} — {infos['quantite']} action(s) "
            f"(alerte : {infos['seuil_bas']:.2f} $ / {infos['seuil_haut']:.2f} $)"
        )

    def _ticker_selectionne(self):
        """Retourne (index, ticker) du titre sélectionné dans la liste, ou None.
        Le ticker est la partie du texte avant le tiret " — "."""
        selection = self.listbox_titres.curselection()
        if not selection:
            return None
        index = selection[0]
        ticker = self.listbox_titres.get(index).split(" — ")[0]
        return index, ticker

    def _statut(self, texte, couleur):
        self.label_statut_titres.config(text=texte, fg=couleur)



    def ajouter_titre(self):
        """Valide le formulaire, puis demande au sujet d'ajouter le titre.
        Le sujet notifie ensuite tous les observateurs."""
        ticker = self.entry_ticker.get().strip().upper()
        if not ticker:
            return
        if ticker in self.portfolio_sujet.titres:
            self._statut(f"{ticker} est déjà dans le portfolio.", "orange")
            return

        try:
            quantite = entier_positif(self.entry_quantite.get().strip())
        except ValueError:
            self._statut("La quantité doit être un nombre entier positif.", "red")
            return

        texte_bas = self.entry_seuil_bas_ajout.get().strip()
        texte_haut = self.entry_seuil_haut_ajout.get().strip()
        try:
            seuil_bas = flottant_positif(texte_bas) if texte_bas else None
            seuil_haut = flottant_positif(texte_haut) if texte_haut else None
        except ValueError:
            self._statut("Les alertes doivent être des nombres positifs.", "red")
            return
        if seuil_bas is not None and seuil_haut is not None and seuil_bas >= seuil_haut:
            self._statut("L'alerte basse doit être inférieure à l'alerte haute.", "red")
            return

        try:
            self.portfolio_sujet.ajouter_titre(ticker, quantite, seuil_bas, seuil_haut)
        except Exception:
            self._statut(f"Le titre '{ticker}' n'existe pas.", "red")
            return

        # Mise à jour de la liste et réinitialisation du formulaire
        self.listbox_titres.insert(tk.END, self._texte_listbox(ticker))
        for entry, valeur in (
            (self.entry_ticker, ""), (self.entry_quantite, "1"),
            (self.entry_seuil_bas_ajout, ""), (self.entry_seuil_haut_ajout, ""),
        ):
            entry.delete(0, tk.END)
            entry.insert(0, valeur)
        self._statut(f"{ticker} ajouté au portfolio ({quantite} action(s)).", "green")

    def retirer_titre(self):
        """Retire le titre sélectionné : le sujet met à jour son état et notifie."""
        selectionne = self._ticker_selectionne()
        if selectionne is None:
            self._statut("Sélectionnez un titre à retirer.", "orange")
            return
        index, ticker = selectionne

        self.portfolio_sujet.retirer_titre(ticker)
        self.listbox_titres.delete(index)
        self._statut(f"{ticker} retiré du portfolio.", "gray")

    def modifier_selection(self):
        """Modifie la quantité et/ou les seuils du titre sélectionné.
        Chaque champ est optionnel : seuls ceux remplis sont modifiés."""
        selectionne = self._ticker_selectionne()
        if selectionne is None:
            self._statut("Sélectionnez un titre à modifier.", "orange")
            return
        index, ticker = selectionne

        texte_qte = self.entry_nouvelle_quantite.get().strip()
        texte_bas = self.entry_nouveau_seuil_bas.get().strip()
        texte_haut = self.entry_nouveau_seuil_haut.get().strip()
        if not texte_qte and not texte_bas and not texte_haut:
            self._statut("Entrez une nouvelle quantité et/ou de nouvelles alertes.", "orange")
            return

        try:
            qte = entier_positif(texte_qte) if texte_qte else None
            s_bas = flottant_positif(texte_bas) if texte_bas else None
            s_haut = flottant_positif(texte_haut) if texte_haut else None
        except ValueError:
            self._statut("La quantité et les alertes doivent être des nombres positifs.", "red")
            return

        # Cohérence des seuils
        infos = self.portfolio_sujet.titres[ticker]
        bas_final = s_bas if s_bas is not None else infos["seuil_bas"]
        haut_final = s_haut if s_haut is not None else infos["seuil_haut"]
        if bas_final >= haut_final:
            self._statut("L'alerte basse doit être inférieure à l'alerte haute.", "red")
            return

        self.portfolio_sujet.modifier_titre(ticker, qte, s_bas, s_haut)

        # Rafraîchit la ligne de la liste et garde la sélection
        self.listbox_titres.delete(index)
        self.listbox_titres.insert(index, self._texte_listbox(ticker))
        self.listbox_titres.selection_set(index)
        for entry in (self.entry_nouvelle_quantite, self.entry_nouveau_seuil_bas, self.entry_nouveau_seuil_haut):
            entry.delete(0, tk.END)
        self._statut(f"{ticker} mis à jour.", "green")



    def rafraichir(self):
        """Cycle principal : le sujet récupère les prix puis notifie les observateurs.
        Se replanifie lui-même, que le cycle ait réussi ou échoué."""
        try:
            self.portfolio_sujet.mettre_a_jour_prix()
            horodatage = self.portfolio_sujet.get_donnees().get("horodatage")
            self.label_maj.config(text=f"Dernière mise à jour : {horodatage}", fg="gray")
        except Exception as e:
            self.label_maj.config(text=f"Erreur : {e}", fg="red")

        self.fenetre.after(INTERVALLE_MS, self.rafraichir)


if __name__ == "__main__":
    Application()