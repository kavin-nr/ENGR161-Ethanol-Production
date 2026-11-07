#!/usr/bin/env python3
"""
ENGR 16100 - Project 2: Ethanol plant model, Site 3 (rename XX to your team number)

What this does
--------------
1. Mass balance (fermenter -> filter -> distiller -> dehydrator) from the lecture equations,
   scaled so the plant makes 100,000 gal/day and the product is >= 98 wt% ethanol.
2. Energy balance: pump work to cover elevation + pipe friction + bends + valves
   (+ unit-operation internal losses), plus each unit operation's electrical kWh/day.
3. Capital cost from the parts catalog (+ Site 3 building with 10% tax).
4. Exhaustive search over equipment tiers and unit placements; for each, the best pipe /
   valve / pump choice per stream segment. Results are returned as a capital-vs-EROI
   Pareto front, and the report gives the agricultural waste needed per day.

Usage (from a terminal):
    python Proj2_FermModel_TeamXX.py                 # knee-point design + Pareto front
    python Proj2_FermModel_TeamXX.py --pick cost     # cheapest design
    python Proj2_FermModel_TeamXX.py --pick eroi     # highest-EROI design
    python Proj2_FermModel_TeamXX.py --min-eroi 11   # cheapest design with EROI >= 11
    python Proj2_FermModel_TeamXX.py --csv front.csv --plot
    python Proj2_FermModel_TeamXX.py --selfcheck     # run validation checks only

Every assumption you might want to change is in the ASSUMPTIONS block below.
"""
import argparse
import csv
import itertools
import math
import sys

import numpy as np

# =====================================================================================
# ASSUMPTIONS  (edit these; items marked CONFIRM should be checked with your instructor
#               or against the "Sample Values to Validate Model" spreadsheet)
# =====================================================================================
G = 9.81                      # m/s^2
GAL_TO_M3 = 3.78541e-3
KWH_TO_MJ = 3.6

OUTPUT_GAL_PER_DAY = 100_000  # required product volume
MIN_PURITY = 0.98             # required ethanol mass fraction in product
ETHANOL_MJ_PER_GAL = 80.1

FEED_COMP = {"sugar": 0.20, "water": 0.60, "fiber": 0.20}   # input slurry, wt fraction
ETH_FRAC_FROM_SUGAR = 0.51    # kg ethanol per kg sugar fermented (rest is CO2)

DENSITY = {"sugar": 1599.0, "ethanol": 789.0, "fiber": 1311.0, "water": 997.0}  # kg/m^3 (lecture)
CO2_DENSITY = 1.84            # kg/m^3 gas at ~25 C, 1 atm (ASSUMPTION)

# --- Site 3 -------------------------------------------------------------------------
BUILDING_PRICE = 1_600_000
BUILDING_TAX = 0.10           # Site 3 has +10% real-estate tax up front
INCLUDE_BUILDING_IN_CAPITAL = True       # CONFIRM (does not change the ranking, only the total)

FT = 0.3048
FLOOR_HEIGHT = 20 * FT        # floor-to-ceiling 20 ft
PORT_HEIGHT = 5 * FT          # pipe ports at mid-height of each 10-ft-tall unit (ASSUMPTION)
MIN_EXIT_HEIGHT = 3.0         # m; product AND waste must leave at >= 3 m
EXTERNAL_RUN = 3.0            # m horizontal run from a unit port to/from the outside wall (ASSUMPTION)
PORT_BENDS = 0                # extra 90-degree bends where pipes meet unit ports (ASSUMPTION)

# Only 4 unit-sized slots exist at Site 3 (one 20x20 ft unit per 30x20 floor of the tall
# section = 3 slots; the 25x20 ft side building holds 1; ground floor of tall + side
# building is 55 ft wide and fits exactly two units with the required 10-ft gap).
# (x, y) are slot centres in metres, floor = floor index (0 = ground).
SLOTS = {
    "side_G":  {"x": 10 * FT, "y": 10 * FT, "floor": 0},
    "tall_G":  {"x": 40 * FT, "y": 10 * FT, "floor": 0},
    "tall_F2": {"x": 40 * FT, "y": 10 * FT, "floor": 1},
    "tall_F3": {"x": 40 * FT, "y": 10 * FT, "floor": 2},   # <- mold issue on this floor
}

