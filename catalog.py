
# catalog.py
# ENGR 161 - Project 2 Equipment Catalog
#
# All costs are in USD.
# Energy consumption is in kWh/day.
# Diameters and lengths are in meters.
# Flow rates are in m3/s.


# UNIT OPERATIONS
# Format: (efficiency, energy in kWh/day, cost per m3/s)

FERMENTER_OPTIONS = {
    "scrap": (0.50, 46600, 320000),
    "average": (0.75, 47200, 380000),
    "premium": (0.90, 47500, 460000),
    "world-class": (0.95, 48000, 1100000)
}

FILTER_OPTIONS = {
    "scrap": (0.50, 48800, 200000),
    "average": (0.75, 49536, 240000),
    "premium": (0.90, 50350, 280000),
    "world-class": (0.98, 51000, 480000)
}

DISTILLER_OPTIONS = {
    "scrap": (0.81, 47004, 390000),
    "average": (0.90, 47812, 460000),
    "premium": (0.915, 48200, 560000),
    "world-class": (0.98, 49500, 1370000)
}

DEHYDRATOR_OPTIONS = FILTER_OPTIONS


# PUMP CATALOG
# Efficiency and cost per m3/s for each height rating

PUMP_HEIGHTS = [6, 9, 12, 15, 18, 21, 24, 27, 30, 33, 36]

PUMP_OPTIONS = {
    "cheap": {
        "efficiency": 0.80,
        "costs": [200000, 220000, 240000, 260000,
                  290000, 320000, 350000, 390000,
                  420000, 470000, 510000]
    },
    "value": {
        "efficiency": 0.83,
        "costs": [240000, 260000, 290000, 310000,
                  350000, 380000, 420000, 460000,
                  510000, 560000, 620000]
    },
    "standard": {
        "efficiency": 0.86,
        "costs": [280000, 310000, 340000, 380000,
                  420000, 460000, 510000, 560000,
                  610000, 670000, 740000]
    },
    "high-grade": {
        "efficiency": 0.89,
        "costs": [340000, 380000, 410000, 460000,
                  500000, 550000, 610000, 670000,
                  740000, 810000, 890000]
    },
    "premium": {
        "efficiency": 0.92,
        "costs": [415000, 456000, 502000, 552000,
                  607000, 668000, 735000, 808000,
                  889000, 978000, 1076000]
    }
}


# LIQUID PIPE CATALOG
# Darcy friction factor and cost per meter by diameter

PIPE_OPTIONS = {
    "salvage": {
        "frictionFactor": 0.05,
        "costs": {
            0.10: 1000, 0.11: 1200, 0.12: 2570,
            0.13: 6300, 0.14: 14000, 0.15: 26000
        }
    },
    "questionable": {
        "frictionFactor": 0.03,
        "costs": {
            0.10: 1200, 0.11: 1440, 0.12: 3080,
            0.13: 7560, 0.14: 16000, 0.15: 31000
        }
    },
    "better": {
        "frictionFactor": 0.02,
        "costs": {
            0.10: 1440, 0.11: 1720, 0.12: 3700,
            0.13: 9070, 0.14: 20000, 0.15: 37000
        }
    },
    "nice": {
        "frictionFactor": 0.01,
        "costs": {
            0.10: 2160, 0.11: 2580, 0.12: 5550,
            0.13: 14000, 0.14: 29000, 0.15: 55000
        }
    },
    "outstanding": {
        "frictionFactor": 0.005,
        "costs": {
            0.10: 2700, 0.11: 3230, 0.12: 6940,
            0.13: 17000, 0.14: 37000, 0.15: 69000
        }
    },
    "glorious": {
        "frictionFactor": 0.002,
        "costs": {
            0.10: 2970, 0.11: 3550, 0.12: 7640,
            0.13: 19000, 0.14: 40000, 0.15: 76000
        }
    }
}


# DUCTWORK CATALOG
# Gas only; diameter (m): cost per meter ($/m)

DUCTWORK_FRICTION_FACTOR = 0.002

DUCTWORK_OPTIONS = {
    1.00: 228,
    1.25: 414,
    1.50: 700
}


# BEND CATALOG
# Angle (degrees), loss coefficient, and cost by diameter

BEND_OPTIONS = {
    20: {
        "lossCoefficient": 0.10,
        "costs": {
            0.10: 100, 0.11: 149, 0.12: 493,
            0.13: 1400, 0.14: 3200, 0.15: 6200
        }
    },
    30: {
        "lossCoefficient": 0.15,
        "costs": {
            0.10: 105, 0.11: 157, 0.12: 517,
            0.13: 1500, 0.14: 3400, 0.15: 6500
        }
    },
    45: {
        "lossCoefficient": 0.20,
        "costs": {
            0.10: 110, 0.11: 164, 0.12: 543,
            0.13: 1600, 0.14: 3600, 0.15: 6900
        }
    },
    60: {
        "lossCoefficient": 0.22,
        "costs": {
            0.10: 116, 0.11: 173, 0.12: 570,
            0.13: 1600, 0.14: 3800, 0.15: 7200
        }
    },
    75: {
        "lossCoefficient": 0.27,
        "costs": {
            0.10: 122, 0.11: 181, 0.12: 599,
            0.13: 1700, 0.14: 3900, 0.15: 7600
        }
    },
    90: {
        "lossCoefficient": 0.30,
        "costs": {
            0.10: 128, 0.11: 190, 0.12: 700,
            0.13: 1800, 0.14: 4100, 0.15: 8000
        }
    }
}


# VALVE CATALOG
# Loss coefficient and cost by diameter

VALVE_OPTIONS = {
    "salvage": {
        "lossCoefficient": 800,
        "costs": {
            0.10: 100, 0.11: 120, 0.12: 257,
            0.13: 630, 0.14: 1400, 0.15: 2600
        }
    },
    "questionable": {
        "lossCoefficient": 700,
        "costs": {
            0.10: 120, 0.11: 144, 0.12: 308,
            0.13: 756, 0.14: 1600, 0.15: 3100
        }
    },
    "outstanding": {
        "lossCoefficient": 600,
        "costs": {
            0.10: 270, 0.11: 323, 0.12: 694,
            0.13: 1700, 0.14: 3700, 0.15: 6900
        }
    },
    "glorious": {
        "lossCoefficient": 500,
        "costs": {
            0.10: 297, 0.11: 355, 0.12: 764,
            0.13: 1900, 0.14: 4000, 0.15: 7600
        }
    }
}
