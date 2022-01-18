import random as rd
from initialize import *
from preprocessing import preprocessing, VaccinationEffectiveness, pmeetinglist
from vaccination import *
from customTypes cimport person, changes
import numpy as np

    

cdef class simulation:
    def __cinit__(self, vaccEffectiveness, meeting, network, housedict, othergroups, people):
        self.vaccEffectiveness = vaccEffectiveness
        self.meeting = meeting
        self.network = network
        self.housedict = housedict
        self.othergroups = othergroups
        self.people = people
        self.startage = N - 1
        self.sumt = 0
    cdef list vaccEffectiveness, meeting, network, othergroups
    cdef public list people, housedict
    cdef person person
    cdef int id, total, startage
    cdef float p, r, chance
    cdef int x[1000000], y[1000000]
    cdef int sumt

    cdef infect_standard(self, int time):
        """This function performs one time step (day) of the infections
        a is the n by n adjacency matrix of the network
        status represents the health status of the persons.
        In this step, infectious persons infect their susceptible contacts
        with a certain probability.
        """
        cdef int total = 0, id
        cdef person person
        # determine list of infectious persons from status
        for per in self.people:
            person = per
            id = person.person_id
            if person.infectious == 1:
                self.x[id] = 1
            else :
                self.x[id] = 0
            if twoG and person.vaccinated == 0:
                self.x[id] = 0
            self.y[id] = 0
            
        # propagate the infections
        for edge in self.network:
            (i, j) = edge
            self.y[i] += self.x[j]

        for per in self.people:
            person = per
            # incorporate the daily probability of meeting a contact
            # taking into account the possibility of being infected twice
            
            if twoG :
                if person.vaccinated == 0:
                    continue
            #print(self.y[self.person.person_id])
            if self.y[person.person_id] > 0:
               if person.susceptible == 1 and \
                  rd.uniform(0,1) < 1 - (1 - P_MEETING) ** self.y[person.person_id] and \
                  rd.uniform(0,1) < self.prevVaccinated(time, person) :
                      person.daysSinceInfection = 1
                      self.people[person.person_id] = person
                      
    cdef int infectChance(self, int time, person person) :
        """ This function calculates the chance that someone will get infect based
            on the infections in their innercircle. This chance is base on:
        - how many people in their household are infected
        - how many people in their classroom are infected
        and an overall difference if someone has been vaccinated or not
        and how long ago"""
        cdef int chance = 0

        # if cohab or classmate is sick, chance increases
        chance += self.cohabIsSick(person)
        chance += self.classmateIsSick(person)
        return min(chance, 100)
        


    cdef int cohabIsSick(self, person person):
        # checks if there is someone sick in your household
        if self.housedict[person.household].infected > 0 :
            return 2
        return 0


    cdef int classmateIsSick(self, person person):
        # this function checks if there is someone sick in 
        # the same household as the person in question
            try:
                return othergroups[person.schoolClass].infected * 1
            except :
                return 0

    cdef float prevVaccinated(self, int time, person person):
        # this function calculates how long ago someone has been vaccinated
        # according to research the protection of a vaccine decreases over time
        if person.vaccinated == 1 :
            return self.vaccEffectiveness[time//7 + 47 - person.weekOfVaccination]
        else :
            return 1

    cdef infectRandom(self) :
        """This function randomly infects 10 people with ages between 12 and 60
        these infections represent the infections that would result from getting infected from
        someone a person does not personally know. """
        for i in range(infectPeopleRandom) :
            index = random.randint(0,N-1)
            if (self.people[index]["age"] < 12 or self.people[index]["age"] > 60) and \
                self.people[index]["susceptible"] == 1:
                index = random.randint(0, N-1)
            self.people[index]["daysSinceInfection"] = 1
            
    cdef vaccinate(self, int time ):
        """This function vaccinates a certain amount of people. The number of people that get 
        vaccinated will decrease over time since the number of people getting a booster will increase
        over time """
        cdef int totalWeek = vaccinationsGiven * N, index, week = time // 7
        for i in range(totalWeek):
            index = random.randint(0,N-1)
            while self.people[index]["vaccinated"] == 1 or \
                  self.people[index]["age"] < 12 or \
                  self.people[index]["susceptible"] == 0 or \
                  self.people[index]["dontVaccme"] == 1:
                index = random.randint(0,N-1)
            self.people[index]["weekOfVaccination"] = week
            self.people[index]["vaccinated"] = 1
            index -= 1
        return 
        
    cdef boosters(self,weekp):
        """In this function we give a number of people a boostervaccine. The vaccines
        are distrubted from oldest to youngest and you can only get a boostervaccine
        if you have already been vaccinated before. We update the week of vaccination
        to the current week and use a parameter startage which keeps track of where
        we left vaccinating the previous day."""
        cdef int numberOfBoosters = boostersGiven*N, week = weekp  + 47
        cdef person person
        for i in range(numberOfBoosters):
            # if the person has not been vaccinated, we skip them
            person = self.people[self.startage]
            while person.vaccinated == 0 or \
                  person.susceptible == 0 or \
                  week - person.weekOfVaccination < 24:    
                self.startage -= 1
                if self.startage < 1 :
                   self.startage = N -1
                   return 
                person = self.people[self.startage]
            person.weekOfVaccination = week
            self.people[self.startage] = person
            self.startage -= 1
        return

    cdef changes update(self, fatality, changes newchanges):
        """This function updates the status and increments the number
        of days that a person has been infected.
        For a new infection, days[i]=1.  For uninfected persons, days[i]=0.
        Input: infection fatality rate and age of persons i
        """
        # typing the variables
        cdef person person
        cdef int newinfections = 0, recovered = 0, id, houseID, schooolID
    
        for p in self.people:
            person = p
            id = person.person_id
            if person.daysSinceInfection > 0 :
                person.daysSinceInfection += 1
                if person.daysSinceInfection == 2 :    
                    newchanges.newInfections += 1
                    newchanges.vaccinated += person.vaccinated
                    newchanges.nonvaccinated += 1 - person.vaccinated 
                    newchanges.totalInfected += 1
                    person.susceptible = 0
                    person.infectionProtected = 1

            # on the day symptoms should be noticable we check if someone goes into quarantine
            # if someone does not go in quarantine because they don't want to, they don't know
            # that they have COVID or for other reasons, they stay in their household.
            # for this it doesn't matter if they have or do not have symptoms
                if person.daysSinceInfection == DAY_SYMPTOMS :
                    if rd.random() < P_QUARANTINE:
	                    # i gets symptoms and quarantines
                            person.quarantined = 1
                    else:
	                    # i gets symptoms but does not quarantine
                            houseID = person.household
                            self.housedict[houseID].infected += 1
                            person.infectious = 1
                            schoolID = person.schoolClass
                            if schoolID > -1 :
                                self.othergroups[schoolID].infected += 1
      
                    # on the recovery day of a person we check if they recover or if they get admitted to the hospital
                    # when they are hospitalised we change their status based on if they had been quarantined.
                elif person.daysSinceInfection == DAY_RECOVERY :
                        if rd.random() < RATIO_HF * fatality[person.age]:
                            if person.vaccinated == 1 and rd.random() < 0.95 :
                                continue
                            person.hospitalised = 1
                            if person.quarantined == 0:
                                person.infectious -= 1
                                houseId = person.household
                                self.housedict[houseId].infected -= 1
                                schoolId = person.schoolClass
                                if schoolId > -1 :
                                    self.othergroups[schoolId].infected -= 1
                            else :
                                person.quarantined = 0
                            person.hospitalised = 1
                            newchanges.hospitalized += 1
                        else:
                            if person.quarantined == 0 :
                                houseID = person.household
                                self.housedict[houseID].infected -= 1
                                schoolId = person.schoolClass
                                if schoolId > -1:
                                    self.othergroups[schoolId].infected -= 1
                            person.infectious = 0    
                            person.quarantined = 0    
                            person.daysSinceInfection = 0
                            person.recovered = 1
                            person.daysSinceRecovery = 1
        
                    # on the day of release of someone who has been hospitalised, they have a chance of dying
                elif person.daysSinceInfection == DAY_RELEASE:
                    #nchanges["hospitalized"] -= 1
                    person.hospitalised = 0    
                    if rd.random() < 1 / RATIO_HF:
                        person.infectious = 0
                        person.quarantined = 0
                        person.daysSinceInfection = 0
                        person.deceased = 1
                        #self.newchanges.hospitalized -= 1
                        newchanges.deceased += 1
                    else:
                        person.infectious = 0
                        person.quarantined = 0
                        person.daysSinceInfection = 0
                        person.recovered = 1
                        person.daysSinceRecovery = 1
                        #self.newchanges.hospitalized -= 1
         
            if person.daysSinceRecovery > 0 :
                if person.daysSinceRecovery == 14 :
                    person.susceptible = 1
                elif person.daysSinceRecovery == protectionInfection :
                    person.infectionProtected = 0 
                    person.daysSinceRecovery = 0
                person.daysSinceRecovery += 1
            self.people[id] = person
        return newchanges 
    def run_model(self,data, tracker, timesteps):
        """ This function simulates infections for a given number of days given by the input timesteps. 
        The input for this function is the population containing information about all the people and
        their households, the contact matrix containing occasional meetings between people. A tracker
        that keeps track of the statistical changes and the number of timesteps."""
        
        # identify types of variables
        cdef person person
        cdef changes newchanges
        cdef int id, startage = N - 1, c, would = 1, result = 0
        cdef float number, total = 0

        # initializing values for the tracker
        newchanges.totalInfected = 0
        newchanges.deceased = 0
        
        
        # initialize infections
        self.infectRandom()
        newchanges = self.update(data['IFR'], newchanges)
    
    
        # loop through time
        for time in range(timesteps):
            self.sumt = 0
            infpr = 0
            # printing the day we are currently simulating
            sys.stdout.write('\r' + "Time step: " + str(time)) 
            sys.stdout.flush()
            # loop through all the people in the population, 
            # if they are not sick we calculate their change
            # of getting infected. If they get infected it is their first day since infection.
            for p in self.people:
                person = p
                if person.infectionProtected == 1 :
                    infpr += 1
                if person.susceptible == 1 and person.infectionProtected == 0:
                    if rd.randint(0,100) < self.infectChance(time, person) :
                        would += 1
                        total += self.prevVaccinated(time, person)
                        if rd.uniform(0,1) < self.prevVaccinated(time, person) :
                            result += 1
                            person.daysSinceInfection = 1
                            self.people[person.person_id] = person           
            # we infect a number of people based on occasional meetings
            self.infect_standard(time)
            
            # we infect a number of people randomly. If there is a lockdown, we skip this
            if not lockdown :
                self.infectRandom()
                
            newchanges.newInfections = 0
            newchanges.vaccinated = 0
            newchanges.nonvaccinated = 0
            newchanges.hospitalized = 0
            
            # update the people in the population
            newchanges = self.update(data['IFR'], newchanges)
        
            # vaccinate a number of people who have not had a vaccine yet in the first 25
            # afterwards we have the same number of fully vaccinated people as in the Netherlands
            # as of January 2022
            if time < 25 :
                self.vaccinate(time)
            # booster people if boolean is true
            if booster :
                self.boosters(time//7)
        
            # update the tracker
            status_changes = tracker.empty_changes()
            status_changes["new infected"] = newchanges.newInfections
            status_changes["total infected"] = newchanges.totalInfected
            status_changes["hospitalized"] = newchanges.hospitalized
            status_changes["deceased"] = newchanges.deceased
            status_changes["vaccinated"] = newchanges.vaccinated
            status_changes["nonvaccinated"] = newchanges.nonvaccinated
            # update the tracker
            tracker.update_statistics(status_changes)
        print(would, result)
        print(newchanges.totalInfected)
        return tracker


def model(filenames, type, timesteps):
    # this initializes and runs the entire model for a certain number of timesteps.
    # It returns a pandas dataframe containing all data at time t
    tracker = track_statistics()

    tracker_changes = tracker.init_empty_changes()
    data, network, tracker_changes, currentPopulation = initialise_model(filenames, type, tracker_changes)
    # update the dataframe
    tracker.update_statistics(tracker_changes)
    # preprocessing
    #newPopulation, tracker, vaccEffectiveness, meeting = preprocessing(currentPopulation, filenames, data, tracker)
    
    # creating lists
    vaccEffectiveness = VaccinationEffectiveness()
    meeting = pmeetinglist()

    # Run the model
    cdef simulation sim= simulation(vaccEffectiveness, meeting, network, currentPopulation.houseDict, currentPopulation.otherGroups, currentPopulation.people) 
    sim = preprocessing(filenames, data, sim)  
    tracker = sim.run_model(data, tracker, timesteps)

    return tracker

