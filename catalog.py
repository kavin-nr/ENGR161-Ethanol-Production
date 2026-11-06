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