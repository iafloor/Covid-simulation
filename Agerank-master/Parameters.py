# Main input parameters of the simulation, you may want to vary these.
N = 1000000  # number of persons in the network,
time = 100 # timesteps in the simulation, this number is only used for preprocessing
# a trade-off between accuracy and speed

# measures
twoG = True # the 2G measure decreasing the number of contacts nonvaccinated people have
booster = False  # True if we are boostering people
vaccChildren = False # True if we vaccinate children

# For the following parameters choose sensible values, as realistic as possible.
ENCOUNTERS = 10
P_ENCOUNTER = 0.0005

# willingness for a vaccine based on data found on https://www.rivm.nl/gedragsonderzoek/maatregelen-welbevinden/vaccinatie
# we save this in a dictionary with as key the starting age of the group with the willingness of the value in percentage
vaccReadiness = {16: 91.6, 25: 90.6, 40: 92.9, 55: 96.9, 70: 98.7}
chanceToRefuse = 0.8 # I don't think we do anything with this
growFactor = 1.06
begin = 0.13
protectionInfection = 28 # based on not much
boostersGiven = 0.0029 # based on the 0.29% people getting a booster shot each day
#
STARTGROUP = [0, 4, 12, 18, 25, 35, 45, 55, 65, 75]
# Willingness to take the vaccine if offered
Vacc_readiness = 0.85
# Probability parameters (0 <= P <= 1 must hold)
P0 = 0.003  # probability of infection at time 0
P_MEETING = 0.02
# probability of meeting a contact on a given day
# and becoming infected.
# A base value in a non lockdown situation would be 0.02,
# assuming that 10% of daily meetings results in an infection
# and that the same person is met on average 6 times per month.
# For the lockdown situation, this number has been reduced.
# Here, an 80%-effective lockdown multiplies
# P_MEETING by a further factor 0.2.
P_QUARANTINE = 0.9  # probability of a person with symptoms going into
# quarantine where the alternative is being symptomatic
# and still infecting others. This takes into account
# that some persons will quarantine only partially.
P_TRANSMIT0 = 0.2  # probability of becoming a transmitter of the disease
# (with an asymptomatic infection) after having been vaccinated,
# when meeting an infected person, see the CDC brief
# https://www.cdc.gov/coronavirus/2019-ncov/science/science-briefs/fully-vaccinated-people.html

P_COHAB = 0.2  # todo add source and commentaar

P_TRANSMIT1 = 0.25  # probability of getting infected by a transmitter
# when meeting him/her, see Levine-Tiefenbrun  et al.,
# Decreased SARS-CoV-2 viral load following vaccination.
# https://www.medrxiv.org/content/10.1101/2021.02.06.21251283v1.full.pdf

# Time parameters based on characteristics of the disease.
# This is a simplification, since the actual development of the disease
# shows a spread around these values.
# It must hold that: DAY_SYMPTOMS < DAY_RECOVERY < DAY_RELEASE
NDAYS_VACC = 28  # number of days to wait after recovery before vaccinating
NDAYS_TRANSMIT = 5  # number of days a vaccinated person can transmit the disease
# assumed only short period, being an asymptomatic infection
DAY_SYMPTOMS = 2  # first day of showing symptoms, and decision day
# of going into quarantine
DAY_RECOVERY = 13  # day of possible recovery, or hospitalisation
DAY_RELEASE = 20  # day of release from hospital, or death

# Vaccination parameters
VACC0 = 0.155   # fraction of vaccination at time 0
                # based on 2.2 million first doses in NL for an adult
                # population of 14.1 million.
BETA0 = 0.0     # fraction of young among the vaccinated persons at time 0
                # These might be young care workers and hospital staff
                # For now, neglected. The others are assumed to be the oldest.
VACC = 0.005    # fraction of the population vaccinated per day.
                # The vaccination is assumed to have immediate effect, modelling
                # receiving the shot two weeks earlier.
                # Only susceptible persons are vaccinated.
                # The order is by increasing index (young to old)
                # for the fraction BETA, and old to young for the fraction 1-BETA.
                # The value is based on 100000 first doses per day.
STARTAGE = 12   # starting age of the vaccination, country dependent (NL 18, IL 16)
                # Other parameters.
PERIOD = 6      # number of days for which the contacts are the same group.
                # It must be between 1 (all monthly contacts are with different
                # persons, # and 30 (all monthly contacts are with the same person).
                # A period of 6 seems a good compromise.
RATIO_HF = 3    # ratio between number of admissions to the hospital
                # and the number of fatalities (ratio must be >=1)
                # this does not influence the simulation, as the age-dependence
                # of hospitalisation has been modelled through the fatality rate.


# parameters for creating groups
KIDSINGROUP = 23 # based on the average number of kids in a class in primary school in 2018 in the Netherlands
                 # for high school the numbers differ per educational attainment. The averages are at lest 13 and at most 26. I have choosen to 
                 # still use the average of 23 for these groups.
                 # https://www.rijksoverheid.nl/onderwerpen/basisonderwijs/vraag-en-antwoord/hoe-zijn-de-groepen-in-het-basisonderwijs-bo-samengesteld
STUDENTHOUSE = 2.18     # percentage of population living in a student house based on the population in the netherlands, 17.44 milion and
                        # https://www.kences.nl/wp-content/uploads/2020/11/20201105-Kences-Landelijke-monitor-studentenhuisvesting-2020.pdf
                        # page 33 "uitwonend" 370.300
STUDENTSGV = 7          # students live in a house with an averag of 7 per house. This differs from 1 to 13.
RETIREMENT = 0.67       # number of people living in a retirement home
PEOPLEINRETIREMENT = 48 # based on the 115,000 people living in retirement houses and the 2373 retirement houses
                        # in the Netherlands
LIVINGALONE = 17.7      # percentage based on cbs
"""
def parameter():
    return {"N": N,
            "ENCOUNTERS": ENCOUNTERS,
            "P_ENCOUNTER": P_ENCOUNTER,
            "STARTGROUP": STARTGROUP,
            "Vacc_readiness": Vacc_readiness,
            "P0": P0,
            "P_MEETING": P_MEETING,
            "P_QUARANTINE": P_QUARANTINE,
            "P_TRANSMIT0": P_TRANSMIT0,
            "P_COHAB": P_COHAB,
            "P_TRANSMIT1": P_TRANSMIT1,
            "NDAYS_VACC": NDAYS_VACC,
            "NDAYS_TRANSMIT": NDAYS_TRANSMIT,
            "DAY_SYMPTOMS": DAY_SYMPTOMS,
            "DAY_RECOVERY": DAY_RECOVERY,
            "DAY_RELEASE": DAY_RELEASE,
            "VACC0": VACC0,
            "BETA0": BETA0,
            "VACC": VACC,
            "STARTAGE": STARTAGE,
            "PERIOD": PERIOD,
            "RATIO_HF": RATIO_HF,
            "SUSCEPTIBLE": 0,
            "INFECTIOUS": 1,  # but no symptoms yet
            "SYMPTOMATIC": 2,  # but not quarantined
            "QUARANTINED": 3,
            "HOSPITALISED": 4,
            "RECOVERED": 5,
            "VACCINATED": 6,
            "TRANSMITTER": 7,  # infectious after being vaccinated or having recovered
            "DECEASED": 8
            }"""
