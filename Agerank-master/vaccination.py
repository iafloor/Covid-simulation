from Read_data import *
from Classes import *
from Parameters import *
# functions to vaccinate people

def boosters(population, number, startage, week):
    """In this function we give a number of people a boostervaccine. The vaccines
    are distrubted from oldest to youngest and you can only get a boostervaccine
    if you have already been vaccinated before. We update the week of vaccination
    to the current week and use a parameter startage which keeps track of where
    we left vaccinating the previous day."""

    for i in range(number):
        # if the person has not been vaccinated, we skip them
        while population.people[startage].weekOfVaccination < 0 :
            startage -= 1
        population.people[startage].weekOfVaccination = week


def vaccinateKids(population, number, week):
    """In this function we vaccinate children under 12. We chose a
    random index and check if this kid has already been vaccinated,
    if so we chose another one."""

    for i in range(number):
        index = 1
        while(population.people[index].vaccinated != 0):
            index = 1
        population.people[index].vaccinated = 1
        population.people[index].weekOfVaccination = week


def vaccinate(population, status_changes):
    """This function performs one time step (day) of the vaccinations.
    status represents the health status of the persons.
    Only the susceptible or recovered (after a number of days) are vaccinated
    """

    new_status_changes = status_changes
    n = len(population.people)

    # today's number of vaccines
    vacc = math.floor((1 - BETA) * VACC * n)  # and for the old
    for i in range(min(vacc, len(population.vaccOrder))):
        person = population.vaccOrder.pop(0)
        if person.status == SUSCEPTIBLE:
            if person.vaccination_readiness == True:
                person.update_status(VACCINATED)
                new_status_changes["susceptible"] += -1
                new_status_changes["vaccinated"] += 1

        if person.status == RECOVERED and person.daysSinceInfection >= DAY_RECOVERY + NDAYS_VACC:
            person.update_status(VACCINATED)
            new_status_changes["vaccinated"] += 1

    return new_status_changes, population