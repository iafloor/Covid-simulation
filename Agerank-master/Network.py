import random

import numpy as np
import pandas as pd
import math
import random as rd
import sys


from Read_data import *
from Classes import *
from Parameters import *


def how_many_children(available_children):
    #calculates how many children a family has. We check the maximum and choose a random number, if there are still households needed with that many kids we're done, else we choose another number
    maxNumberOfChildren = len(available_children)
    numberOfChildren = random.choice((range(0,maxNumberOfChildren)))
    while(available_children[numberOfChildren] < 1) :
        numberOfChildren = random.choice((range(0,maxNumberOfChildren)))
    return numberOfChildren


def couple_childless(population):
    # ages of all the people living with 1 other person which is not their child
    couples = list(population.amountPeople["Fraction couple without children"])
    number_of_couples = int(sum(couples) / 2)

    #  we use this parameter to keep track of the index of the first available age
    popage = 19
    # calculate all ages available for the couples
    availableAges = {}

    # calculate the start age
    startage = 0;
    while (couples[startage] < 1) :
        startage += 1

    for age in range(startage, len(couples)) :
        availableAges[age] = couples[age]


    #availableAges = {index for index in range(len(couples)) if couples[index] > 0}
    #print(sum(couples))

    # we give all the couples an age
    for couple in range(number_of_couples - 1):

        # pick the lowest available age for person 1
        age1 = list(availableAges.keys())[0]
        person1 = population.ageDist[age1].pop()
        availableAges[age1] -= 1

        # if that was the last person of that age, we deleted the available age
        if availableAges[age1] < 1:
            availableAges.pop(abs(age1))        # ages start at 19

        # pick age for person 2
        ageDifference = random.choice(range(5))
        ageDifference = min(ageDifference, len(availableAges)-1)
        age2 = list(availableAges.keys())[ageDifference]
        person2 = population.ageDist[age2].pop()
        availableAges[age2] -= 1

        # if that was the last person of that age, we deleted the available age
        if availableAges[age2] < 1:
            availableAges.pop(abs(age2))         # ages start at 19

        # household id
        id = population.createdHouses
        # we put them in a household
        house = household(id,2)
        house.add_member(person1)
        house.add_member(person2)
        person1.update_household(id)
        person2.update_household(id)

        # add house to list of houses
        population.houseDict.append(house)

        # increase household id
        population.createdHouses += 1

        # we also add them to their age group in the future 

    return population


def twoParentHH(population, twoParentDist):
    # for every couple we loop through the list
    # we loop through all the couples and calculate how many children they'll get
    while (int(sum(twoParentDist) > 0 )):
      
        # calculate how many kids they'll get
        numberOfChildren = how_many_children(twoParentDist)
        twoParentDist[numberOfChildren] -= 1

        # create a household
        id = population.createdHouses
        house = household(id, 2 + numberOfChildren+1)

        # add parents to the household. Ages for couples come from 
        # guess age of the first parent
        ageParent1 = random.choice(range(95))
        while(population.couples[ageParent1] < 1 or len(population.ageDist[ageParent1]) < 1) :
            ageParent1 = random.choice(range(95))
        parent1 = population.ageDist[ageParent1].pop()
        population.couples[ageParent1] -= 1

        # guess age of the second parent
        # parents have at most 5 years different in age
        ageDiff = random.choice(range(20))

        # we try for the parents to have a 5 year age different, this will work for most people
        ageParent2 = ageParent1 - 10 + ageDiff

        # check that they're not too old to avoid index out of range
        ageParent2 = min(ageParent2, 95)
        while(population.couples[ageParent2] < 1 or len(population.ageDist[ageParent2]) < 1) :
            # if it doesn't work we just give them a random age:
            # some alone parents live with one of their parents and some people have a bigger age difference than 5
            ageParent2 = random.choice(range(95))
        parent2 = population.ageDist[ageParent1].pop()
        population.couples[ageParent2] -= 1

        #add both parents to the houshold
        house.add_member(parent1)
        house.add_member(parent2)
        parent1.update_household(id)
        parent2.update_household(id)

        # we loop through the children and give the kids an age and add them to the household
         # and add create the numberOfChildren wanted
        for child in range(numberOfChildren + 1) :
            # choose random age for child and check if there are still kids of that age, kids have a maximum age of 19
            age = random.choice(range(28))
            while(len(population.ageDist[age]) <1 ) :         
                age = random.choice(range(28))

            # get person from age list and add to household
            person = population.ageDist[age].pop()
            house.add_member(person)
            person.update_household(id)

        # add the household to the houses in the population
        population.houseDict.append(house)

        # increase household id
        population.createdHouses += 1

    return population


