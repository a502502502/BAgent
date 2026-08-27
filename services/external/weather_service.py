"""
BAgent - Open-Meteo Weather & Pitch Conditions Engine (Step 2)
Interroga le coordinate geografiche degli stadi europei per estrarre
precipitazioni, temperatura e vento, calcolando l'impatto su Corner e Gol.
"""

import sys
import requests
from dataclasses import dataclass
from typing import Optional, Dict, Any

@dataclass
class WeatherCondition:
    stadium_city: str
    temperature_c: float
    precipitation_mm: float
    precipitation_prob_pct: int
    wind_speed_kmh: float
    pitch_condition: str # ASCIUTTO / VELOCE, UMIDO, PESANTE / FANGOSO, VENTO FORTE
    betting_impact: str
    corner_impact: str
    goals_impact: str

class WeatherService:
    """
    Servizio Meteo basato su Open-Meteo API (100% Gratuito, Nessuna Chiave Richiesta).
    """

    # Database coordinate stadi principali
    STADIUM_COORDINATES = {
        "miskolc": (48.10, 20.78),      # DVTK Stadion (Ungheria - Hapoel vs Atalanta)
        "barcelona": (41.38, 2.12),     # Spotify Camp Nou / Montjuic (FC Barcellona)
        "bilbao": (43.26, -2.94),       # San Mamés (Athletic Club)
        "braga": (41.56, -8.43),        # Estádio Municipal de Braga
        "belgrade": (44.78, 20.45),     # Partizan Stadium (Belgrado)
        "reykjavik": (64.13, -21.90),   # Islanda (Vikingur vs Brighton)
        "brighton": (50.86, -0.08),     # Amex Stadium
        "rome": (41.93, 12.45),         # Stadio Olimpico
        "milan": (45.47, 9.12),         # San Siro
        "bologna": (44.49, 11.31),      # Stadio Renato Dall'Ara
        "london": (51.47, -0.22),       # Craven Cottage (Fulham)
        "madrid": (40.45, -3.68)        # Santiago Bernabéu / Metropolitano
    }

    def get_weather_forecast(self, city_or_venue: str) -> WeatherCondition:
        """
        Interroga Open-Meteo per la città/stadio specificato.
        """
        city_clean = city_or_venue.lower().strip()
        coords = self.STADIUM_COORDINATES.get(city_clean, (41.90, 12.50)) # default Roma

        lat, lon = coords
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,precipitation,wind_speed_10m&hourly=precipitation_probability&forecast_days=1"

        try:
            r = requests.get(url, timeout=6)
            if r.status_code == 200:
                data = r.json()
                current = data.get("current", {})
                hourly = data.get("hourly", {})

                temp = current.get("temperature_2m", 22.0)
                precip = current.get("precipitation", 0.0)
                wind = current.get("wind_speed_10m", 12.0)
                probs = hourly.get("precipitation_probability", [0])
                prob_pct = probs[0] if probs else 0

                # Analisi del Campo e Impatto Betting
                if precip > 4.0:
                    pitch = "PESANTE / FANGOSO 🌧️"
                    corner_impact = "⚠️ NEGATIVO: Campo pesante riduce i cross radenti e favorisce scivolate / interruzioni."
                    goals_impact = "📉 Tendenza Under / Battaglia fisica con molti falli e contrasti duri."
                    advice = "Favorisce mercati su Falli e Cartellini; evitare Over Corner alti."
                elif wind > 35.0:
                    pitch = "VENTO FORTE 💨"
                    corner_impact = "⚠️ IMPREVEDIBILE: Traiettorie aeree deviate dal vento."
                    goals_impact = "📉 Ridotta precisione nei tiri da fuori."
                    advice = "Preferire mercati di risultato protetto (Doppia Chance) o falli a terra."
                elif precip > 0.5 or prob_pct > 60:
                    pitch = "UMIDO / VELOCE 🌦️"
                    corner_impact = "✅ OTTIMO: Pallone rapido, tiri veloci deviati dai portieri in calcio d'angolo."
                    goals_impact = "⚽ Normale / Alto: Rimbalzi ingannevoli che favoriscono i gol."
                    advice = "Condizioni eccellenti per Over 1.5 Gol e Over 7.5 Corner Totali."
                else:
                    pitch = "PERFETTO / ASCIUTTO ☀️"
                    corner_impact = "✅ IDEALE: Piena fluidità per schemi offensivi e ali da cross sul fondo."
                    goals_impact = "⚽ Normale / Veloce: Massima esaltazione del tasso tecnico."
                    advice = "Piena conformità ai modelli Poisson standard."

                return WeatherCondition(
                    stadium_city=city_clean.capitalize(),
                    temperature_c=round(temp, 1),
                    precipitation_mm=round(precip, 1),
                    precipitation_prob_pct=prob_pct,
                    wind_speed_kmh=round(wind, 1),
                    pitch_condition=pitch,
                    betting_impact=advice,
                    corner_impact=corner_impact,
                    goals_impact=goals_impact
                )
        except Exception as e:
            print(f"[WeatherService Warning] Errore Open-Meteo per {city_or_venue}: {e}")

        # Fallback neutrale
        return WeatherCondition(
            stadium_city=city_or_venue.capitalize(),
            temperature_c=22.0,
            precipitation_mm=0.0,
            precipitation_prob_pct=10,
            wind_speed_kmh=10.0,
            pitch_condition="PERFETTO / ASCIUTTO ☀️",
            betting_impact="Piena conformità ai modelli Poisson standard.",
            corner_impact="✅ Ideale per schemi offensivi.",
            goals_impact="⚽ Normale / Veloce."
        )
