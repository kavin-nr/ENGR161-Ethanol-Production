# (efficiency, energy in kWh/day, cost per m3/s)

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



# PIPE CATALOG
# Cost in $/m, diameter in m

PIPE_OPTIONS = {
    "salvage": {
        "frictionFactor": 0.05,
        "costs": {
            0.10: 1000,
            0.11: 1200,
            0.12: 2570,
            0.13: 6300,
            0.14: 14000,
            0.15: 26000
        }
    },
    "questionable": {
        "frictionFactor": 0.03,
        "costs": {
            0.10: 1200,
            0.11: 1440,
            0.12: 3080,
            0.13: 7560,
            0.14: 16000,
            0.15: 31000
        }
    },
    "better": {
        "frictionFactor": 0.02,
        "costs": {
            0.10: 1440,
            0.11: 1720,
            0.12: 3700,
            0.13: 9070,
            0.14: 20000,
            0.15: 37000
        }
    },
    "nice": {
        "frictionFactor": 0.01,
        "costs": {
            0.10: 2160,
            0.11: 2580,
            0.12: 5550,
            0.13: 14000,
            0.14: 29000,
            0.15: 55000
        }
    },
    "outstanding": {
        "frictionFactor": 0.005,
        "costs": {
            0.10: 2700,
            0.11: 3230,
            0.12: 6940,
            0.13: 17000,
            0.14: 37000,
            0.15: 69000
        }
    },
    "glorious": {
        "frictionFactor": 0.002,
        "costs": {
            0.10: 2970,
            0.11: 3550,
            0.12: 7640,
            0.13: 19000,
            0.14: 40000,
            0.15: 76000
        }
    }
}

# DUCTWORK CATALOG
# Fixed Darcy friction factor = 0.002

DUCTWORK_FRICTION_FACTOR = 0.002

DUCTWORK_OPTIONS = {
    1.00: 228,
    1.25: 414,
    1.50: 700
}