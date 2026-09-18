# -*- coding: utf-8 -*-

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.core.window import Window
from tinydb import TinyDB, Query
import os

# Configuration de la base de données locale
db_path = 'royal_palm_db.json'
db = TinyDB(db_path)
lots_table = db.table('lots')

# Design Global
BG_COLOR = (0.06, 0.06, 0.06, 1)  # #111
GOLD_COLOR = (0.83, 0.68, 0.21, 1)  # #d4af37
TEXT_COLOR = (1, 1, 1, 1)
CARD_COLOR = (0.11, 0.11, 0.11, 1)  # #1c1c1c

class AccueilScreen(Screen):
    def on_enter(self):
        self.clear_widgets()
        Window.clearcolor = BG_COLOR
        
        main_layout = BoxLayout(orientation='vertical', padding=20, spacing=15)
        
        # Header
        header = Label(
            text="ROYAL SERVICE\nGESTION ROYAL'PALM",
            font_size='24sp', bold=True, color=GOLD_COLOR, halign='center', size_hint_y=0.2
        )
        main_layout.add_widget(header)
        
        # Liste des lots défilante
        scroll = ScrollView(size_hint_y=0.6)
        lots_layout = BoxLayout(orientation='vertical', spacing=10, size_hint_y=None)
        lots_layout.bind(minimum_height=lots_layout.setter('height'))
        
        lots = sorted(lots_table.all(), key=lambda x: x.get("id", 0))
        for lot in lots:
            lot_box = BoxLayout(orientation='horizontal', spacing=10, size_hint_y=None, height=60, padding=10)
            lbl = Label(text=f"Lot {lot['id']:04d}", font_size='18sp', color=GOLD_COLOR)
            btn = Button(text="Ouvrir", background_color=GOLD_COLOR, color=(0,0,0,1), font_size='16sp', bold=True)
            btn.bind(on_release=lambda instance, l_id=lot['id']: self.ouvrir_lot(l_id))
            
            lot_box.add_widget(lbl)
            lot_box.add_widget(btn)
            lots_layout.add_widget(lot_box)
            
        scroll.add_widget(lots_layout)
        main_layout.add_widget(scroll)
        
        # Bouton Ajouter Lot
        btn_add = Button(
            text="+ Créer un nouveau Lot",
            background_color=GOLD_COLOR, color=(0,0,0,1),
            font_size='18sp', bold=True, size_hint_y=0.15
        )
        btn_add.bind(on_release=self.creer_lot)
        main_layout.add_widget(btn_add)
        
        self.add_widget(main_layout)

    def ouvrir_lot(self, lot_id):
        self.manager.current_lot_id = lot_id
        self.manager.current = 'lot_detail'

    def creer_lot(self, instance):
        lots = lots_table.all()
        prochain_id = max([l["id"] for l in lots]) + 1 if lots else 1
        lots_table.insert({
            "id": prochain_id,
            "achat": {"litres": 0, "prix_achat": 0, "transport_achat": 0, "conditionnement": 0, "transport_vente": 0},
            "ventes": [],
            "depenses": []
        })
        self.on_enter()

class LotDetailScreen(Screen):
    def on_enter(self):
        self.clear_widgets()
        lot_id = self.manager.current_lot_id
        Lot = Query()
        lot = lots_table.search(Lot.id == lot_id)[0]
        
        main_layout = BoxLayout(orientation='vertical', padding=15, spacing=10)
        
        # Navigation
        btn_back = Button(text="← Retour aux lots", size_hint_y=0.08, background_color=(0.2,0.2,0.2,1))
        btn_back.bind(on_release=self.retour)
        main_layout.add_widget(btn_back)
        
        # Titre
        title = Label(text=f"Gestion du Lot {lot_id:04d}", font_size='22sp', bold=True, color=GOLD_COLOR, size_hint_y=0.08)
        main_layout.add_widget(title)
        
        # Calculs et Statistiques
        achat = lot["achat"]
        total_achat = achat["prix_achat"] + achat["transport_achat"] + achat["conditionnement"] + achat["transport_vente"]
        total_vente = sum(v["qte"] * v["pu"] for v in lot["ventes"])
        benefice = total_vente - total_achat
        
        grid = GridLayout(cols=2, spacing=10, size_hint_y=0.25)
        grid.add_widget(Label(text=f"Litres: {achat['litres']} L", color=TEXT_COLOR))
        grid.add_widget(Label(text=f"Total Achat: {total_achat}", color=TEXT_COLOR))
        grid.add_widget(Label(text=f"Total Vente: {total_vente}", color=TEXT_COLOR))
        grid.add_widget(Label(text=f"Bénéfice: {benefice}", color=GOLD_COLOR, bold=True))
        main_layout.add_widget(grid)
        
        # Formulaire d'Achat rapide
        form_layout = BoxLayout(orientation='vertical', spacing=5, size_hint_y=0.4)
        form_layout.add_widget(Label(text="Mettre à jour les Litres achetés:", font_size='14sp', color=GOLD_COLOR))
        self.txt_litres = TextInput(text=str(achat['litres']), multiline=False, input_filter='float')
        form_layout.add_widget(self.txt_litres)
        
        form_layout.add_widget(Label(text="Prix Achat Total:", font_size='14sp', color=GOLD_COLOR))
        self.txt_prix = TextInput(text=str(achat['prix_achat']), multiline=False, input_filter='float')
        form_layout.add_widget(self.txt_prix)
        
        btn_save = Button(text="Enregistrer l'achat", background_color=GOLD_COLOR, color=(0,0,0,1), bold=True)
        btn_save.bind(on_release=self.enregistrer_achat)
        form_layout.add_widget(btn_save)
        
        main_layout.add_widget(form_layout)
        self.add_widget(main_layout)

    def enregistrer_achat(self, instance):
        lot_id = self.manager.current_lot_id
        Lot = Query()
        try:
            litres = float(self.txt_litres.text or 0)
            prix = float(self.txt_prix.text or 0)
            lots_table.update({
                "achat": {
                    "litres": litres, "prix_achat": prix,
                    "transport_achat": 0, "conditionnement": 0, "transport_vente": 0
                }
            }, Lot.id == lot_id)
            self.on_enter()
        except:
            pass

    def retour(self, instance):
        self.manager.current = 'accueil'

class RoyalPalmApp(App):
    def build(self):
        sm = ScreenManager()
        sm.current_lot_id = None
        sm.add_widget(AccueilScreen(name='accueil'))
        sm.add_widget(LotDetailScreen(name='lot_detail'))
        return sm

if __name__ == '__main__':
    RoyalPalmApp().run()