def oneParentHH(population, oneParentDist):
    # one parent households
    for parent in range(sum(oneParentDist)):
        # check how many children the parent will get and create the household
        numberOfChildren = how_many_children(oneParentDist)
        oneParentDist[numberOfChildren] -= 1
        # create a house
        id = population.createdHouses
        house = household(id, 1 + numberOfChildren+1)

        # create the parrent, we let their age be between 20 and 55
        age = random.choice(range(35)) + 20
        while(len(population.ageDist[age]) < 1) :
            age = random.choice(range(35)) + 20
        parent = population.ageDist[age].pop()
        house.add_member(parent)
        parent.update_household(id)

        # and add create the numberOfChildren wanted
        for child in range(numberOfChildren + 1) :
            # choose random age for child and check if there are still kids of that age, kids have a maximum age of 19
            age = random.choice(range(19))
            while(len(population.ageDist[age]) <1 ) :
                age = random.choice(range(19))

            # get person from age list and add to household
            person = population.ageDist[age].pop()
            house.add_member(person)
            person.update_household(id)

        # add house to list of houses
        population.houseDict.append(house)
        
        # increase household id
        population.createdHouses += 1

    return population


def make_households(population, N, dataframe, file1, file2, file3):

    # read in data from files 
    makeup_data = read_makeup_households(file1)
    population.noHH = calculate_houses(N, makeup_data)
    child_dist = read_child_distribution(file3)
    household_data = read_households(N, file2)

    population.amountPeople, total_child_or_couple, non_couples = calculate_household(N, household_data)

    # initialise some numbers
    population.createdHouses = 0

    # number of people in a house 
    population.houseDict = []
    population.ageDict = [ [] for _ in range(100)]

    # couple without children
    population = couple_childless(population)

    # couples with children
    population.couples = list(population.amountPeople["Fraction couple with children"])
    population.children = list(population.amountPeople["Fraction child"])
    numberOfCouples = int(sum(population.couples) / 2)

    # two parent households with children
    twoParentDist = [int(numberOfCouples * j) for j in child_dist.iloc[:, 1]]
    twoParentHouses = [i * j for i, j in zip(twoParentDist, [1, 2, 3])]

    # one parent households with children
    oneParent = population.noHH["One Parent"][0]
    oneParentDist = [int(oneParent * j) for j in child_dist.iloc[:, 0]]
    one_parent_houses = [i * j for i, j in zip(oneParentDist, [1, 2, 3])]

    # The number of children does not match up with the households therefore we will add some 4 and 5 person households.
    # determine the amount of children left to be placed
    remaining_children = int(sum(population.children) - sum(one_parent_houses) - sum(twoParentHouses))
    four_houses = round(2 / 3 * remaining_children)
    while (remaining_children - four_houses) % 2 != 0:
        four_houses += 1

    twoParentDist[2] -= four_houses
    twoParentDist.append(four_houses)
    five_houses = (remaining_children - four_houses) / 2
    twoParentDist[2] -= five_houses
    twoParentDist.append(five_houses)
    twoParentHouses = [i * j for i, j in zip(twoParentDist, [1, 2, 3, 4, 5])]

    # add them to the population
    population = oneParentHH(population, oneParentDist)
    population = twoParentHH(population, twoParentDist)

    return population


