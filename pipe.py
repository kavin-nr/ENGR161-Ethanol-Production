from utils import (energyLostToFriction, calcFluidVelocity, SECONDS_PER_DAY,
                   energyLostToBend, energyLostToValve)
from catalog import (PIPE_OPTIONS, DUCTWORK_OPTIONS, DUCTWORK_FRICTION_FACTOR,
                     BEND_OPTIONS, VALVE_OPTIONS)

class Pipe:

    def __init__(self, length, diameter, tier, flowRate, density, 
                 bends=None, valves=None):

        self.length = length
        self.diameter = diameter
        self.flowRate = flowRate
        self.density = density

        # Found it much easier to grab stuff from the catalog directly here
        # Keep it all contained rather than putting it in main.py
        options = PIPE_OPTIONS[tier]

        self.frictionFactor = options["frictionFactor"] # Darcy-Weisbach
        self.costPerMeter = options["costs"][diameter] # $ / m

        self.bends = bends if bends is not  None else []
        self.valves = valves if valves is not None else []


    # total cost from bends and valves
    def getFittingsCost(self):
        cost = 0
        for angle in self.bends:
            cost += BEND_OPTIONS[angle]["costs"][self.diameter]

        for tier in self.valves:
            cost += VALVE_OPTIONS[tier]["costs"][self.diameter]
        return cost

    # cost of a pipe includes bends and valves
    def getCapitalCost(self):
        return self.costPerMeter * self.length + self.getFittingsCost()

    def getVelocity(self):
        return calcFluidVelocity(self.flowRate, self.diameter)

    def getFluidMass(self):
        return self.density * self.flowRate * SECONDS_PER_DAY

    def getFrictionLoss(self):

        # If I haven't expressed my dislike for the 80 character limit before,
        # I do here.
        return energyLostToFriction(
            self.getFluidMass(),
            self.frictionFactor,
            self.length,
            self.diameter,
            self.flowRate
        )

    def getFittingsLoss(self):
        mass = self.getFluidMass()
        velocity = self.getVelocity()
        loss = 0

        for angle in self.bends:
            coefficient = BEND_OPTIONS[angle]["lossCoefficient"]
            loss += energyLostToBend(mass, coefficient, velocity)

        for tier in self.valves:
            coefficient = VALVE_OPTIONS[tier]["lossCoefficient"]
            loss += energyLostToValve(mass, coefficient, velocity)

        return loss

    # Energy loss for a given pipe system is friction + fittings (for now)
    # i need to add gravitational potential energy
    def getEnergyLoss(self):
        return self.getFrictionLoss() + self.getFittingsLoss()

# If you think about it, ducts are basically pipes with a few caveats
# Just made sense to just have it as a child class 

class Duct(Pipe):

    def __init__(self, length, diameter, flowRate, density):

        self.length = length
        self.diameter = diameter
        self.flowRate = flowRate
        self.density = density
        self.frictionFactor = DUCTWORK_FRICTION_FACTOR
        self.costPerMeter = DUCTWORK_OPTIONS[diameter]

        # even though ducts don't have fittings,
        # its parent class is Pipe which uses fitting functions for 
        # energy loss calculations
        self.bends = []
        self.valves = []

    
    # IMPORTANT TO NOTE: Darcy-Weisbach deals with the flow of incompressible
    # fluids. CO2 (going through these ducts) is a gas, so it's compressible.
    # So we probably can neglect the energyLostToFriction in these ducts. 

    # Also, the validation model says it neglects waste pipe friction. I'm 
    # just going to go with that for now. 


def createPipes(configs, units, initialFlowRate, initialDensity):
    pipes = []
    for length, diameter, tier, source, bends, valves, in configs:
        duct = False
        # If the pipe is coming from somewhere, then use its output flow
        if source is not None:
            match source:
                case "fermenter":
                    id = 0
                case "filter":
                    id = 1
                case "distiller":
                    id = 2
                case "dehydrator":
                    id = 3
                case "fermenter-waste":
                    id = 4
                    duct = True
                case "filter-waste":
                    id = 5
                case "distiller-waste":
                    id = 6
                case "dehydrator-waste":
                    id = 7
                case _:
                    raise Exception("Unknown pipe source")

            if 0 <= id <= 3:
                flowRate = units[id].getOutputFlowRate()
                density = units[id].getOutputDensity()

            else:                  
                flowRate = units[id - 4].getWasteFlowRate()
                density = units[id - 4].getWasteDensity()

        # Initial slurry pipe, so initial slurry flow
        else:
            flowRate = initialFlowRate
            density = initialDensity

        if not duct:
            # Make a pipe obejct
            pipe = Pipe(
                length=length,
                diameter=diameter,
                tier=tier,
                flowRate=flowRate,
                density=density,
                bends=bends,
                valves=valves
            )
        else:
            pipe = Duct(
                length=length,
                diameter=diameter,
                flowRate=flowRate,
                density=density
            )

        pipes.append(pipe)

    return pipes