# --- Energy-model choices ------------------------------------------------------------
UNIT_INTERNAL_LOSS_FACTOR = 1.0   # CONFIRM: slide 33 says a unit's internal losses equal its inlet+outlet
                                  # valve losses. 1.0 => total valve-type head = 2x the valves' own head.
                                  # Set 0.0 if your instructor says the valves already ARE the internal losses.
ALLOW_SERIES_PUMPS = True         # CONFIRM: catalog pumps top out at 36 m but valve losses are often >36 m,
                                  # so pumps are allowed in series (cost and energy add up). If False, any
                                  # segment needing >36 m of head is infeasible.
PRICE_GAS_PUMP = False            # CONFIRM: CO2 leaves via ductwork. If True, a pump from the catalog is
                                  # priced for the (large) gas volume flow - this adds hundreds of $k.
GAS_FAN_EFF = 0.80                # used for CO2 energy when PRICE_GAS_PUMP is False (no fan capital)
MAX_HEAD = 3000.0                 # m; designs needing more are discarded as silly

# =====================================================================================
# PARTS CATALOG
# =====================================================================================
FERM = dict(names=["Scrap", "Average", "Premium", "World-class"],
            eff=[0.5, 0.75, 0.9, 0.95], price=[320e3, 380e3, 460e3, 1100e3],
            kwh=[46600, 47200, 47500, 48000])
DIST = dict(names=["Scrap", "Average", "Premium", "World-class"],
            eff=[0.81, 0.9, 0.915, 0.98], price=[390e3, 460e3, 560e3, 1370e3],
            kwh=[47004, 47812, 48200, 49500])
REMOVAL = dict(names=["Scrap", "Average", "Premium", "World-class"],   # filter AND dehydrator
               eff=[0.5, 0.75, 0.9, 0.98], price=[200e3, 240e3, 280e3, 480e3],
               kwh=[48800, 49536, 50350, 51000])

PUMP_TIERS = ["Cheap", "Value", "Standard", "High-Grade", "Premium"]
PUMP_EFF = np.array([0.80, 0.83, 0.86, 0.89, 0.92])
PUMP_RATING = np.arange(6, 37, 3)                   # m
PUMP_PRICE = np.array([                              # [rating][tier]  $ per m^3/s
    [200e3, 240e3, 280e3, 340e3, 415e3], [220e3, 260e3, 310e3, 380e3, 456e3],
    [240e3, 290e3, 340e3, 410e3, 502e3], [260e3, 310e3, 380e3, 460e3, 552e3],
    [290e3, 350e3, 420e3, 500e3, 607e3], [320e3, 380e3, 460e3, 550e3, 668e3],
    [350e3, 420e3, 510e3, 610e3, 735e3], [390e3, 460e3, 560e3, 670e3, 808e3],
    [420e3, 510e3, 610e3, 740e3, 889e3], [470e3, 560e3, 670e3, 810e3, 978e3],
    [510e3, 620e3, 740e3, 890e3, 1076e3]])

PIPE_CLASSES = ["Salvage", "Questionable", "Better", "Nice", "Outstanding", "Glorious"]
PIPE_F = np.array([0.05, 0.03, 0.02, 0.01, 0.005, 0.002])
DIAMETERS = np.array([0.10, 0.11, 0.12, 0.13, 0.14, 0.15])
PIPE_PRICE = np.array([                              # [diameter][class]  $/m
    [1000, 1200, 1440, 2160, 2700, 2970], [1200, 1440, 1720, 2580, 3230, 3550],
    [2570, 3080, 3700, 5550, 6940, 7640], [6300, 7560, 9070, 14000, 17000, 19000],
    [14000, 16000, 20000, 29000, 37000, 40000], [26000, 31000, 37000, 55000, 69000, 76000]], float)

BEND90_XI = 0.30                                     # 90-degree bends only (best coefficient per bend needed)
BEND90_PRICE = np.array([128, 190, 700, 1800, 4100, 8000], float)   # [diameter]

VALVE_TIERS = ["Salvage", "Questionable", "Outstanding", "Glorious"]
VALVE_K = np.array([800, 700, 600, 500], float)
VALVE_PRICE = np.array([                             # [diameter][tier]
    [100, 120, 270, 297], [120, 144, 323, 355], [257, 308, 694, 764],
    [630, 756, 1700, 1900], [1400, 1600, 3700, 4000], [2600, 3100, 6900, 7600]], float)

