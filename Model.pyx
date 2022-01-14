import random as rd
from initialize import *
from preprocessing import *
from vaccination import *
from customTypes cimport person, changes
import numpy as np

cdef infectChance(int time, list houseDict, list otherGroups, person person) :
    """ This function calculates the chance that someone will get infect based
    on the infections in their innercircle. This chance is base on:
    - how many people in their household are infected
    - how many people in their classroom are infected
    and an overall difference if someone has been vaccinated or not
    and how long ago"""
    cdef float chance = 0

    # if cohab or classmate is sick, chance increases
    chance += cohabIsSick(houseDict, person)
    chance += classmateIsSick(otherGroups, person)
    return chance


cdef int cohabIsSick(list populationhouseDict, person person):
    # checks if there is someone sick in your household
    cdef int chance = 0
    cdef int household
    household = person.household
    if (populationhouseDict[household].infected > 0) :
        chance = 20
    return chance


cdef int classmateIsSick(list populationschoolGroup, person person):
    # checks if there is someone sick in your class
    cdef int chance = 0
    cdef int id 
    id = person.schoolClass
    if(id > -1) :   # a person has id -1 if they're not in a class
        if(populationschoolGroup[id].infected > 0):
            chance = 20
    return chance

cdef float prevVaccinated(int time, person person, list vaccEffectiveness):
    # this function calculates how long ago someone has been vaccinated
    # according to research the protection of a vaccine decreases over time
    if person.vaccinated == 1 :
        return vaccEffectiveness[time//7 + 46 - person.weekOfVaccination]
    else :
        return 1

def infect_standard(network, listOfPeople, time, vaccEffectiveness):
    """This function performs one time step (day) of the infections
    a is the n by n adjacency matrix of the network
    status represents the health status of the persons.
    In this step, infectious persons infect their susceptible contacts
    with a certain probability.
    """
    cdef list people  = listOfPeople
    cdef person person
    cdef int r, id, n = len(people), total = 0
    cdef float p
    cdef list x = [], y = []

    # determine list of infectious persons from status
    for per in people:
        person = per
        if person.infectious == 1:
            x.append( 1)
        else :
            x.append(0)
        y.append(0)
            
    # propagate the infections
    for edge in network:
        i, j = edge
        y[i] += x[j]

    for per in people:
        person = per
        # incorporate the daily probability of meeting a contact
        # taking into account the possibility of being infected twice
        
        if twoG :
            if person.vaccinated == 0:
                continue
        if y[person.person_id] > 0:
            r = rd.random()
            if y[person.person_id] == 1:
                p = P_MEETING # probability of a meeting with 1 infected contact
            else:
                p = 1 - (1 - P_MEETING) ** y[person.person_id]  # probability with more than 1
            if r < p:
                if person.susceptible == 1:
                    r = rd.uniform(0,1)
                    if r < prevVaccinated(time, per, vaccEffectiveness ):
                        person.daysSinceInfection = 1
                        total += 1
        id = person.person_id
        people[id] = person
    return people

def infectRandom(people) :
    """This function randomly infects 10 people with ages between 12 and 60
    these infections represent the infections that would result from getting infected from
    someone a person does not personally know. """
    for i in range(infectPeopleRandom) :
        index = random.randint(0,N-1)
        if (people[index]["age"] < 12 or people[index]["age"] > 60) and people[index]["susceptible"] == 1:
            index = random.randint(0, N-1)
        people[index]["daysSinceInfection"] = 1
    return people

def run_model(peopleList, houseDictList, otherGroupsList, data, contact_matrix, tracker, timesteps, start_vaccination, vaccEffectiveness):
    """ This function simulates infections for a given number of days given by the input timesteps. 
    The input for this function is the population containing information about all the people and
    their households, the contact matrix containing occasional meetings between people. A tracker
    that keeps track of the statistical changes and the number of timesteps."""
    
    # identify types of variables
    cdef person person
    cdef changes newchanges
    cdef int id, startage = N - 1, c, would = 0, result = 0
    cdef float number
    cdef list houseDict = houseDictList, otherGroups = otherGroupsList, people = peopleList
    
    # initializing values for the tracker
    newchanges.newInfections = 0
    newchanges.totalInfected = 0
    newchanges.hospitalized = 0
    newchanges.deceased = 0
    
    # loop through time
    for time in range(timesteps):
        # printing the day we are currently simulating
        sys.stdout.write('\r' + "Time step: " + str(time)) 
        sys.stdout.flush()
        status_changes = tracker.empty_changes()
        # loop through all the people in the population, 
        # if they are not sick we calculate their change
        # of getting infected. If they get infected it is their first day since infection.
        for p in people:
            person = p
            if person.susceptible == 1 and person.infectionProtected == 0:
                number = rd.randint(0,10000)
                c = infectChance(time, houseDict, otherGroups, person)
                if number < c*100 :
                    would += 1
                    number = rd.uniform(0,1)
                    newchance = prevVaccinated(time, person, vaccEffectiveness)
                    if number < newchance :
                        result += 1
                        id = person.person_id
                        person.daysSinceInfection = 1
                        people[id] = person
                    

        # we infect a number of people based on occasional meetings
        people = infect_standard(contact_matrix, people, time, vaccEffectiveness)
        
        # we infect a number of people randomly. If there is a lockdown, we skip this
        if not lockdown :
            people = infectRandom(people)

        # update the people in the population
        people, houseDict, otherGroups, newchanges = update(data['IFR'], people, houseDict, otherGroups, newchanges)
        
        # vaccinate a number of people who have not had a vaccine yet
        people = vaccinate(people,time)
        # booster people if boolean is true
        if(booster):
            people, startage = boosters(people, startage, time//7)
        
        # update the tracker
        status_changes["new infected"] = newchanges.newInfections
        status_changes["total infected"] = newchanges.totalInfected
        status_changes["hospitalized"] = newchanges.hospitalized
        status_changes["deceased"] = newchanges.deceased
        # update the tracker
        tracker.update_statistics(status_changes)
        
    print(would)
    print(result)
    return tracker


def model(filenames, type, timesteps):
    # this initializes and runs the entire model for a certain number of timesteps.
    # It returns a pandas dataframe containing all data at time t
    tracker = track_statistics()

    tracker_changes = tracker.init_empty_changes()
    data, contact_matrix, tracker_changes, currentPopulation = initialise_model(filenames, type, tracker_changes)
    # update the dataframe
    tracker.update_statistics(tracker_changes)
    # preprocessing
    newPopulation, tracker, vaccEffectiveness = preprocessing(currentPopulation, filenames, data, tracker)

    # Run the model
    tracker = run_model(newPopulation.people, newPopulation.houseDict, newPopulation.otherGroups, data, contact_matrix, tracker, timesteps - 1, 0, vaccEffectiveness)

    return tracker

