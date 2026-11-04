# Parent class for all 4 units
class Unit:

    # Note the order: sugar, ethanol, fibrous, then water
    def __init__(self, efficiency, energy_needed, 
            sugarMass, ethanolMass, fibrousMass, waterMass):
        
        self.efficiency = efficiency        # Actual efficiency of the machine
        self.energy_needed = energy_needed  # Energy input for the machine

        self.sugar = sugarMass
        self.ethanol = ethanolMass
        self.fibrous = fibrousMass
        self.water = waterMass

    def getSugar(self):
        return self.sugar

    def getEthanol(self):
        return self.ethanol

    def getWater(self):
        return self.water

    def getFibrous(self):
        return self.fibrous

    def getEnergy(self):
        return self.energy_needed

    # Returned as a state vector for easy transfer into next machine
    def getOutputs(self):
        return [self.getSugar(), self.getEthanol(), 
            self.getFibrous(), self.getWater()]

    # Total mass flow?
    def getTotalMassOutput(self):
        return sum(self.getOutputs())

    def getOutputMassFractions(self):
        total = self.getTotalMassOutput()
        return [mass / total for mass in self.getOutputs()]

    # Will be returned as a decimal
    def getOutputPurity(self):
        return self.getEthanol() / self.getTotalMassOutput()

    # Nothing generates CO2 except for the fermenter
    def getCO2(self):
        return 0 


# Sugar is converted to ethanol and co2, everything else remains
class Fermenter(Unit):
    
    def __init__(self, *args):
        super().__init__(*args)

        self.SUGAR_TO_ETHANOL = 0.51
        self.SUGAR_TO_CO2 = 1 - self.SUGAR_TO_ETHANOL


    def getSugar(self):
        return self.sugar * (1 - self.efficiency)

    def getEthanol(self): # Incoming ethanol is 0, but just for good standard
        generatedEthanol = self.SUGAR_TO_ETHANOL * self.sugar * self.efficiency
        return self.ethanol + generatedEthanol
    
    # Waste
    def getCO2(self):
        return self.SUGAR_TO_CO2 * self.sugar * self.efficiency


# Fibrous material is taken out
class Filter(Unit):
    def __init__(self, *args):
        super().__init__(*args)

    def getFibrous(self):
        return self.fibrous * (1 - self.efficiency)


# Ethanol remains, but removes water, sugar, and fibrous material
class Distiller(Unit):
    def __init__(self, *args):
        super().__init__(*args)

        # Only doing this to stay within the 80 char/line limit
        self.numer = (self.ethanol * ((1/self.efficiency) - 1))
        self.denom = (self.water + self.sugar + self.fibrous)

    def getSugar(self):
        return self.sugar * self.numer / self.denom
    
    def getWater(self):
        return self.water * self.numer / self.denom
    
    def getFibrous(self):
        return self.fibrous * self.numer / self.denom


# Water is removed, everything else remains
class Dehydrator(Unit):
    def __init__(self, *args):
        super().__init__(*args)

    def getWater(self):
        return (1 - self.efficiency) * self.water
    
    
