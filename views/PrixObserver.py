import tkinter as tk
from observateurs.observateur import Observateur


def formater_prix(prix, ouverture):
    """Retourne le texte et la couleur à afficher pour un prix et sa variation."""
    variation = (prix - ouverture) / ouverture * 100
    symbole = "▲" if variation >= 0 else "▼"
    couleur = "green" if variation >= 0 else "red"
    return f"{prix:.2f} $  {symbole} {abs(variation):.2f}%", couleur


class PrixObserver(Observateur):
    def __init__(self, frame_prix):
        self.frame_prix = frame_prix
        self.frames_prix = {}   # ticker -> Frame de la ligne
        self.labels_prix = {}   # ticker -> Label du prix

    def actualiser(self, sujet):
        donnees = sujet.get_donnees()
        tickers = donnees["titres"]

        # Retirer les lignes des titres qui n'existent plus
        for ticker in list(self.frames_prix):
            if ticker not in tickers:
                self.frames_prix.pop(ticker).destroy()
                self.labels_prix.pop(ticker)

        # Créer les lignes des nouveaux titres
        for ticker in tickers:
            if ticker not in self.frames_prix:
                self._creer_ligne_prix(ticker)

        #Mettre à jour le prix et la couleur de chaque ligne
        for ticker, (prix, ouverture) in donnees["prix"].items():
            if ticker in self.labels_prix:
                texte, couleur = formater_prix(prix, ouverture)
                self.labels_prix[ticker].config(text=texte, fg=couleur)

    def _creer_ligne_prix(self, ticker):
        frame = tk.Frame(self.frame_prix)
        frame.pack(fill=tk.X, pady=2)
        tk.Label(frame, text=f"{ticker}:", width=8, font=("Segoe UI", 10, "bold"), anchor="w").pack(side=tk.LEFT)
        label = tk.Label(frame, text="Chargement...")
        label.pack(side=tk.LEFT)
        self.frames_prix[ticker] = frame
        self.labels_prix[ticker] = label