def create_people(population, N, dataframe, vaccinationreadiness) :
    # read in file with age distrubution
    startage = dataframe["Start of age group"].tolist()
    # we will store the people in lists per age in the following list
    people = [ ]
    people.append([])
    currentAge = 0

    # go through N people and create them as person
    # starting with age 0, we start adding people until we have enough people of a certain age and then continue to the next age
    for i in range(N):
        if(i < startage[currentAge+1]) :
            people[currentAge].append(person(i,currentAge,False))
        else :  
            currentAge += 1
            people.append([])
            people[currentAge].append(person(i,currentAge,False))

    population.ageDist = people

    # one long list (used for vaccinating ie)
    population.people = [item for sublist in people for item in sublist]

    # todo add willingness to get vaccinated

    return population


def create_subnetwork(group1, group2, degree, i0, j0):
    n = group1.size()
    m = group2.size()
    # determine whether the block is a diagonal block,
    # to avoid creating contacts with yourself
    if n == m and i0 == j0:
        isdiagonal = True
    else:
        isdiagonal = False

    # remove some degenerate cases
    if m <= 0 or n <= 0 or (isdiagonal and n == 1):
        return []

    # handle other special cases
    if (isdiagonal and degree >= n - 1) or (not isdiagonal and degree >= n):
        # the matrix should be full
        out = []
        for person1 in group1.members:
            for person2 in group2.members:
                if not person1.person_id == person2.person_id:  # no edges to self
                    out.append((i0 + person1.person_id, j0 + person2.person_id))
                    out.append((j0 + person2.person_id, i0 + person1.person_id))
        return out

    else:
        # determine the number of trials needed to create
        # the desired number of edges, using some basic probability theory
        p = 1 / (m * n)  # probability of a matrix element a(i,j)
        # becoming nonzero in one trial
        if isdiagonal:
            trials = math.floor(math.log(1 - degree / (n - 1)) / math.log(1 - p))
        else:
            trials = math.floor(math.log(1 - degree / n) / math.log(1 - p))

        out = []
        for k in range(trials):
            r1 = rd.randint(0, m - 1)
            i = group2.members[r1].person_id
            r2 = rd.randint(0, n - 1)
            j = group1.members[r2].person_id
            if not i == j:  # no links to self
                if group1.members[r2].household != 0:  # make sure the network is not over connected
                    if group2.age_group_id not in group1.members[r2].overestimate:
                        out.append((i, j))
                        out.append((j, i))
                        over = [T for T in group1.members[r2].household.members if (T != group1.members[r2]) and (T.age in group2.ages)]
                        group1.members[r2].overestimation(group2.age_group_id)
                        for T in over:
                            group1.members[r2].overestimation(group2.age_group_id)

                    if group1.members[r2].overestimate[group2.age_group_id] < degree:
                        out.append((i, j))
                        out.append((j, i))
                        group1.members[r2].overestimation(group2.age_group_id)
                    else:
                        continue

                if group1.members[r2].household == 0:
                    out.append((i, j))
                    out.append((j, i))

        return out


def create_network(dataframe, people, contact_data):
    """This function creates an n by n adjacency matrix A
    that defines a random network with n vertices,
    where vertex i has a number of contacts determined
    by the degree matrix d.

    ngroups = number of age groups represented in the network
    size[g] = size of age group g in the network, i.e. the number
              of persons in the age group. The sum of all sizes is n.
    d[gi][gj] = average degree of a vertex in age group gi, considering
                only connections to age group gj.

    This is a fast method, linear in the number of edges |E|,
    so it can be used to create large networks.
    a is stored as a list of pairs (i,j), sorted by rows, and within
    each row by column index.
    """
    ngroups = dataframe['Age group class object'].nunique()
    Groepen = dataframe['Age group class object'].unique()

    out = []
    i0 = 0
    teller = 1
    for gi in range(ngroups):
        j0 = 0
        for gj in range(ngroups):
            # size is the number of persons of an age group
            # d[gi][gj] is the degree of a block, which is a submatrix
            # containing all contacts between age groups gi and gj.
            out += create_subnetwork(Groepen[gi], Groepen[gj], contact_data[gi][gj], i0, j0)
            sys.stdout.write('\r' + "Blok: " + str(teller))
            sys.stdout.flush()
            teller += 1
            j0 += Groepen[gj].size()
        i0 += Groepen[gi].size()

    # remove duplicates from the list
    a = list(dict.fromkeys(out))

    return a


