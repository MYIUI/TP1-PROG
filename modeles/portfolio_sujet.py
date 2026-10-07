from datetime import datetime
import yfinance as yf
from modeles.sujet import Sujet

class PortfolioSujet(Sujet):
    def __init__(self, titres_initiaux=None):
        super().__init__()
        # Structure de titres: {ticker: {"quantite": int, "seuil_bas": float, "seuil_haut": float}}
        self.titres = titres_initiaux if titres_initiaux is not None else {}
        # Structure de prix: {ticker: (prix, ouverture)}
        self.prix = {}

    def recuperer_prix_ticker(self, ticker):

        info = yf.Ticker(ticker).fast_info
        prix = info["last_price"]
        if prix is None:
            raise ValueError(f"Le titre '{ticker}' n'existe pas.")
        return prix, info["open"]

    def ajouter_titre(self, ticker, quantite, seuil_bas=None, seuil_haut=None):

        prix, ouverture = self.recuperer_prix_ticker(ticker)
        
        self.titres[ticker] = {
            "quantite": quantite,
            "seuil_bas": round(seuil_bas if seuil_bas is not None else prix * 0.8, 2),
            "seuil_haut": round(seuil_haut if seuil_haut is not None else prix * 1.2, 2)
        }
        self.prix[ticker] = (prix, ouverture)
        self.notifier()

    def retirer_titre(self, ticker):

        if ticker in self.titres:
            del self.titres[ticker]
            self.prix.pop(ticker, None)
            self.notifier()

    def modifier_titre(self, ticker, quantite=None, seuil_bas=None, seuil_haut=None):
   
        if ticker in self.titres:
            if quantite is not None:
                self.titres[ticker]["quantite"] = quantite
            if seuil_bas is not None:
                self.titres[ticker]["seuil_bas"] = round(seuil_bas, 2)
            if seuil_haut is not None:
                self.titres[ticker]["seuil_haut"] = round(seuil_haut, 2)
            self.notifier()

    def mettre_a_jour_prix(self):

        nouveaux_prix = {}
        for ticker in self.titres:
            nouveaux_prix[ticker] = self.recuperer_prix_ticker(ticker)
        self.prix = nouveaux_prix
        self.notifier()

    def get_donnees(self) -> dict:

        return {
            "titres": self.titres,
            "prix": self.prix,
            "horodatage": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }