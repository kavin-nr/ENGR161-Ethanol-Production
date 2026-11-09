# ENGR161-Ethanol-Production
A Python-based simulation of an ethanol production facility developed for Purdue University's ENGR 16100 – Project 2.

This project models the production of ethanol from an initial sugar-containing slurry through a series of industrial unit operations. It calculates material flows, energy consumption, hydraulic losses, equipment costs, and overall facility performance.

The goal is to evaluate different facility configurations and identify designs that meet production and purity requirements while balancing capital costs and energy efficiency.


### Running the Simulation

Run the simulation using the default equipment configuration:

```bash
python Proj2_FermModel_Team50.py
```

Specify equipment tiers from the command line:

```bash
python Proj2_FermModel_Team50.py scrap average premium world-class
```

The four arguments correspond to the fermenter, filter, distiller, and dehydrator, respectively.

Available unit tiers are:

- `scrap`
- `average`
- `premium`
- `world-class`

To display detailed results, append the `-v` flag:

```bash
python Proj2_FermModel_Team50.py -v
```

```bash
python Proj2_FermModel_Team50.py premium premium premium premium -v
