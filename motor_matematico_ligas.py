"""
MOTOR MATEMÁTICO INDEPENDIENTE POR LIGA — QUANTBET22 v7
=======================================================
Aísla la matemática y estadística de CADA liga en su propio perfil calibrado
(calibracion_ligas.json), con candado de ligas validadas ("bloqueada_ok": true)
para impedir que ajustes en una liga o en selecciones alteren ligas ya estables.

Fundamentos matemáticos implementados:
1. Integral Gamma-Poisson (Conjugada Bayesiana Empírica):
   P(X = k) = ∫ Poisson(k | λ) * Gamma(λ; α, β) dλ = NegBin(k; r=α, p=β/(β+1))
   Evita sobreconfianza cuando un equipo tiene pocos partidos.
2. Modelo Log-Lineal Regularizado (Espacio Logarítmico + tanh):
   ln(λ_H) = ln(μ_H) + κ_atq * tanh(ln(GF_H / μ_H) + ln(GC_A / μ_H)) + η * dλ/dt
   Impide que marcadores anómalos (6-0) o multiplicadores globales disparen λ.
3. Máxima Verosimilitud (MLE) por Derivada Analítica para Dixon-Coles (ρ_liga):
   Resuelve dℓ(ρ)/dρ = 0 sobre los marcadores reales de cada liga por separado.
4. Sobredispersión Empírica por Momentos (φ_liga = Var(X) / E[X]):
   Calibra φ independiente para Córners, Faltas, Remates y Tarjetas en cada liga.
5. Entropía de Shannon Normalizada:
   H_norm = -(1 / ln 3) * Σ p_i * ln(p_i) ∈ [0, 1]
   Detecta partidos moneda al aire para bloquear mercados 1X2 / Doble Oportunidad.
"""

import json
import math
import os
from datetime import datetime
import pandas as pd

ARCHIVO_CALIBRACION_LIGAS = "calibracion_ligas.json"

