#!/bin/bash
# Installiert die Abhängigkeiten und startet das Projekt

echo "📦 Installiere benötigte Pakete..."
pip install -r requirements.txt

echo "🚀 Starte das Chat-Programm..."
python3 main.py
