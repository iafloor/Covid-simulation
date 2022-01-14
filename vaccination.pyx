from Read_data import *
from Classes import *
from Parameters import *
from customTypes cimport person, changes
import random


def boosters(peoplep, startagep,  weekp):
    """In this function we give a number of people a boostervaccine. The vaccines
    are distrubted from oldest to youngest and you can only get a boostervaccine
    if you have already been vaccinated before. We update the week of vaccination
    to the current week and use a parameter startage which keeps track of where
    we left vaccinating the previous day."""
    cdef int numberOfBoosters = boostersGiven*N
    cdef list people = peoplep
    cdef int startage = startagep, week = weekp
    for i in range(numberOfBoosters):
        # if the person has not been vaccinated, we skip them
        while people[startage]["weekOfVaccination"] < 0 or \
        people[startage]["susceptible"] == 0 or \
        week + 46 - people[startage]["weekOfVaccination"] < 12:
            startage -= 1
            if startage < 1 :
               return people, N-1
        people[startage]["weekOfVaccination"] = week
        startage -= 1
    return people, startage


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

def vaccinate(people, time ):
    """This function vaccinates a certain amount of people. The number of people that get 
    vaccinated will decrease over time since the number of people getting a booster will increase
    over time """
    cdef int total = vaccinationsGiven * N, index, week = time // 7
    for i in range(total):
        index = N-1
        while people[index]["vaccinated"] == 1 or people[index]["age"] < 12 or people[index]["susceptible"] == 1 or people[index]["dontVaccme"]:
            index -= 1
            if index < 1 :
                return people
        people[index]["weekOfVaccination"] = week
        people[index]["vaccinated"] = 1
        index -= 1
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