# Perfiles base independientes por liga (calibrables automáticamente vía MLE sin tocar ligas bloqueadas)
PERFILES_BASE_LIGAS = {
    "inglaterra": {
        "nombre": "Premier League",
        "bloqueada_ok": True,
        "activa_clientes": True,
        "mu_h": 1.62,
        "mu_a": 1.32,
        "rho_dc": -0.075,
        "xi_decay": 0.11,
        "kappa_bayes": 4.0,
        "phi_corners": 1.52,
        "phi_faltas": 1.66,
        "phi_remates": 1.4,
        "phi_tarjetas": 1.3,
        "peso_mercado_1x2": 0.56,
        "peso_mercado_goles": 0.42,
        "entropia_max_ganador": 0.945,
        "notas": "BLOQUEADA (ROI real positivo): Ritmo alto, córners altos."
    },
    "españa": {
        "nombre": "LaLiga EA Sports",
        "bloqueada_ok": False,
        "activa_clientes": True,
        "mu_h": 1.42,
        "mu_a": 1.05,
        "rho_dc": -0.135,
        "xi_decay": 0.13,
        "kappa_bayes": 4.5,
        "phi_corners": 1.58,
        "phi_faltas": 1.88,
        "phi_remates": 1.46,
        "phi_tarjetas": 1.44,
        "peso_mercado_1x2": 0.66,
        "peso_mercado_goles": 0.52,
        "entropia_max_ganador": 0.925,
        "notas": "Desbloqueada y recalibrada (v24): mayor peso al mercado y menor sobreconfianza en X2/Under."
    },
    "españa_2": {
        "nombre": "LaLiga Hypermotion (2ª)",
        "bloqueada_ok": False,
        "activa_clientes": True,
        "mu_h": 1.28,
        "mu_a": 0.94,
        "rho_dc": -0.155,
        "xi_decay": 0.16,
        "kappa_bayes": 5.0,
        "phi_corners": 1.58,
        "phi_faltas": 1.94,
        "phi_remates": 1.46,
        "phi_tarjetas": 1.44,
        "peso_mercado_1x2": 0.72,
        "peso_mercado_goles": 0.56,
        "entropia_max_ganador": 0.92,
        "notas": "Alta paridad; fuerte anclaje a tabla actual y mercado."
    },
    "italia": {
        "nombre": "Serie A",
        "bloqueada_ok": True,
        "activa_clientes": True,
        "mu_h": 1.42,
        "mu_a": 1.14,
        "rho_dc": -0.125,
        "xi_decay": 0.12,
        "kappa_bayes": 4.0,
        "phi_corners": 1.5,
        "phi_faltas": 1.78,
        "phi_remates": 1.38,
        "phi_tarjetas": 1.36,
        "peso_mercado_1x2": 0.58,
        "peso_mercado_goles": 0.42,
        "entropia_max_ganador": 0.94,
        "notas": "BLOQUEADA (ROI real +4.76%): Táctica estructurada."
    },
    "alemania": {
        "nombre": "Bundesliga",
        "bloqueada_ok": True,
        "activa_clientes": True,
        "mu_h": 1.74,
        "mu_a": 1.36,
        "rho_dc": -0.055,
        "xi_decay": 0.12,
        "kappa_bayes": 4.0,
        "phi_corners": 1.5,
        "phi_faltas": 1.7,
        "phi_remates": 1.4,
        "phi_tarjetas": 1.3,
        "peso_mercado_1x2": 0.56,
        "peso_mercado_goles": 0.42,
        "entropia_max_ganador": 0.945,
        "notas": "BLOQUEADA (ROI real +10.16%): Alta producción ofensiva."
    },
    "francia": {
        "nombre": "Ligue 1",
        "bloqueada_ok": True,
        "activa_clientes": True,
        "mu_h": 1.39,
        "mu_a": 1.09,
        "rho_dc": -0.135,
        "xi_decay": 0.14,
        "kappa_bayes": 5.0,
        "phi_corners": 1.56,
        "phi_faltas": 1.82,
        "phi_remates": 1.46,
        "phi_tarjetas": 1.36,
        "peso_mercado_1x2": 0.68,
        "peso_mercado_goles": 0.56,
        "entropia_max_ganador": 0.915,
        "notas": "BLOQUEADA (ROI real +2.72%): Calibrada."
    },
    "portugal": {
        "nombre": "Primeira Liga",
        "bloqueada_ok": False,
        "activa_clientes": True,
        "mu_h": 1.36,
        "mu_a": 1.02,
        "rho_dc": -0.15,
        "xi_decay": 0.14,
        "kappa_bayes": 5.0,
        "phi_corners": 1.66,
        "phi_faltas": 1.94,
        "phi_remates": 1.54,
        "phi_tarjetas": 1.46,
        "peso_mercado_1x2": 0.72,
        "peso_mercado_goles": 0.6,
        "entropia_max_ganador": 0.915,
        "notas": "Recalibrada (v24): duelos cerrados fuera del Top 3."
    },
    "holanda": {
        "nombre": "Eredivisie",
        "bloqueada_ok": True,
        "activa_clientes": True,
        "mu_h": 1.58,
        "mu_a": 1.18,
        "rho_dc": -0.095,
        "xi_decay": 0.14,
        "kappa_bayes": 5.0,
        "phi_corners": 1.58,
        "phi_faltas": 1.74,
        "phi_remates": 1.48,
        "phi_tarjetas": 1.3,
        "peso_mercado_1x2": 0.68,
        "peso_mercado_goles": 0.58,
        "entropia_max_ganador": 0.925,
        "notas": "BLOQUEADA (ROI real +8.63%): Prior goleador regularizado."
    },
    "belgica": {
        "nombre": "Pro League Bélgica",
        "bloqueada_ok": False,
        "activa_clientes": True,
        "mu_h": 1.56,
        "mu_a": 1.24,
        "rho_dc": -0.085,
        "xi_decay": 0.14,
        "kappa_bayes": 4.5,
        "phi_corners": 1.54,
        "phi_faltas": 1.78,
        "phi_remates": 1.42,
        "phi_tarjetas": 1.34,
        "peso_mercado_1x2": 0.64,
        "peso_mercado_goles": 0.5,
        "entropia_max_ganador": 0.93,
        "notas": "Ritmo medio-alto."
    },
    "turquia": {
        "nombre": "Süper Lig Turquía (DESACTIVADA)",
        "bloqueada_ok": True,
        "activa_clientes": False,
        "mu_h": 1.58,
        "mu_a": 1.18,
        "rho_dc": -0.095,
        "xi_decay": 0.14,
        "kappa_bayes": 4.5,
        "phi_corners": 1.58,
        "phi_faltas": 1.92,
        "phi_remates": 1.46,
        "phi_tarjetas": 1.44,
        "peso_mercado_1x2": 0.66,
        "peso_mercado_goles": 0.54,
        "entropia_max_ganador": 0.93,
        "notas": "ELIMINADA de escaneo y clientes."
    },
    "arabia_saudita": {
        "nombre": "Saudi Pro League",
        "bloqueada_ok": False,
        "activa_clientes": True,
        "mu_h": 1.54,
        "mu_a": 1.22,
        "rho_dc": -0.095,
        "xi_decay": 0.18,
        "kappa_bayes": 5.5,
        "phi_corners": 1.72,
        "phi_faltas": 1.92,
        "phi_remates": 1.58,
        "phi_tarjetas": 1.48,
        "peso_mercado_1x2": 0.78,
        "peso_mercado_goles": 0.68,
        "entropia_max_ganador": 0.905,
        "notas": "Recalibrada (v24): máxima cautela por alta varianza; fuerte peso de mercado real."
    },
    "colombia": {
        "nombre": "Liga BetPlay Colombia",
        "bloqueada_ok": False,
        "activa_clientes": True,
        "mu_h": 1.34,
        "mu_a": 0.86,
        "rho_dc": -0.165,
        "xi_decay": 0.17,
        "kappa_bayes": 5.0,
        "phi_corners": 1.66,
        "phi_faltas": 2.02,
        "phi_remates": 1.52,
        "phi_tarjetas": 1.52,
        "peso_mercado_1x2": 0.74,
        "peso_mercado_goles": 0.58,
        "entropia_max_ganador": 0.915,
        "notas": "Desbloqueada y recalibrada (v24): separada de Copa BetPlay; altura/clima vía motor_ambiental."
    },
    "argentina": {
        "nombre": "Liga Profesional Argentina",
        "bloqueada_ok": False,
        "activa_clientes": True,
        "mu_h": 1.24,
        "mu_a": 0.84,
        "rho_dc": -0.18,
        "xi_decay": 0.16,
        "kappa_bayes": 5.5,
        "phi_corners": 1.66,
        "phi_faltas": 2.04,
        "phi_remates": 1.54,
        "phi_tarjetas": 1.52,
        "peso_mercado_1x2": 0.76,
        "peso_mercado_goles": 0.62,
        "entropia_max_ganador": 0.91,
        "notas": "Desbloqueada y recalibrada (v24): separada de Copa Argentina; alta fricción y baja media."
    },
    "brasil": {
        "nombre": "Brasileirão Serie A",
        "bloqueada_ok": True,
        "activa_clientes": True,
        "mu_h": 1.48,
        "mu_a": 1.02,
        "rho_dc": -0.125,
        "xi_decay": 0.15,
        "kappa_bayes": 4.5,
        "phi_corners": 1.56,
        "phi_faltas": 1.94,
        "phi_remates": 1.44,
        "phi_tarjetas": 1.44,
        "peso_mercado_1x2": 0.68,
        "peso_mercado_goles": 0.52,
        "entropia_max_ganador": 0.925,
        "notas": "BLOQUEADA (separada de Copa do Brasil): Localía pesada y calendario intenso."
    },
    "mexico": {
        "nombre": "Liga MX",
        "bloqueada_ok": False,
        "activa_clientes": True,
        "mu_h": 1.52,
        "mu_a": 1.1,
        "rho_dc": -0.115,
        "xi_decay": 0.16,
        "kappa_bayes": 5.0,
        "phi_corners": 1.64,
        "phi_faltas": 1.94,
        "phi_remates": 1.52,
        "phi_tarjetas": 1.48,
        "peso_mercado_1x2": 0.74,
        "peso_mercado_goles": 0.6,
        "entropia_max_ganador": 0.915,
        "notas": "Desbloqueada y recalibrada (v24): torneos cortos y Liguilla con alta varianza."
    },
    "usa": {
        "nombre": "MLS Estados Unidos",
        "bloqueada_ok": False,
        "activa_clientes": True,
        "mu_h": 1.54,
        "mu_a": 1.14,
        "rho_dc": -0.105,
        "xi_decay": 0.16,
        "kappa_bayes": 5.0,
        "phi_corners": 1.6,
        "phi_faltas": 1.84,
        "phi_remates": 1.48,
        "phi_tarjetas": 1.38,
        "peso_mercado_1x2": 0.72,
        "peso_mercado_goles": 0.62,
        "entropia_max_ganador": 0.92,
        "notas": "Anclada al mercado en playoffs."
    },
    "UEFA CHAMPIONS LEAGUE": {
        "nombre": "UEFA Champions League",
        "bloqueada_ok": False,
        "activa_clientes": True,
        "mu_h": 1.66,
        "mu_a": 1.26,
        "rho_dc": -0.08,
        "xi_decay": 0.12,
        "kappa_bayes": 4.5,
        "phi_corners": 1.74,
        "phi_faltas": 1.9,
        "phi_remates": 1.56,
        "phi_tarjetas": 1.56,
        "peso_mercado_1x2": 0.66,
        "peso_mercado_goles": 0.5,
        "entropia_max_ganador": 0.93,
        "notas": "Recalibrada (v24): Goles +13.9% ROI; phi alto en Córners/Tarjetas/Remates para frenar varianza UEFA."
    },
    "UEFA EUROPA LEAGUE": {
        "nombre": "UEFA Europa League",
        "bloqueada_ok": False,
        "activa_clientes": True,
        "mu_h": 1.56,
        "mu_a": 1.2,
        "rho_dc": -0.095,
        "xi_decay": 0.13,
        "kappa_bayes": 4.5,
        "phi_corners": 1.74,
        "phi_faltas": 1.92,
        "phi_remates": 1.56,
        "phi_tarjetas": 1.56,
        "peso_mercado_1x2": 0.68,
        "peso_mercado_goles": 0.52,
        "entropia_max_ganador": 0.925,
        "notas": "Recalibrada (v24): Goles +19.2% ROI; phi alto en estadísticas UEFA."
    },
    "UEFA CONFERENCE LEAGUE": {
        "nombre": "UEFA Conference League",
        "bloqueada_ok": False,
        "activa_clientes": True,
        "mu_h": 1.58,
        "mu_a": 1.16,
        "rho_dc": -0.095,
        "xi_decay": 0.14,
        "kappa_bayes": 5.0,
        "phi_corners": 1.76,
        "phi_faltas": 1.94,
        "phi_remates": 1.58,
        "phi_tarjetas": 1.58,
        "peso_mercado_1x2": 0.7,
        "peso_mercado_goles": 0.56,
        "entropia_max_ganador": 0.925,
        "notas": "Recalibrada (v24): diferencia amplia de presupuestos y alta varianza estadística."
    },
    "COPA LIBERTADORES": {
        "nombre": "CONMEBOL Copa Libertadores",
        "bloqueada_ok": False,
        "activa_clientes": True,
        "mu_h": 1.48,
        "mu_a": 0.96,
        "rho_dc": -0.145,
        "xi_decay": 0.15,
        "kappa_bayes": 5.0,
        "phi_corners": 1.68,
        "phi_faltas": 2.04,
        "phi_remates": 1.52,
        "phi_tarjetas": 1.54,
        "peso_mercado_1x2": 0.7,
        "peso_mercado_goles": 0.56,
        "entropia_max_ganador": 0.915,
        "notas": "Perfil independiente Libertadores (v24): localía fuerte, viajes largos y alta fricción."
    },
    "COPA SUDAMERICANA": {
        "nombre": "CONMEBOL Copa Sudamericana",
        "bloqueada_ok": False,
        "activa_clientes": True,
        "mu_h": 1.42,
        "mu_a": 0.94,
        "rho_dc": -0.155,
        "xi_decay": 0.16,
        "kappa_bayes": 5.0,
        "phi_corners": 1.7,
        "phi_faltas": 2.02,
        "phi_remates": 1.54,
        "phi_tarjetas": 1.52,
        "peso_mercado_1x2": 0.72,
        "peso_mercado_goles": 0.58,
        "entropia_max_ganador": 0.915,
        "notas": "Perfil independiente Sudamericana (v24): marcadores cerrados y alta varianza en cruces."
    },
    "copa_españa": {
        "nombre": "Copa del Rey (España)",
        "bloqueada_ok": False,
        "activa_clientes": True,
        "mu_h": 1.4,
        "mu_a": 1.08,
        "rho_dc": -0.14,
        "xi_decay": 0.15,
        "kappa_bayes": 5.5,
        "phi_corners": 1.68,
        "phi_faltas": 1.94,
        "phi_remates": 1.54,
        "phi_tarjetas": 1.5,
        "peso_mercado_1x2": 0.74,
        "peso_mercado_goles": 0.6,
        "entropia_max_ganador": 0.915,
        "notas": "Eliminatoria a partido único con rotaciones: separada de LaLiga."
    },
    "copa_inglaterra": {
        "nombre": "FA Cup / EFL Cup (Inglaterra)",
        "bloqueada_ok": False,
        "activa_clientes": True,
        "mu_h": 1.52,
        "mu_a": 1.24,
        "rho_dc": -0.1,
        "xi_decay": 0.15,
        "kappa_bayes": 5.5,
        "phi_corners": 1.66,
        "phi_faltas": 1.84,
        "phi_remates": 1.52,
        "phi_tarjetas": 1.44,
        "peso_mercado_1x2": 0.74,
        "peso_mercado_goles": 0.6,
        "entropia_max_ganador": 0.92,
        "notas": "Copas inglesas con rotaciones de plantilla: separada de Premier League."
    },
    "copa_italia": {
        "nombre": "Coppa Italia",
        "bloqueada_ok": False,
        "activa_clientes": True,
        "mu_h": 1.38,
        "mu_a": 1.06,
        "rho_dc": -0.145,
        "xi_decay": 0.15,
        "kappa_bayes": 5.5,
        "phi_corners": 1.66,
        "phi_faltas": 1.92,
        "phi_remates": 1.52,
        "phi_tarjetas": 1.48,
        "peso_mercado_1x2": 0.72,
        "peso_mercado_goles": 0.58,
        "entropia_max_ganador": 0.915,
        "notas": "Eliminatoria italiana con rotaciones: separada de Serie A."
    },
    "copa_alemania": {
        "nombre": "DFB Pokal (Alemania)",
        "bloqueada_ok": False,
        "activa_clientes": True,
        "mu_h": 1.66,
        "mu_a": 1.32,
        "rho_dc": -0.075,
        "xi_decay": 0.15,
        "kappa_bayes": 5.0,
        "phi_corners": 1.64,
        "phi_faltas": 1.84,
        "phi_remates": 1.5,
        "phi_tarjetas": 1.42,
        "peso_mercado_1x2": 0.7,
        "peso_mercado_goles": 0.56,
        "entropia_max_ganador": 0.925,
        "notas": "Eliminatoria alemana a partido único: separada de Bundesliga."
    },
    "copa_francia": {
        "nombre": "Coupe de France",
        "bloqueada_ok": False,
        "activa_clientes": True,
        "mu_h": 1.36,
        "mu_a": 1.08,
        "rho_dc": -0.145,
        "xi_decay": 0.16,
        "kappa_bayes": 5.5,
        "phi_corners": 1.68,
        "phi_faltas": 1.92,
        "phi_remates": 1.54,
        "phi_tarjetas": 1.46,
        "peso_mercado_1x2": 0.76,
        "peso_mercado_goles": 0.62,
        "entropia_max_ganador": 0.91,
        "notas": "Eliminatoria francesa: separada de Ligue 1."
    },
    "copa_portugal": {
        "nombre": "Taça de Portugal",
        "bloqueada_ok": False,
        "activa_clientes": True,
        "mu_h": 1.34,
        "mu_a": 1.0,
        "rho_dc": -0.155,
        "xi_decay": 0.16,
        "kappa_bayes": 5.5,
        "phi_corners": 1.72,
        "phi_faltas": 1.98,
        "phi_remates": 1.58,
        "phi_tarjetas": 1.52,
        "peso_mercado_1x2": 0.76,
        "peso_mercado_goles": 0.64,
        "entropia_max_ganador": 0.91,
        "notas": "Eliminatoria portuguesa: separada de Primeira Liga."
    },
    "copa_holanda": {
        "nombre": "KNVB Beker (Países Bajos)",
        "bloqueada_ok": False,
        "activa_clientes": True,
        "mu_h": 1.54,
        "mu_a": 1.18,
        "rho_dc": -0.105,
        "xi_decay": 0.15,
        "kappa_bayes": 5.5,
        "phi_corners": 1.68,
        "phi_faltas": 1.86,
        "phi_remates": 1.54,
        "phi_tarjetas": 1.42,
        "peso_mercado_1x2": 0.74,
        "peso_mercado_goles": 0.6,
        "entropia_max_ganador": 0.915,
        "notas": "Copa holandesa: separada de Eredivisie."
    },
    "copa_colombia": {
        "nombre": "Copa BetPlay / Superliga (Colombia)",
        "bloqueada_ok": False,
        "activa_clientes": True,
        "mu_h": 1.26,
        "mu_a": 0.8,
        "rho_dc": -0.18,
        "xi_decay": 0.18,
        "kappa_bayes": 5.5,
        "phi_corners": 1.72,
        "phi_faltas": 2.08,
        "phi_remates": 1.58,
        "phi_tarjetas": 1.58,
        "peso_mercado_1x2": 0.78,
        "peso_mercado_goles": 0.64,
        "entropia_max_ganador": 0.905,
        "notas": "Copa BetPlay (rotaciones y llaves cerradas): separada de Liga BetPlay."
    },
    "copa_argentina": {
        "nombre": "Copa Argentina / Copa de la Liga",
        "bloqueada_ok": False,
        "activa_clientes": True,
        "mu_h": 1.18,
        "mu_a": 0.82,
        "rho_dc": -0.185,
        "xi_decay": 0.18,
        "kappa_bayes": 5.5,
        "phi_corners": 1.72,
        "phi_faltas": 2.08,
        "phi_remates": 1.58,
        "phi_tarjetas": 1.58,
        "peso_mercado_1x2": 0.78,
        "peso_mercado_goles": 0.64,
        "entropia_max_ganador": 0.905,
        "notas": "Cancha neutral y alta fricción: separada de Liga Profesional."
    },
    "copa_brasil": {
        "nombre": "Copa do Brasil",
        "bloqueada_ok": False,
        "activa_clientes": True,
        "mu_h": 1.4,
        "mu_a": 0.94,
        "rho_dc": -0.145,
        "xi_decay": 0.16,
        "kappa_bayes": 5.5,
        "phi_corners": 1.66,
        "phi_faltas": 2.02,
        "phi_remates": 1.52,
        "phi_tarjetas": 1.52,
        "peso_mercado_1x2": 0.74,
        "peso_mercado_goles": 0.6,
        "entropia_max_ganador": 0.915,
        "notas": "Eliminatoria ida/vuelta brasileña: separada del Brasileirão."
    },
    "europa": {
        "nombre": "Competición Europea / UWCL",
        "bloqueada_ok": False,
        "activa_clientes": True,
        "mu_h": 1.72,
        "mu_a": 1.28,
        "rho_dc": -0.065,
        "xi_decay": 0.14,
        "kappa_bayes": 5.0,
        "phi_corners": 1.66,
        "phi_faltas": 1.88,
        "phi_remates": 1.5,
        "phi_tarjetas": 1.48,
        "peso_mercado_1x2": 0.74,
        "peso_mercado_goles": 0.66,
        "entropia_max_ganador": 0.93,
        "notas": "Anclado fuertemente al mercado real."
    },
    "internacional": {
        "nombre": "Selecciones Nacionales (Aislado)",
        "bloqueada_ok": True,
        "activa_clientes": True,
        "mu_h": 1.44,
        "mu_a": 1.06,
        "rho_dc": -0.115,
        "xi_decay": 0.15,
        "kappa_bayes": 5.0,
        "phi_corners": 1.62,
        "phi_faltas": 1.9,
        "phi_remates": 1.48,
        "phi_tarjetas": 1.44,
        "peso_mercado_1x2": 0.68,
        "peso_mercado_goles": 0.55,
        "entropia_max_ganador": 0.935,
        "notas": "BLOQUEADO Y AISLADO: no afecta nunca a las ligas de clubes."
    },
    "grecia": {
        "nombre": "Super League Grecia",
        "bloqueada_ok": False,
        "activa_clientes": True,
        "mu_h": 1.39,
        "mu_a": 1.09,
        "rho_dc": -0.135,
        "xi_decay": 0.14,
        "kappa_bayes": 5.0,
        "phi_corners": 1.6,
        "phi_faltas": 1.88,
        "phi_remates": 1.48,
        "phi_tarjetas": 1.42,
        "peso_mercado_1x2": 0.68,
        "peso_mercado_goles": 0.56,
        "entropia_max_ganador": 0.915,
        "notas": "Perfil independiente Grecia."
    },
    "escocia": {
        "nombre": "Scottish Premiership",
        "bloqueada_ok": False,
        "activa_clientes": True,
        "mu_h": 1.39,
        "mu_a": 1.09,
        "rho_dc": -0.135,
        "xi_decay": 0.14,
        "kappa_bayes": 5.0,
        "phi_corners": 1.6,
        "phi_faltas": 1.84,
        "phi_remates": 1.48,
        "phi_tarjetas": 1.4,
        "peso_mercado_1x2": 0.68,
        "peso_mercado_goles": 0.56,
        "entropia_max_ganador": 0.915,
        "notas": "Perfil independiente Escocia."
    }
}

