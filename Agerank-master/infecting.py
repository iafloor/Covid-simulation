from Read_data import *
from Classes import *
from Parameters import *
# infecting people

def infectChance(time, population, person) :
    """ This function calculates the chance that someone will get infect based
    on the infections in their innercircle. This chance is base on:
    - how many people in their household are infected
    - how many people in their classroom are infected
    and an overall difference if someone has been vaccinated or not
    and how long ago"""
    chance = 0

    # if cohab or classmate is sick, chance increases
    chance += cohabIsSick(population, person)
    chance += classmateIsSick(population, person)

    # if persen is vaccinated chance lowers but protection decreases over time
    if chance > 0:
        if person.vaccinated :
            chance *= prevVaccinated(time, person)
        else :
            chance = 10

    return chance


def cohabIsSick(population, person):
    # checks if there is someone sick in your household
    household = person.household
    if (population.houseDict[household].infected > 0) :
        chance = 20
    else :
        chance = 0
    return chance


def classmateIsSick(population, person):
    # checks if there is someone sick in your class
    id = person.schoolClass
    chance = 0
    if(id > -1) :   # a person has id -1 if they're not in a class
        if(population.schoolGroup[id].infected > 0):
            chance = 20
    return chance


def prevVaccinated(time, person):
    # this function calculates how long ago someone has been vaccinated
    # according to research the protection of a vaccine decreases over time
    vaccInWeek = person.weekOfVaccination
    timeSinceVacc = int(time/7) - vaccInWeek
    return 20 + 5*timeSinceVacc


def infect_standard(network, population):
    """This function performs one time step (day) of the infections
    a is the n by n adjacency matrix of the network
    status represents the health status of the persons.
    In this step, infectious persons infect their susceptible contacts
    with a certain probability.
    """

    people = population.people
    n = len(people)
    x = np.zeros((n + 1), dtype=int)
    y = np.zeros((n + 1), dtype=int)

    # determine list of infectious persons from status
    for person in people:
        if person.infectious == 1:
            x[person.person_id] = 1

    # propagate the infections
    for edge in network:
        i, j = edge
        y[i] += x[j]

    for person in people:
        # incorporate the daily probability of meeting a contact
        # taking into account the possibility of being infected twice

        if y[person.person_id] > 0:
            r = rd.random()
            if y[person.person_id] == 1:
                p = P_MEETING # probability of a meeting with 1 infected contact
            else:
                p = 1 - (1 - P_MEETING) ** y[person.person_id]  # probability with more than 1
            if r < p:
                if person.susceptible == 1:
                    person.daysSinceInfection = 1
        id = person.person_id
        population.people[id] = person

    return population