DUCT_D = np.array([1.0, 1.25, 1.5])
DUCT_PRICE = np.array([228.0, 414.0, 700.0])         # $/m, f = 0.002
DUCT_F = 0.002

# Pump "cover cost": cheapest set of series pumps (same tier) whose ratings sum to >= H.
_K_UNITS = int(MAX_HEAD // 3) + 1
_RU = (PUMP_RATING // 3).astype(int)


def _build_pump_cover():
    cost = np.zeros((len(PUMP_TIERS), _K_UNITS + 1))
    choice = np.zeros((len(PUMP_TIERS), _K_UNITS + 1), int)
    for t in range(len(PUMP_TIERS)):
        for k in range(1, _K_UNITS + 1):
            best, bi = math.inf, 0
            for ri, ru in enumerate(_RU):
                if not ALLOW_SERIES_PUMPS and k > _RU[-1]:
                    continue
                c = PUMP_PRICE[ri, t] + cost[t, max(0, k - ru)]
                if c < best:
                    best, bi = c, ri
            cost[t, k], choice[t, k] = best, bi
    return cost, choice


PUMP_COVER, PUMP_CHOICE = _build_pump_cover()


def pump_set(tier, head):
    """Ratings (m) of the series pumps chosen to cover `head` metres."""
    k, out = int(math.ceil(head / 3 - 1e-9)), []
    while k > 0:
        ri = PUMP_CHOICE[tier, k]
        out.append(int(PUMP_RATING[ri]))
        k -= _RU[ri]
    return out


# =====================================================================================
# PHYSICS HELPERS (equations from lecture)
# =====================================================================================
def head_friction(f, Q, L, D):
    return f * 8 * Q ** 2 * L / (math.pi ** 2 * G * D ** 5) if np.isscalar(D) else \
        f * 8 * Q ** 2 * L / (np.pi ** 2 * G * D ** 5)


def head_minor(K, Q, D):
    """K*v^2/(2g) for a bend (xi) or valve (K); v = Q / (pi r^2)."""
    v = Q / (np.pi * D ** 2 / 4)
    return K * v ** 2 / (2 * G)


def mix_density(comp):
    """Mass-fraction-weighted density used in the lecture slides. comp: kg/s by component."""
    tot = sum(comp.values())
    return sum(comp[c] * DENSITY[c] for c in comp) / tot


# =====================================================================================
# MASS BALANCE
# =====================================================================================
def mass_balance(eta_ferm, eta_filt, eta_dist, eta_dehy, feed=1.0):
    """All flows in kg/s for a given feed rate (kg/s). Follows Lecture 2 slides 7-15."""
    s0, w0, f0 = (FEED_COMP[c] * feed for c in ("sugar", "water", "fiber"))
    feed_s = dict(sugar=s0, water=w0, fiber=f0)

    # Fermenter: water/fiber pass; sugar partly converted
    eth = ETH_FRAC_FROM_SUGAR * eta_ferm * s0
    co2 = (1 - ETH_FRAC_FROM_SUGAR) * eta_ferm * s0
    ferm = dict(sugar=s0 * (1 - eta_ferm), ethanol=eth, water=w0, fiber=f0)

    # Filter: removes fiber only
    filt = dict(ferm)
    filt["fiber"] = ferm["fiber"] * (1 - eta_filt)
    w_filt = dict(fiber=ferm["fiber"] * eta_filt)

    # Distiller: all ethanol passes; others scaled per the provided formula
    others = filt["water"] + filt["sugar"] + filt["fiber"]
    k = filt["ethanol"] * (1 / eta_dist - 1) / others
    dist = dict(ethanol=filt["ethanol"], water=filt["water"] * k,
                sugar=filt["sugar"] * k, fiber=filt["fiber"] * k)
    w_dist = {c: filt[c] - dist[c] for c in ("water", "sugar", "fiber")}

    # Dehydrator: removes water
    prod = dict(dist)
    prod["water"] = dist["water"] * (1 - eta_dehy)
    w_dehy = dict(water=dist["water"] * eta_dehy)

    M_prod = sum(prod.values())
    return dict(feed=feed_s, ferm=ferm, filt=filt, dist=dist, prod=prod,
                co2=co2, w_filt=w_filt, w_dist=w_dist, w_dehy=w_dehy,
                M_prod=M_prod, purity=prod["ethanol"] / M_prod)


def scaled_flows(etas):
    """Return mass balance scaled to the required output, or None if purity fails."""
    base = mass_balance(*etas, feed=1.0)
    if base["purity"] < MIN_PURITY - 1e-12:
        return None
    rho_prod = mix_density(base["prod"])
    M_needed = rho_prod * OUTPUT_GAL_PER_DAY * GAL_TO_M3 / 86400.0       # kg/s
    feed_rate = M_needed / base["M_prod"]
    return mass_balance(*etas, feed=feed_rate)


def balance_residual(mb):
    """Total mass in minus total mass out (should be ~0)."""
    mi = sum(mb["feed"].values())
    mo = sum(mb["prod"].values()) + mb["co2"] + sum(mb["w_filt"].values()) + \
        sum(mb["w_dist"].values()) + sum(mb["w_dehy"].values())
    return mi - mo


# =====================================================================================
# GEOMETRY: slots, segments
# =====================================================================================
def port_z(slot):
    return SLOTS[slot]["floor"] * FLOOR_HEIGHT + PORT_HEIGHT


def route(dx, dy, dz):
    comps = [abs(dx), abs(dy), abs(dz)]
    axes = sum(c > 1e-9 for c in comps)
    return sum(comps), max(axes - 1, 0) + PORT_BENDS


def build_segments(mb, layout):
    """layout = tuple of 4 slot names for (fermenter, filter, distiller, dehydrator)."""
    pz = [port_z(s) for s in layout]
    xy = [(SLOTS[s]["x"], SLOTS[s]["y"]) for s in layout]
    segs = []

    def dens(c):
        return mix_density(c)

    def mk(name, comp, kind, vec, nvalves, mass=None):
        m = sum(comp.values()) if mass is None else mass
        rho = dens(comp) if kind == "liquid" else CO2_DENSITY
        L, nb = route(*vec)
        segs.append(dict(name=name, kind=kind, mass=m, rho=rho, Q=m / rho, L=L,
                         n_bends=0 if kind == "gas" else nb, dz=vec[2], n_valves=nvalves))

    # main line
    mk("feed -> fermenter", mb["feed"], "liquid", (EXTERNAL_RUN, 0, pz[0]), 1)
    for i, (a, b, key) in enumerate([(0, 1, "ferm"), (1, 2, "filt"), (2, 3, "dist")]):
        mk(f"{['fermenter','filter','distiller'][i]} -> {['filter','distiller','dehydrator'][i]}",
           mb[key], "liquid",
           (xy[b][0] - xy[a][0], xy[b][1] - xy[a][1], pz[b] - pz[a]), 2)
    ze = max(pz[3], MIN_EXIT_HEIGHT)
    mk("dehydrator -> product exit", mb["prod"], "liquid", (EXTERNAL_RUN, 0, ze - pz[3]), 1)

    # waste streams (pumped, no extra valves)
    for name, comp, u in [("filter waste (fiber)", mb["w_filt"], 1),
                          ("distiller waste", mb["w_dist"], 2),
                          ("dehydrator waste (water)", mb["w_dehy"], 3)]:
        ze = max(pz[u], MIN_EXIT_HEIGHT)
        mk(name, comp, "liquid", (EXTERNAL_RUN, 0, ze - pz[u]), 0)
    ze = max(pz[0], MIN_EXIT_HEIGHT)
    mk("CO2 duct (fermenter)", {"co2": mb["co2"]}, "gas", (EXTERNAL_RUN, 0, ze - pz[0]), 0,
       mass=mb["co2"])
    return segs


def unit_flows(mb):
    """Volumetric flow INTO each unit operation (m^3/s) - used to price the units."""
    return [sum(mb["feed"].values()) / mix_density(mb["feed"]),
            sum(mb["ferm"].values()) / mix_density(mb["ferm"]),
            sum(mb["filt"].values()) / mix_density(mb["filt"]),
            sum(mb["dist"].values()) / mix_density(mb["dist"])]


# =====================================================================================
# SEGMENT OPTIMISATION (vectorised) + PARETO TOOLS
# =====================================================================================
_PI, _DI, _VI, _TI = (a.ravel() for a in np.meshgrid(
    range(len(PIPE_F)), range(len(DIAMETERS)), range(len(VALVE_K)), range(len(PUMP_EFF)),
    indexing="ij"))


def pareto_mask(C, E):
    order = np.lexsort((E, C))
    Es = E[order]
    cm = np.minimum.accumulate(Es)
    keep = np.ones(len(Es), bool)
    keep[1:] = Es[1:] < cm[:-1] - 1e-9
    mask = np.zeros(len(C), bool)
    mask[order[keep]] = True
    return mask


def segment_front(seg):
    """Pareto front (capital $, energy kWh/day) of all pipe/valve/pump choices for one segment."""
    Q, rho, L, nb, nv, dz = seg["Q"], seg["rho"], seg["L"], seg["n_bends"], seg["n_valves"], seg["dz"]
    if seg["kind"] == "gas":
        D = DUCT_D
        H = np.maximum(dz + head_friction(DUCT_F, Q, L, D), 0.0)
        eta = 0.92 if PRICE_GAS_PUMP else GAS_FAN_EFF
        energy = rho * G * Q * H / eta * 24 / 1000.0
        cost = DUCT_PRICE * L
        if PRICE_GAS_PUMP:
            k = np.ceil(H / 3 - 1e-9).astype(int)
            cost = cost + PUMP_COVER[4, np.minimum(k, _K_UNITS)] * Q
        m = pareto_mask(cost, energy)
        idx = np.nonzero(m)[0]
        return cost[idx], energy[idx], idx[:, None], dict(kind="gas")

    sel = (_VI == 0) if nv == 0 else np.ones(len(_PI), bool)
    pi, di, vi, ti = _PI[sel], _DI[sel], _VI[sel], _TI[sel]
    D = DIAMETERS[di]
    Hf = head_friction(PIPE_F[pi], Q, L, D)
    Hb = nb * head_minor(BEND90_XI, Q, D)
    Hv = nv * (1 + UNIT_INTERNAL_LOSS_FACTOR) * head_minor(VALVE_K[vi], Q, D)
    H = np.maximum(dz + Hf + Hb + Hv, 0.0)
    k = np.ceil(H / 3 - 1e-9).astype(int)
    ok = (k <= _K_UNITS) & (H <= MAX_HEAD)
    kk = np.minimum(k, _K_UNITS)
    pump_cost = PUMP_COVER[ti, kk] * Q
    ok &= np.isfinite(pump_cost)
    cost = L * PIPE_PRICE[di, pi] + nb * BEND90_PRICE[di] + nv * VALVE_PRICE[di, vi] + pump_cost
    energy = rho * G * Q * H / PUMP_EFF[ti] * 24 / 1000.0
    if not ok.any():
        return None
    idx_all = np.nonzero(sel)[0][ok]
    cost, energy = cost[ok], energy[ok]
    m = pareto_mask(cost, energy)
    keep = np.nonzero(m)[0]
    return cost[keep], energy[keep], idx_all[keep][:, None], dict(kind="liquid")


def combine(fa, fb):
    ca, ea, ia = fa
    cb, eb, ib = fb
    C = (ca[:, None] + cb[None, :]).ravel()
    E = (ea[:, None] + eb[None, :]).ravel()
    m = pareto_mask(C, E)
    idx = np.nonzero(m)[0]
    a_idx, b_idx = idx // len(cb), idx % len(cb)
    return C[idx], E[idx], np.hstack([ia[a_idx], ib[b_idx]])


def design_front(segs):
    fronts = []
    for s in segs:
        r = segment_front(s)
        if r is None:
            return None
        fronts.append(r[:3])
    acc = fronts[0]
    for f in fronts[1:]:
        acc = combine(acc, f)
    return acc


# =====================================================================================
# FULL SEARCH
# =====================================================================================
def equipment_costs(etas_idx, uf):
    i, j, k, l = etas_idx
    cap = (FERM["price"][i] * uf[0] + REMOVAL["price"][j] * uf[1] +
           DIST["price"][k] * uf[2] + REMOVAL["price"][l] * uf[3])
    kwh = FERM["kwh"][i] + REMOVAL["kwh"][j] + DIST["kwh"][k] + REMOVAL["kwh"][l]
    return cap, kwh


E_ETHANOL_KWH = OUTPUT_GAL_PER_DAY * ETHANOL_MJ_PER_GAL / KWH_TO_MJ      # kWh/day of fuel energy
BUILDING = BUILDING_PRICE * (1 + BUILDING_TAX) if INCLUDE_BUILDING_IN_CAPITAL else 0.0


def search(verbose=True):
    cases, C_all, E_all, I_all, owner = [], [], [], [], []
    layouts = list(itertools.permutations(SLOTS.keys()))
    combos = list(itertools.product(range(4), repeat=4))
    n_feasible = 0
    for ci, (i, j, k, l) in enumerate(combos):
        etas = (FERM["eff"][i], REMOVAL["eff"][j], DIST["eff"][k], REMOVAL["eff"][l])
        mb = scaled_flows(etas)
        if mb is None:
            continue
        n_feasible += 1
        uf = unit_flows(mb)
        ucap, ukwh = equipment_costs((i, j, k, l), uf)
        for lay in layouts:
            segs = build_segments(mb, lay)
            fr = design_front(segs)
            if fr is None:
                continue
            c, e, idx = fr
            cases.append(((i, j, k, l), lay))
            C_all.append(c + ucap + BUILDING)
            E_all.append(e + ukwh)
            I_all.append(idx)
            owner.append(np.full(len(c), len(cases) - 1))
        if verbose and n_feasible % 10 == 0:
            print(f"  ...searched {n_feasible} purity-feasible equipment sets", file=sys.stderr)
    C, E = np.concatenate(C_all), np.concatenate(E_all)
    O, I = np.concatenate(owner), np.vstack(I_all)
    m = pareto_mask(C, E)
    sel = np.nonzero(m)[0]
    order = sel[np.argsort(C[sel])]
    pts = [dict(capital=C[n], energy_kwh=E[n], eroi=E_ETHANOL_KWH / E[n],
                case=cases[O[n]], choices=I[n]) for n in order]
    return pts, n_feasible, len(cases)


def pick_point(pts, how="knee", min_eroi=None):
    cand = [p for p in pts if (min_eroi is None or p["eroi"] >= min_eroi)]
    if not cand:
        raise SystemExit(f"No design reaches EROI >= {min_eroi}. Max EROI is "
                         f"{max(p['eroi'] for p in pts):.2f}.")
    if min_eroi is not None or how == "cost":
        return min(cand, key=lambda p: p["capital"])
    if how == "eroi":
        return max(cand, key=lambda p: p["eroi"])
    c = np.array([p["capital"] for p in cand])
    r = np.array([p["eroi"] for p in cand])
    cn = (c - c.min()) / (np.ptp(c) or 1)
    rn = (r.max() - r) / (np.ptp(r) or 1)
    return cand[int(np.argmin(np.hypot(cn, rn)))]


# =====================================================================================
# REPORT
# =====================================================================================
def describe(p):
    (i, j, k, l), lay = p["case"]
    etas = (FERM["eff"][i], REMOVAL["eff"][j], DIST["eff"][k], REMOVAL["eff"][l])
    mb = scaled_flows(etas)
    uf = unit_flows(mb)
    ucap, ukwh = equipment_costs((i, j, k, l), uf)
    segs = build_segments(mb, lay)
    lines = []
    feed_kg_s = sum(mb["feed"].values())
    feed_m3_day = uf[0] * 86400
    lines += ["=" * 78, "RECOMMENDED DESIGN (Site 3)", "=" * 78,
              f"Equipment : fermenter={FERM['names'][i]} (eff {etas[0]}), filter={REMOVAL['names'][j]} "
              f"(eff {etas[1]}), distiller={DIST['names'][k]} (eff {etas[2]}), "
              f"dehydrator={REMOVAL['names'][l]} (eff {etas[3]})",
              "Placement : " + ", ".join(f"{n}->{s}" for n, s in
                                         zip(["fermenter", "filter", "distiller", "dehydrator"], lay)),
              f"Product   : {OUTPUT_GAL_PER_DAY:,} gal/day at {100 * mb['purity']:.2f} wt% ethanol "
              f"({mb['M_prod']:.3f} kg/s)", "",
              "AGRICULTURAL WASTE (corn slurry) NEEDED",
              f"  {feed_kg_s:,.2f} kg/s = {feed_kg_s * 86400 / 1000:,.0f} tonnes/day "
              f"= {feed_m3_day:,.0f} m^3/day = {feed_m3_day / GAL_TO_M3:,.0f} gal/day", ""]

    seg_cost_total, seg_kwh_total, rows = 0.0, 0.0, []
    for n, s in enumerate(segs):
        ch = p["choices"][n]
        if s["kind"] == "gas":
            D = DUCT_D[ch]
            H = max(s["dz"] + head_friction(DUCT_F, s["Q"], s["L"], D), 0)
            cost = DUCT_PRICE[ch] * s["L"]
            eta = GAS_FAN_EFF
            if PRICE_GAS_PUMP:
                eta = 0.92
                cost += PUMP_COVER[4, min(int(math.ceil(H / 3 - 1e-9)), _K_UNITS)] * s["Q"]
            kwh = s["rho"] * G * s["Q"] * H / eta * 24 / 1000
            desc = f"duct D={D} m, f=0.002"
        else:
            pi, di, vi, ti = _PI[ch], _DI[ch], _VI[ch], _TI[ch]
            D = DIAMETERS[di]
            Hf = head_friction(PIPE_F[pi], s["Q"], s["L"], D)
            Hb = s["n_bends"] * head_minor(BEND90_XI, s["Q"], D)
            Hv = s["n_valves"] * (1 + UNIT_INTERNAL_LOSS_FACTOR) * head_minor(VALVE_K[vi], s["Q"], D)
            H = max(s["dz"] + Hf + Hb + Hv, 0)
            cost = (s["L"] * PIPE_PRICE[di, pi] + s["n_bends"] * BEND90_PRICE[di] +
                    s["n_valves"] * VALVE_PRICE[di, vi] + PUMP_COVER[ti, int(math.ceil(H / 3 - 1e-9))] * s["Q"])
            kwh = s["rho"] * G * s["Q"] * H / PUMP_EFF[ti] * 24 / 1000
            vtxt = f", {s['n_valves']}x {VALVE_TIERS[vi]} valve (K={VALVE_K[vi]:.0f})" if s["n_valves"] else ""
            desc = (f"D={D:.2f} m {PIPE_CLASSES[pi]} pipe (f={PIPE_F[pi]}){vtxt}, {s['n_bends']} bend(s); "
                    f"head: lift {s['dz']:.1f} + fric {Hf:.1f} + bends {Hb:.1f} + valves {Hv:.1f} = {H:.1f} m; "
                    f"pumps {pump_set(ti, H)} m ({PUMP_TIERS[ti]})")
        seg_cost_total += cost
        seg_kwh_total += kwh
        rows.append(f"  {s['name']:<28} Q={s['Q']:.4f} m^3/s L={s['L']:.1f} m | {desc} "
                    f"| ${cost:,.0f}, {kwh:,.0f} kWh/day")

    lines += ["SEGMENT DESIGN (pipes, valves, bends, pumps)"] + rows + [""]
    lines += ["CAPITAL COST",
              f"  Building (incl. 10% tax)  : ${BUILDING:,.0f}",
              f"  Unit operations           : ${ucap:,.0f}",
              f"  Piping/valves/bends/pumps : ${seg_cost_total:,.0f}",
              f"  TOTAL                     : ${BUILDING + ucap + seg_cost_total:,.0f}", "",
              "ENERGY",
              f"  Unit operations           : {ukwh:,.0f} kWh/day",
              f"  Pumps/fans                : {seg_kwh_total:,.0f} kWh/day",
              f"  TOTAL electricity         : {ukwh + seg_kwh_total:,.0f} kWh/day",
              f"  Ethanol energy out        : {E_ETHANOL_KWH:,.0f} kWh/day "
              f"({OUTPUT_GAL_PER_DAY * ETHANOL_MJ_PER_GAL:,.0f} MJ/day)",
              f"  ENERGY RETURN ON INVESTMENT: {E_ETHANOL_KWH / (ukwh + seg_kwh_total):.2f}x", "",
              f"Mass balance residual (in - out): {balance_residual(mb):.2e} kg/s"]
    top = [n for n, s in zip(["fermenter", "filter", "distiller", "dehydrator"], lay) if s == "tall_F3"]
    if top:
        lines.append(f"NOTE: the {top[0]} sits on Site 3's top floor, which has a mold issue "
                     f"(remediation cost is NOT in this model).")
    return "\n".join(lines)


# =====================================================================================
# SELF-CHECKS (validation against lecture examples + conservation)
# =====================================================================================
def selfcheck():
    ok = True

    def check(name, got, want, tol=0.01):
        nonlocal ok
        good = abs(got - want) <= tol * abs(want)
        ok &= good
        print(f"[{'PASS' if good else 'FAIL'}] {name}: got {got:.4g}, expected {want:.4g}")

    check("Darcy-Weisbach example (slide 24)", head_friction(0.1, 0.06, 100, 0.1), 297)
    check("Bend example (slide 30)", head_minor(2.0, 0.06, 0.1), 5.95)
    check("Valve example (slide 34)", head_minor(800, 0.06, 0.1), 2385, tol=0.01)
    d = 0.15 * 1599 + 0.35 * 997 + 0.28 * 1311 + 0.22 * 789
    check("Density example (slide 16)", d, 1129, tol=0.005)
    for etas in [(0.5, 0.5, 0.81, 0.5), (0.95, 0.98, 0.98, 0.98), (0.9, 0.9, 0.915, 0.9)]:
        mb = mass_balance(*etas)
        res = balance_residual(mb)
        good = abs(res) < 1e-12
        ok &= good
        print(f"[{'PASS' if good else 'FAIL'}] mass closes for etas={etas}: residual {res:.1e}")
    mb = scaled_flows((0.95, 0.98, 0.98, 0.98))
    q_out = sum(mb["prod"].values()) / mix_density(mb["prod"]) * 86400 / GAL_TO_M3
    check("scaled product volume (gal/day)", q_out, OUTPUT_GAL_PER_DAY, tol=1e-6)
    n_pass = sum(scaled_flows((FERM["eff"][i], REMOVAL["eff"][j], DIST["eff"][k], REMOVAL["eff"][l]))
                 is not None for i, j, k, l in itertools.product(range(4), repeat=4))
    print(f"[INFO] {n_pass} of 256 equipment combinations reach {MIN_PURITY:.0%} purity")
    print("ALL CHECKS PASSED" if ok else "SOME CHECKS FAILED")
    return ok


# =====================================================================================
def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--pick", choices=["knee", "cost", "eroi"], default="knee")
    ap.add_argument("--min-eroi", type=float, default=None,
                    help="cheapest design whose EROI is at least this value")
    ap.add_argument("--csv", help="write the Pareto front to this CSV file")
    ap.add_argument("--plot", action="store_true", help="show/save the capital-vs-EROI Pareto plot")
    ap.add_argument("--selfcheck", action="store_true")
    a = ap.parse_args()

    if a.selfcheck:
        sys.exit(0 if selfcheck() else 1)

    pts, n_feas, n_cases = search()
    print(f"\n{n_feas} of 256 equipment sets meet purity; {n_cases} (equipment x layout) cases searched; "
          f"{len(pts)} Pareto-optimal designs.\n")
    print(f"Cheapest design : ${pts[0]['capital']:,.0f}  EROI {pts[0]['eroi']:.2f}")
    print(f"Best-EROI design: ${pts[-1]['capital']:,.0f}  EROI {pts[-1]['eroi']:.2f}\n")
    best = pick_point(pts, a.pick, a.min_eroi)
    print(describe(best))

    if a.csv:
        with open(a.csv, "w", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(["capital_usd", "electricity_kwh_day", "eroi", "equipment_tiers(ferm,filt,dist,dehy)", "layout"])
            for p in pts:
                w.writerow([f"{p['capital']:.0f}", f"{p['energy_kwh']:.0f}", f"{p['eroi']:.3f}",
                            p["case"][0], "|".join(p["case"][1])])
        print(f"\nPareto front written to {a.csv}")
    if a.plot:
        try:
            import matplotlib.pyplot as plt
            plt.figure(figsize=(7, 4.5))
            plt.plot([p["capital"] / 1e6 for p in pts], [p["eroi"] for p in pts], "o-", ms=3)
            plt.plot(best["capital"] / 1e6, best["eroi"], "r*", ms=14, label="selected design")
            plt.xlabel("Capital cost ($ million)")
            plt.ylabel("Energy return on investment (x)")
            plt.title("Site 3: Pareto front")
            plt.legend()
            plt.grid(alpha=.3)
            plt.tight_layout()
            plt.savefig("pareto_site3.png", dpi=200)
            print("Saved pareto_site3.png")
            plt.show()
        except ImportError:
            print("matplotlib not installed; skipping plot")


if __name__ == "__main__":
    main()