_CACHE_CALIBRACION_MEM = None


def cargar_calibracion_ligas(ruta=ARCHIVO_CALIBRACION_LIGAS, forzar_disco=False):
    global _CACHE_CALIBRACION_MEM
    if _CACHE_CALIBRACION_MEM is not None and not forzar_disco:
        return _CACHE_CALIBRACION_MEM

    datos = {k: dict(v) for k, v in PERFILES_BASE_LIGAS.items()}
    if os.path.exists(ruta):
        try:
            with open(ruta, "r", encoding="utf-8") as f:
                en_disco = json.load(f) or {}
            for lk, cfg in en_disco.items():
                if isinstance(cfg, dict):
                    base = dict(datos.get(lk, PERFILES_BASE_LIGAS["europa"]))
                    base.update(cfg)
                    datos[lk] = base
        except Exception:
            pass
    else:
        guardar_calibracion_ligas(datos, ruta)

    _CACHE_CALIBRACION_MEM = datos
    return datos


def guardar_calibracion_ligas(datos, ruta=ARCHIVO_CALIBRACION_LIGAS):
    global _CACHE_CALIBRACION_MEM
    _CACHE_CALIBRACION_MEM = datos
    try:
        with open(ruta, "w", encoding="utf-8") as f:
            json.dump(datos, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def resolver_clave_competicion(liga_key, liga_visual="", is_america=False):
    """Separa cada competición (Liga doméstica vs Copa doméstica vs Libertadores vs Sudamericana vs UEFA)."""
    lv = str(liga_visual or "").upper()
    if "LIBERTADORES" in lv or liga_key == "COPA LIBERTADORES":
        return "COPA LIBERTADORES"
    if "SUDAMERICANA" in lv or liga_key == "COPA SUDAMERICANA":
        return "COPA SUDAMERICANA"
    if "CHAMPIONS" in lv and "WOMEN" not in lv and "FEMEN" not in lv:
        return "UEFA CHAMPIONS LEAGUE"
    if "EUROPA LEAGUE" in lv:
        return "UEFA EUROPA LEAGUE"
    if "CONFERENCE LEAGUE" in lv:
        return "UEFA CONFERENCE LEAGUE"
    es_copa_dom = any(k in lv for k in (
        "COPA DEL REY", "FA CUP", "EFL CUP", "COPPA ITALIA", "DFB POKAL",
        "COUPE DE FRANCE", "TAÇA DE PORTUGAL", "KNVB BEKER",
        "COPA BETPLAY", "SUPERLIGA", "COPA ARGENTINA", "COPA DE LA LIGA", "COPA DO BRASIL"
    ))
    if es_copa_dom:
        clave_copa = f"copa_{liga_key}"
        if clave_copa in PERFILES_BASE_LIGAS:
            return clave_copa
    return liga_key


def obtener_perfil_liga(liga_key, is_america=False, liga_visual=""):
    cal = cargar_calibracion_ligas()
    clave_real = resolver_clave_competicion(liga_key, liga_visual=liga_visual, is_america=is_america)
    if clave_real in cal:
        return cal[clave_real]
    if liga_key in cal:
        return cal[liga_key]
    fallback = "brasil" if is_america else "francia"
    return cal.get(fallback, PERFILES_BASE_LIGAS["francia"])


def estimar_tasa_bayes_gamma_poisson(serie_valores, xi_decay=0.12, prior_media=1.30, kappa_bayes=4.0):
    """
    Estimación Bayesiana Empírica conjugada Gamma-Poisson con decaimiento exponencial temporal
    y derivada temporal de tendencia (regresión lineal ponderada).

    Integral posterior:
      λ | y ~ Gamma(α₀ + Σ w_i y_i,  β₀ + Σ w_i)
      E[λ | y] = (κ·μ₀ + Σ w_i y_i) / (κ + Σ w_i)

    Retorna: (tasa_posterior, n_efectivo, pendiente_dt, varianza_ponderada)
    """
    if serie_valores is None:
        return float(prior_media), 0.0, 0.0, float(prior_media)

    try:
        vals = [float(x) for x in serie_valores if x is not None and not math.isnan(float(x))]
    except Exception:
        vals = []

    n = len(vals)
    if n == 0:
        return float(prior_media), 0.0, 0.0, float(prior_media)

    # Pesos exponenciales w_i = exp(-xi * (n - 1 - i)) -> el partido más reciente pesa 1.0
    pesos = [math.exp(-float(xi_decay) * (n - 1 - i)) for i in range(n)]
    sum_w = sum(pesos)
    sum_wy = sum(w * y for w, y in zip(pesos, vals))

    alpha_post = (float(kappa_bayes) * float(prior_media)) + sum_wy
    beta_post = float(kappa_bayes) + sum_w
    tasa_post = max(0.22, alpha_post / max(beta_post, 1e-6))

    # Varianza empírica ponderada (mide regularidad del club)
    media_emp = sum_wy / max(sum_w, 1e-6)
    var_pond = sum(w * ((y - media_emp) ** 2) for w, y in zip(pesos, vals)) / max(sum_w, 1e-6)

    # Derivada temporal d(goles)/dt sobre los últimos 6 partidos (momento real)
    ult = vals[-6:] if n >= 6 else vals
    m = len(ult)
    if m >= 3:
        t_bar = (m - 1) / 2.0
        y_bar = sum(ult) / m
        num = sum((i - t_bar) * (ult[i] - y_bar) for i in range(m))
        den = sum((i - t_bar) ** 2 for i in range(m))
        pendiente = (num / den) if den > 0 else 0.0
    else:
        pendiente = 0.0

    return round(tasa_post, 4), round(sum_w, 3), round(pendiente, 4), round(var_pond, 4)


def calcular_lambdas_log_lineal_liga(
    liga_key,
    gf_loc_vals, gc_loc_vals,
    gf_vis_vals, gc_vis_vals,
    is_america=False,
    st_loc_real=None, st_vis_real=None,
    liga_visual="",
):
    """
    Modelo Log-Lineal independiente por liga:
      ln(λ_H) = ln(μ_H) + β_atq * tanh(ln(GF_H / μ_H)) + β_def * tanh(ln(GC_A / μ_H)) + η * dλ_H/dt
      ln(λ_A) = ln(μ_A) + β_atq * tanh(ln(GF_A / μ_A)) + β_def * tanh(ln(GC_H / μ_A)) + η * dλ_A/dt

    - Cada liga usa SU propia media μ_H, μ_A, decaimiento ξ y prior Bayesiano κ.
    - Si un equipo tiene pocos partidos en CSV, la integral Gamma-Poisson contrae suavemente hacia μ_liga
      y se fusiona con su clasificación real 2026-27 (st_loc_real / st_vis_real).
    - Nunca aplica doble penalización de liga.
    """
    cfg = obtener_perfil_liga(liga_key, is_america=is_america, liga_visual=liga_visual)
    mu_h = max(0.85, float(cfg.get("mu_h", 1.45)))
    mu_a = max(0.65, float(cfg.get("mu_a", 1.12)))
    xi = float(cfg.get("xi_decay", 0.12))
    kappa = float(cfg.get("kappa_bayes", 4.5))

    # Prior específico por club si tenemos tabla real de la temporada actual (2026-27)
    prior_gf_h = mu_h
    prior_gc_h = mu_a
    if st_loc_real and st_loc_real.get("pj", 0) >= 3:
        ratio_loc = math.sqrt(mu_h / max(mu_a, 0.5))
        prior_gf_h = max(0.45, min(2.85, float(st_loc_real["gf_pg"]) * ratio_loc))
        prior_gc_h = max(0.40, min(2.45, float(st_loc_real["ga_pg"]) / ratio_loc))

    prior_gf_a = mu_a
    prior_gc_a = mu_h
    if st_vis_real and st_vis_real.get("pj", 0) >= 3:
        ratio_loc = math.sqrt(mu_h / max(mu_a, 0.5))
        prior_gf_a = max(0.38, min(2.55, float(st_vis_real["gf_pg"]) / ratio_loc))
        prior_gc_a = max(0.45, min(2.75, float(st_vis_real["ga_pg"]) * ratio_loc))

    gf_h, n_h, d_gf_h, _ = estimar_tasa_bayes_gamma_poisson(gf_loc_vals, xi, prior_gf_h, kappa)
    gc_h, _, d_gc_h, _ = estimar_tasa_bayes_gamma_poisson(gc_loc_vals, xi, prior_gc_h, kappa)
    gf_a, n_a, d_gf_a, _ = estimar_tasa_bayes_gamma_poisson(gf_vis_vals, xi, prior_gf_a, kappa)
    gc_a, _, d_gc_a, _ = estimar_tasa_bayes_gamma_poisson(gc_vis_vals, xi, prior_gc_a, kappa)

    # Espacio logarítmico acotado por tanh (inmune a goleadas aisladas 6-0)
    atq_h_log = math.tanh(math.log(max(gf_h, 0.25) / mu_h))
    def_h_log = math.tanh(math.log(max(gc_h, 0.25) / mu_a))
    atq_a_log = math.tanh(math.log(max(gf_a, 0.25) / mu_a))
    def_a_log = math.tanh(math.log(max(gc_a, 0.25) / mu_h))

    # Momento por derivada temporal (acotado a ±0.08 en espacio log)
    mom_h = max(-0.08, min(0.08, (d_gf_h - d_gc_a) * 0.08))
    mom_a = max(-0.08, min(0.08, (d_gf_a - d_gc_h) * 0.08))

    # Fuerza relativa en tabla actual (PPG & GD/p) en espacio logarítmico
    log_tabla_delta = 0.0
    if st_loc_real and st_vis_real and st_loc_real.get("pj", 0) >= 4 and st_vis_real.get("pj", 0) >= 4:
        d_ppg = float(st_loc_real["ppg"]) - float(st_vis_real["ppg"])
        d_gd = float(st_loc_real["gd_pg"]) - float(st_vis_real["gd_pg"])
        log_tabla_delta = max(-0.26, min(0.26, (d_ppg * 0.14) + (d_gd * 0.09)))

    ln_lh = math.log(mu_h) + (0.76 * atq_h_log) + (0.64 * def_a_log) + mom_h + (0.55 * log_tabla_delta)
    ln_la = math.log(mu_a) + (0.76 * atq_a_log) + (0.64 * def_h_log) + mom_a - (0.55 * log_tabla_delta)

    lam_h = round(max(0.38, min(3.10, math.exp(ln_lh))), 4)
    lam_a = round(max(0.28, min(2.65, math.exp(ln_la))), 4)

    return {
        "l_local": lam_h,
        "l_vis": lam_a,
        "n_ef_local": n_h,
        "n_ef_vis": n_a,
        "gf_h_post": gf_h,
        "gc_h_post": gc_h,
        "gf_a_post": gf_a,
        "gc_a_post": gc_a,
        "rho_liga": float(cfg.get("rho_dc", -0.10)),
        "cfg_liga": cfg,
    }


def integral_gamma_poisson_over(mu, linea, phi_liga=1.45, n_efectivo=10.0):
    """
    Calcula P(X > linea) integrando la incertidumbre del parámetro λ bajo distribución Gamma
    combinada con la sobredispersión natural de la liga φ_liga:
      φ_total = φ_liga + incertidumbre_muestra
      P(X = k) = Γ(k + r) / (Γ(k+1)Γ(r)) * p^r * (1-p)^k,  r = μ / (φ_total - 1), p = 1 / φ_total

    Si un equipo tiene pocos partidos (n_efectivo bajo), φ_total aumenta automáticamente y la
    probabilidad se vuelve más conservadora (cero apuestas ciegas).
    """
    if mu is None or mu <= 0:
        return None
    mu = float(mu)
    incert = min(0.35, 1.20 / max(3.5, float(n_efectivo) + 3.0))
    phi_tot = max(1.04, float(phi_liga) + incert)

    k_max = int(math.floor(linea))
    r = mu / (phi_tot - 1.0)
    p = 1.0 / phi_tot
    q = 1.0 - p

    p_under = 0.0
    for k in range(k_max + 1):
        log_pmf = (
            math.lgamma(k + r) - math.lgamma(k + 1) - math.lgamma(r)
            + r * math.log(p) + k * math.log(q)
        )
        p_under += math.exp(log_pmf)
    return round(min(92.0, max(4.0, (1.0 - p_under) * 100.0)), 2)


def entropia_shannon_1x2(p_h, p_d, p_a):
    """Entropía de Shannon normalizada ∈ [0, 1] del resultado 1X2.
    Valores >= 0.94 indican máxima incertidumbre (partido moneda al aire)."""
    tot = max(1e-9, float(p_h) + float(p_d) + float(p_a))
    probs = [max(1e-9, float(p) / tot) for p in (p_h, p_d, p_a)]
    h = -sum(p * math.log(p) for p in probs)
    return round(h / math.log(3.0), 4)


def estimar_rho_mle_liga(df_liga, mu_h, mu_a, rho_prior=-0.10):
    """
    Máxima Verosimilitud Penalizada (MAP) de Dixon-Coles (1997) condicionada a las tasas
    esperadas POR EQUIPO (λ_H,k, λ_A,k) de la liga, resolviendo:
      d/dρ [ Σ log τ(x_k, y_k; λ_H,k, λ_A,k, ρ)  -  (ρ - ρ_prior)² / (2 σ²) ] = 0
    Evita el sesgo positivo de usar una sola media homogénea para toda la liga.
    """
    if df_liga is None or df_liga.empty or "FTHG" not in df_liga.columns or "FTAG" not in df_liga.columns:
        return round(float(rho_prior), 4)

    sub = df_liga.dropna(subset=["FTHG", "FTAG"]).tail(380).copy()
    if len(sub) < 30:
        return round(float(rho_prior), 4)

    # Estimar ataque/defensa empíricos por equipo en esta liga para obtener (λ_H,k, λ_A,k) reales
    tiene_eq = ("HomeTeam" in sub.columns) and ("AwayTeam" in sub.columns)
    atq_h_m, def_h_m, atq_a_m, def_a_m = {}, {}, {}, {}
    if tiene_eq:
        for eq, grp in sub.groupby("HomeTeam"):
            atq_h_m[eq] = (float(grp["FTHG"].sum()) + 4.0 * mu_h) / (len(grp) + 4.0) / max(mu_h, 0.4)
            def_h_m[eq] = (float(grp["FTAG"].sum()) + 4.0 * mu_a) / (len(grp) + 4.0) / max(mu_a, 0.4)
        for eq, grp in sub.groupby("AwayTeam"):
            atq_a_m[eq] = (float(grp["FTAG"].sum()) + 4.0 * mu_a) / (len(grp) + 4.0) / max(mu_a, 0.4)
            def_a_m[eq] = (float(grp["FTHG"].sum()) + 4.0 * mu_h) / (len(grp) + 4.0) / max(mu_h, 0.4)

    obs = []
    for _, r in sub.iterrows():
        try:
            x, y = int(float(r["FTHG"])), int(float(r["FTAG"]))
            if x <= 1 and y <= 1:
                if tiene_eq:
                    ht, at = r["HomeTeam"], r["AwayTeam"]
                    lh = max(0.35, min(3.2, mu_h * atq_h_m.get(ht, 1.0) * def_a_m.get(at, 1.0)))
                    la = max(0.25, min(2.8, mu_a * atq_a_m.get(at, 1.0) * def_h_m.get(ht, 1.0)))
                else:
                    lh, la = mu_h, mu_a
                obs.append((x, y, lh, la))
        except Exception:
            continue
    if len(obs) < 25:
        return round(float(rho_prior), 4)

    sigma2 = 0.055 ** 2  # Regularización Bayesiana suave hacia la física Dixon-Coles de la liga

    def _derivada_map(rho):
        grad = -(rho - float(rho_prior)) / sigma2
        for x, y, lh, la in obs:
            if x == 0 and y == 0:
                tau, dtau = 1.0 - (lh * la * rho), -(lh * la)
            elif x == 1 and y == 0:
                tau, dtau = 1.0 + (la * rho), la
            elif x == 0 and y == 1:
                tau, dtau = 1.0 + (lh * rho), lh
            else:
                tau, dtau = 1.0 - rho, -1.0
            if tau <= 0.05:
                return -1e6 if dtau > 0 else 1e6
            grad += dtau / tau
        return grad

    lo, hi = -0.19, -0.01
    g_lo, g_hi = _derivada_map(lo), _derivada_map(hi)
    if g_lo * g_hi > 0:
        mejor_rho, mejor_val = float(rho_prior), -1e18
        for step in range(-19, 0):
            rh = step / 100.0
            val = -((rh - float(rho_prior)) ** 2) / (2.0 * sigma2)
            ok = True
            for x, y, lh, la in obs:
                if x == 0 and y == 0: tau = 1.0 - lh * la * rh
                elif x == 1 and y == 0: tau = 1.0 + la * rh
                elif x == 0 and y == 1: tau = 1.0 + lh * rh
                else: tau = 1.0 - rh
                if tau <= 0.05:
                    ok = False
                    break
                val += math.log(tau)
            if ok and val > mejor_val:
                mejor_val, mejor_rho = val, rh
        return round(mejor_rho, 4)

    for _ in range(24):
        mid = (lo + hi) / 2.0
        g_mid = _derivada_map(mid)
        if g_lo * g_mid <= 0:
            hi, g_hi = mid, g_mid
        else:
            lo, g_lo = mid, g_mid
    return round((lo + hi) / 2.0, 4)


def estimar_dispersion_phi_liga(df_liga, col_h, col_a, phi_default=1.45):
    """Estima φ_liga = Var(X) / E[X] por el método de momentos sobre la liga exacta."""
    if df_liga is None or df_liga.empty or col_h not in df_liga.columns or col_a not in df_liga.columns:
        return round(float(phi_default), 3)
    sub = df_liga[[col_h, col_a]].dropna().tail(350)
    if len(sub) < 25:
        return round(float(phi_default), 3)
    tot = pd.to_numeric(sub[col_h], errors="coerce") + pd.to_numeric(sub[col_a], errors="coerce")
    tot = tot.dropna()
    if len(tot) < 25:
        return round(float(phi_default), 3)
    media = float(tot.mean())
    var = float(tot.var(ddof=1))
    if media <= 0.1:
        return round(float(phi_default), 3)
    phi_emp = var / media
    # Suavizado ligero hacia el prior para evitar ruido extremo
    phi_suave = (phi_emp * 0.75) + (float(phi_default) * 0.25)
    return round(max(1.12, min(2.35, phi_suave)), 3)


def calibrar_ligas_desde_datos(df_europa=None, ruta_auditoria="auditoria_apuestas.csv", ruta_salida=ARCHIVO_CALIBRACION_LIGAS):
    """
    Calibra matemáticamente CADA liga por separado usando:
    - Sus propios CSV históricos (μ_H, μ_A, γ_localia, ρ_MLE, φ_corners, φ_faltas, φ_remates, φ_tarjetas)
    - Su rendimiento auditado real en auditoria_apuestas.csv (efectividad real, Brier Score, Log-Loss)
    RESPETA SIEMPRE "bloqueada_ok": true (jamás altera una liga ya bloqueada).
    """
    cal = cargar_calibracion_ligas(ruta_salida, forzar_disco=True)

    mapa_div = {
        "españa": ("SP1", None), "españa_2": ("SP2", None), "inglaterra": ("E0", None),
        "italia": ("I1", None), "alemania": ("D1", None), "francia": ("F1", None),
        "portugal": ("P1", None), "holanda": ("N1", None), "belgica": ("B1", None),
        "turquia": ("T1", None), "grecia": ("G1", None), "escocia": ("SC0", None),
        "colombia": (None, "colombia_historico.csv"),
        "argentina": (None, "argentina_historico.csv"),
        "brasil": (None, "brasil_historico.csv"),
        "arabia_saudita": (None, "arabia_historico.csv"),
    }

    resumen_consola = []
    for lk, (div_code, csv_local) in mapa_div.items():
        cfg = cal.setdefault(lk, dict(PERFILES_BASE_LIGAS.get(lk, PERFILES_BASE_LIGAS["francia"])))
        if cfg.get("bloqueada_ok"):
            resumen_consola.append((lk, "🔒 BLOQUEADA", cfg["mu_h"], cfg["mu_a"], cfg["rho_dc"], cfg["phi_corners"], cfg["phi_faltas"]))
            continue

        df_lg = pd.DataFrame()
        if div_code and df_europa is not None and not df_europa.empty and "Div" in df_europa.columns:
            df_lg = df_europa[df_europa["Div"] == div_code].copy()
        elif csv_local and os.path.exists(csv_local):
            try:
                df_lg = pd.read_csv(csv_local)
            except Exception:
                df_lg = pd.DataFrame()

        if not df_lg.empty and "FTHG" in df_lg.columns and "FTAG" in df_lg.columns:
            sub_g = df_lg[["FTHG", "FTAG"]].dropna().tail(380)
            if len(sub_g) >= 25:
                mu_h_new = round(max(0.95, min(2.10, float(sub_g["FTHG"].mean()))), 3)
                mu_a_new = round(max(0.70, min(1.75, float(sub_g["FTAG"].mean()))), 3)
                rho_new = estimar_rho_mle_liga(df_lg, mu_h_new, mu_a_new, rho_prior=PERFILES_BASE_LIGAS.get(lk, {}).get("rho_dc", -0.10))
                cfg["mu_h"] = mu_h_new
                cfg["mu_a"] = mu_a_new
                cfg["gamma_localia"] = round(math.log(mu_h_new / max(mu_a_new, 0.3)), 4)
                cfg["rho_dc"] = rho_new
                cfg["phi_corners"] = estimar_dispersion_phi_liga(df_lg, "HC", "AC", cfg.get("phi_corners", 1.48))
                cfg["phi_faltas"] = estimar_dispersion_phi_liga(df_lg, "HF", "AF", cfg.get("phi_faltas", 1.78))
                cfg["phi_remates"] = estimar_dispersion_phi_liga(df_lg, "HST", "AST", cfg.get("phi_remates", 1.36))
                cfg["phi_tarjetas"] = estimar_dispersion_phi_liga(df_lg, "HY", "AY", cfg.get("phi_tarjetas", 1.30))
                cfg["muestra_csv"] = int(len(sub_g))
                cfg["ultima_calibracion"] = datetime.now().strftime("%Y-%m-%d %H:%M")

        resumen_consola.append((lk, "✅ CALIBRADA", cfg["mu_h"], cfg["mu_a"], cfg["rho_dc"], cfg["phi_corners"], cfg["phi_faltas"]))

    # Medir Brier Score, Log-Loss y Efectividad real por liga desde auditoria_apuestas.csv (sin tocar filas!)
    if os.path.exists(ruta_auditoria):
        try:
            df_aud = pd.read_csv(ruta_auditoria, dtype=str)
            df_res = df_aud[df_aud["Estado"].isin(["Ganada", "Perdida", "Mitad Devuelta"])].copy()
            if not df_res.empty:
                etiquetas_a_key = {
                    "copa del rey": "copa_españa", "fa cup": "copa_inglaterra", "efl cup": "copa_inglaterra",
                    "coppa italia": "copa_italia", "dfb pokal": "copa_alemania", "coupe de france": "copa_francia",
                    "taça de portugal": "copa_portugal", "knvb beker": "copa_holanda",
                    "copa betplay": "copa_colombia", "copa argentina": "copa_argentina", "copa do brasil": "copa_brasil",
                    "libertadores": "COPA LIBERTADORES", "sudamericana": "COPA SUDAMERICANA",
                    "conference league": "UEFA CONFERENCE LEAGUE", "europa league": "UEFA EUROPA LEAGUE",
                    "champions": "UEFA CHAMPIONS LEAGUE",
                    "laliga": "españa", "segunda": "españa_2", "premier": "inglaterra",
                    "brasil": "brasil", "serie a": "italia", "bundesliga": "alemania", "ligue 1": "francia",
                    "primeira": "portugal", "eredivisie": "holanda", "saudi": "arabia_saudita",
                    "colombia": "colombia", "argentina": "argentina",
                    "mls": "usa", "liga mx": "mexico",
                }
                stats_aud = {}
                for _, r in df_res.iterrows():
                    # Excluir filas de boxscore contaminado anteriores al fix real (2026-11-24)
                    f_reg_cal = str(r.get("Fecha_Registro", ""))[:10]
                    m_cal_low = str(r.get("Mercado", "")).lower()
                    if f_reg_cal < "2026-11-24" and any(k_bx in m_cal_low for k_bx in ("córners", "corners", "remates", "faltas", "tarjetas", "amarill")):
                        continue
                    p_low = str(r.get("Partido", "")).lower()
                    lk_m = None
                    for tag_l, k_l in etiquetas_a_key.items():
                        if tag_l in p_low:
                            lk_m = k_l
                            break
                    if not lk_m:
                        continue
                    y_real = 1.0 if str(r.get("Estado")) in ("Ganada", "Mitad Devuelta") else 0.0
                    try:
                        p_pred = max(0.05, min(0.95, float(r.get("Probabilidad", 70.0)) / 100.0))
                    except Exception:
                        p_pred = 0.70
                    slot = stats_aud.setdefault(lk_m, {"n": 0, "ok": 0, "brier": 0.0, "logloss": 0.0})
                    slot["n"] += 1
                    slot["ok"] += int(y_real)
                    slot["brier"] += (p_pred - y_real) ** 2
                    slot["logloss"] += -(y_real * math.log(p_pred) + (1.0 - y_real) * math.log(1.0 - p_pred))

                for lk_m, st_a in stats_aud.items():
                    if lk_m in cal and st_a["n"] > 0:
                        cal[lk_m]["muestra_auditada"] = st_a["n"]
                        cal[lk_m]["efectividad_real_pct"] = round((st_a["ok"] / st_a["n"]) * 100.0, 1)
                        cal[lk_m]["brier_score"] = round(st_a["brier"] / st_a["n"], 4)
                        cal[lk_m]["log_loss"] = round(st_a["logloss"] / st_a["n"], 4)
        except Exception:
            pass

    guardar_calibracion_ligas(cal, ruta_salida)
    return cal, resumen_consola
