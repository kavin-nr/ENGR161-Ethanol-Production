from catalog import PUMP_OPTIONS, PUMP_HEIGHTS


class Pump:

    def __init__(self, tier, height, flowRate):

        # Pump specifications
        self.tier = tier
        self.height = height
        self.flowRate = flowRate  # m3/s

        # Retrieve specifications from catalog
        options = PUMP_OPTIONS[tier]

        self.efficiency = options["efficiency"]
        self.costPerM3perSec = options["costs"][PUMP_HEIGHTS.index(height)]

    def getEfficiency(self):
        return self.efficiency

    def getHeight(self):
        return self.height

    def getFlowRate(self):
        return self.flowRate

    def getCapitalCost(self):
        return self.costPerM3perSec * self.flowRate

    # Hydraulic energy required in J/day
    # Returns electrical energy in J/day
    def getEnergyInput(self, hydraulicEnergy):
        return hydraulicEnergy / self.efficiency

    # Energy dissipated by pump inefficiency in J/day
    def getEnergyLoss(self, hydraulicEnergy):
        energyInput = self.getEnergyInput(hydraulicEnergy)
        return energyInput * (1 - self.efficiency)

    # Electrical consumption in KWh/day

    # 1 KWh is 3.6 * 10^6 J. 
    def getEnergyKWh(self, hydraulicEnergy):
        return self.getEnergyInput(hydraulicEnergy) / (3.6 * 10**6)
