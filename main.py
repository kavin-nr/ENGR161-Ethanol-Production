from units import Fermenter, Filter, Distiller, Dehydrator
from utils import *

# CONSTANTS

ETHANOL_ENERGY_DENSITY = 21160.18 # MJ/m3
SUGAR_TO_CO2_RATIO = 0.49

SLURRY_PERCENT_WEIGHT_SUGAR = 0.20
SLURRY_PERCENT_WEIGHT_ETHANOL = 0
SLURRY_PERCENT_WEIGHT_FIBROUS = 0.20
SLURRY_PERCENT_WEIGHT_WATER = 0.60


# DESIGN VARIABLES (assumed)

DAILY_FLOW_RATE = 3161.58 # m3/day
FLOW_RATE = 3161.58 / SECONDS_PER_DAY # m3/s
NUM_VALVES = 8
NUM_BENDS = 4 # 90 degrees

PUMP_EFFICIENCY = 0.8

FERMENTER_EFFICIENCY = 0.5
FILTER_EFFICIENCY = 0.5
DISTILLER_EFFICIENCY = 0.81
DEHYDRATOR_EFFICIENCY = 0.5

FERMENTER_COST = 320000 # $ per m3/sec
FILTER_COST = 200000 # $ per m3/sec
DISTILLER_COST = 390000 # $ per m3/sec
DEHYDRATOR_COST = 200000 # $ per m3/sec

FERMENTER_ENERGY = 46600 # kWh/day
DISTILLER_ENERGY = 47004 # kWh/day
FILTER_ENERGY = 48800 # kWh/day
DEHYDRATOR_ENERGY = 48800 # kWh/day

'''
Placeholder
'''
SITE_COST = 1600000 # USD, this is Site 3. 
OTHER_COSTS = 0



def main():
    units = [
        (Fermenter, FERMENTER_EFFICIENCY, FERMENTER_ENERGY, FERMENTER_COST),
        (Filter, FILTER_EFFICIENCY, FILTER_ENERGY, FILTER_COST),
        (Distiller, DISTILLER_EFFICIENCY, DISTILLER_ENERGY, DISTILLER_COST),
        (Dehydrator, DEHYDRATOR_EFFICIENCY, DEHYDRATOR_ENERGY, DEHYDRATOR_COST)
    ]

    
    components = {

        DENSITY_SUGAR: SLURRY_PERCENT_WEIGHT_SUGAR, 
        DENSITY_ETHANOL: SLURRY_PERCENT_WEIGHT_ETHANOL,
        DENSITY_FIBROUS: SLURRY_PERCENT_WEIGHT_FIBROUS,
        DENSITY_WATER: SLURRY_PERCENT_WEIGHT_WATER
        
    }

    fluidDensity = calcDensityMixture(components)

    # Just run it for 1 day 
    fluidMass = calcFluidMass(fluidDensity, DAILY_FLOW_RATE, 1)

    initialMasses = [
        fluidMass * SLURRY_PERCENT_WEIGHT_SUGAR,
        fluidMass * SLURRY_PERCENT_WEIGHT_ETHANOL,
        fluidMass * SLURRY_PERCENT_WEIGHT_FIBROUS,
        fluidMass * SLURRY_PERCENT_WEIGHT_WATER
    ]

    units = runProductionLine(initialMasses, units)

    
    
    # FINAL SYSTEM OUTPUTS

    finalUnit = units[-1]

    # Final product
    finalMass = finalUnit.getTotalMassOutput()
    finalPurity = finalUnit.getOutputPurity()
    ethanolMass = finalUnit.getEthanol()

    # Calculate final product volume
    finalDensity = calcDensityMixture({
        DENSITY_SUGAR: finalUnit.getSugar() / finalMass,
        DENSITY_ETHANOL: finalUnit.getEthanol() / finalMass,
        DENSITY_FIBROUS: finalUnit.getFibrous() / finalMass,
        DENSITY_WATER: finalUnit.getWater() / finalMass
    })

    finalVolume = finalMass / finalDensity
    finalGallons = finalVolume * 264.172

    # Capital costs (unit operations only)
    unitCapitalCost = sum(unit.getCapitalCost() for unit in units)

    # Total costs
    totalCost = unitCapitalCost + SITE_COST

    # Electrical energy used by unit operations
    totalEnergy = sum(unit.getEnergy() for unit in units)

    # Ethanol energy output (MJ/day)
    ethanolVolume = ethanolMass / DENSITY_ETHANOL
    energyOutput = ethanolVolume * ETHANOL_ENERGY_DENSITY

    # Energy ROI (excluding pump energy for now)
    energyROI = energyOutput / (totalEnergy * 3.6)

    # Final summary
    print("=" * 50)
    print("ETHANOL PRODUCTION FACILITY - SYSTEM SUMMARY")
    print("=" * 50)
    print()

    print("PRODUCTION")
    print(f"Initial Slurry: {DAILY_FLOW_RATE:,.2f} m3/day")
    print(f"Final Product: {finalGallons:,.2f} gal/day")
    print(f"Ethanol Produced: {ethanolMass:,.2f} kg/day")
    print(f"Ethanol Purity: {finalPurity:.2%}")
    print()

    print("ENERGY")
    print(f"Electrical Input: {totalEnergy:,.2f} kWh/day")
    print(f"Ethanol Energy: {energyOutput:,.2f} MJ/day")
    print(f"Energy ROI: {energyROI:.2f}")
    print()

    print("CAPITAL COSTS")
    print(f"Unit Operations: ${unitCapitalCost:,.2f}")
    print()

    print("TOTAL COST")
    print(f"${totalCost:,.2f}")
    print()

    print("REQUIREMENTS")
    print(f"Production Target: 100000 gal/day")
    print(f"Purity Target: 98%")
    print(f"Production Met: {finalGallons >= 100000}")
    print(f"Purity Met: {finalPurity >= 0.98}")
    print()








if __name__ == "__main__":
    main()
    