def read_households(N, household_file):
    # Read the file containing data about the make up of household demographics
    household_data = pd.read_csv(household_file)
    household_data = household_data.fillna(0)  # replace missing data with zero values
    household_data = household_data.drop([0, 97, 98, 99, 100])  # remove extra data
    household_data = household_data.drop(["Geslacht", "Leeftijd", "Perioden"], axis=1)

    # Change notation of number to not use "." for seperation
    for column in household_data.columns:
        household_data[column] = household_data[column].astype(str).apply(lambda x: x.replace('.', ''))
        household_data[column] = household_data[column].astype(int)

    household_data = household_data.set_axis(['Children living at home', 'Couple without children', 'A', 'B'], axis=1)
    household_data["Couple with children"] = household_data["A"] + household_data["B"]
    household_data = household_data.drop(["A", "B"], axis=1)  # remove extra data

    # the amount of children in the network is determined by the amount of couples

    household_data = household_data.reset_index(drop=True)

    return household_data


def calculate_household(N, dataframe):
    # calculate fractions of population
    
    # read in some files 
    total = read_age_distribution('Datafiles/CBS_NL_population_20200101.txt').sum()[0]
    total_child_or_couple = round(N * dataframe.sum().sum() / total)

    out = pd.DataFrame()
    new_names = ["Fraction child", "Fraction couple without children", "Fraction couple with children"]
    total_people = dataframe.sum().sum()
    for column, name in zip(dataframe.columns, new_names):
        out[name] = round(total_child_or_couple * (dataframe[column] / total_people))
    for i in ["Fraction couple without children", "Fraction couple with children"]:
        if out.loc[:, i].sum() % 2 != 0:
            age = rd.choice(range(19, len(out[i].tolist())))
            out.loc[age, i] = out.loc[age, i] + 1

    # make sure number of people in data matches N. Must remove from children since otherwise couples possibly uneven.
    while out.sum().sum() > total_child_or_couple:
        max = out["Fraction child"].idxmax()
        out.loc[max, "Fraction child"] = out.loc[max, "Fraction child"] - 1

    while out.sum().sum() < total_child_or_couple:
        max = out["Fraction child"].idxmax()
        out.loc[max, "Fraction child"] = out.loc[max, "Fraction child"] + 1

    assert out.sum().sum() == total_child_or_couple

    return out, total_child_or_couple, N - total_child_or_couple


def calculate_houses(N, dataframe):
    out = pd.DataFrame()
    makeup_data_list = dataframe.values[0][:-1]

    people_in_household = [1, 1, 2, 3, 4, 5]
    fractions = [i / makeup_data_list[0] for i in makeup_data_list]
    number_of_households = [int((N * i) // k) for i, k in zip(fractions, people_in_household)]
    number_of_households[0] = sum(number_of_households[1:])
    column_names = ["Total", "One person", "Two Person", "Three person", "Four person", "Five or more person"]

    for name, value in zip(column_names, number_of_households):
        out[name] = [value]

    out["One Parent"] = int(dataframe["One parent household"] * sum(number_of_households[2:]))

    return out


def makeSchoolClasses(population):
    """This function divides the age groups 4 to 18 in subgroups with an average
    of the size of schoolclasses. We choose to let the groups have not less than
    5 less members than the average and not more than 5 more members than the
    average"""

    average = KIDSINGROUP
    groupID = 0

    # keeps track of the kids that are placed in a group
    counter = 0

    # we loop through all the ages. For every age we keep looping through that age until there are no kids left of that age
    for age in range(4,19) :
        while(counter < len(population.ageDist[age])) :
            # create a new group and decide the size of the group
            size = random.choice(average - 5, average + 6)
            size = min(size, len(population.ageDist[age]))
            group = schoolGroup(groupID,age)

            # add the kids to the group
            for child in range(size) :
                group.add_member(population.people[counter])


    return population

# todo create student houses
def makeStudentHouses(population):


    return population

# todo create retirement homes
def makeRetirementHome(population):


    return population