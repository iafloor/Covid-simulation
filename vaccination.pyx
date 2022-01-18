from Read_data import *
from Classes import *
from Parameters import *
from customTypes cimport person, changes
import random


cdef list vaccinateKids(list people, int number, int week):
    """In this function we vaccinate children under 12. We chose a
    random index and check if this kid has already been vaccinated,
    if so we chose another one."""
    cdef int index
    for i in range(number):
        index = 1
        while(population.people[index].vaccinated != 0):
            index = 1
        population.people[index].vaccinated = 1
        population.people[index].weekOfVaccination = week
    return people


def vaccinateNOTMINE(population, status_changes):
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

