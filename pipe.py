from utils import energyLostToFriction, calcFluidVelocity

class Pipe:

    def __init__(self, length, diameter, frictionFactor,
        costPerMeter, flowRate, density):

        self.length = length
        self.diameter = diameter
        self.frictionFactor = frictionFactor
        self.costPerMeter = costPerMeter

        self.flowRate = flowRate
        self.density = density

    def getCapitalCost(self):
        return self.costPerMeter * self.length

    def getVelocity(self):
        return calcFluidVelocity(self.flowRate, self.diameter)

    def getFluidMass(self):
        return self.density * self.flowRate * 86400

    def getEnergyLoss(self):
        return energyLostToFriction(
            self.getFluidMass(),
            self.frictionFactor,
            self.length,
            self.diameter,
            self.flowRate
        )
