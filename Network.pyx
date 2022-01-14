import random
import random as rd
import sys
from customTypes cimport person
from Read_data import *
from Classes import *
from Parameters import *


def how_many_children(available_children):
    # calculates how many children a family has. We check the maximum and choose a random number,
    # if there are still households needed with that many kids we're done, else we choose another number
    maxNumberOfChildren = len(available_children)
    numberOfChildren = random.choice((range(0,maxNumberOfChildren)))
    while available_children[numberOfChildren] < 1:
        numberOfChildren = random.choice((range(0,maxNumberOfChildren)))
    return numberOfChildren

def createCouples(population, couples, childless, childDist):
    """This function creates the couples living in a household.
    We take two random people and add children if they should not be
    childless. This function gets a list of the ages of the couples, a bool
    childless which is true if they do not have children and a childDist which
    is the distribution of the age of children."""
    # rounding off error?
    if childDist != 0 :
        numberOfCouples = int(min(sum(couples)/2, sum(childDist)))
    else :
        numberOfCouples = int(sum(couples) / 2)

    # calculate all ages available for the couples
    availableAges = {}

    # calculate the start age
    startage = 0
    while (couples[startage] < 1):
        startage += 1

    for age in range(startage, len(couples)):
        availableAges[age] = couples[age]

    # we give all the couples an age
    for couple in range(numberOfCouples - 1):
        members = []
        # pick the lowest available age for person 1
        age1 = list(availableAges.keys())[0]
        members.append(population.ageDist[age1].pop())
        availableAges[age1] -= 1

        # if that was the last person of that age, we deleted the available age
        if availableAges[age1] < 1:
            availableAges.pop(abs(age1))  # ages start at 19

        # pick age for person 2
        ageDifference = random.choice(range(5))
        ageDifference = min(ageDifference, len(availableAges) - 1)
        age2 = list(availableAges.keys())[ageDifference]
        members.append(population.ageDist[age2].pop())
        availableAges[age2] -= 1

        # if that was the last person of that age, we deleted the available age
        if availableAges[age2] < 1:
            availableAges.pop(abs(age2))  # ages start at 19

        # if they are parents living with kids, we add them
        if childless :
            population = addToHousehold(population, members)
        else :
            population, members, childDist = addChildren(population, members, childDist)
            population = addToHousehold(population, members)


    return population


def addToHousehold(population, members) :
    """This function takes a list of members and the population, adds
    the members to a house and then add that house to the list of households
    saved in the population."""
    # create a new household
    id = population.createdHouses
    house = household(id, len(members), [])
    
    cdef person p 

    # we put the members in a household
    for i in range(len(members)):
        p = members[i]
        house.add_member(p)
        p.household = id
        population.people[p.person_id] = p

    # and we put their ids in the hosuehold
    for i in range(len(members)):
        p = members[i]
        house.ids.append(p.person_id)
    # add house to list of houses
    population.houseDict.append(house)

    # increase household id
    population.createdHouses += 1
    return population


def addChildren(population, members, childDist) :
    # calculate how many kids they'll get
    numberOfChildren = how_many_children(childDist)
    childDist[numberOfChildren] -= 1
    cdef person p = members[0]
    ageparent = p.age

    age = max(0, ageparent - 40) # parents are at most 40 years older than their youngest child
    # create all the children
    for child in range(numberOfChildren + 1):
        # choose random age for child and check if there are still kids of that age
        while(len(population.ageDist[age]) <1) :
            age += 1
        child = population.ageDist[age].pop()
        members.append(child)
        ageDifference = random.choice(range(5))
        age += ageDifference

    return population, members, childDist


def oneParentHousehold(population, oneParentDist):
    """This function chooses people for the households containing one parent and
    a number of children. It takes the population in which the household will be
    saved and the distribution of the children's ages as input."""
    # one parent households
    for parent in range(sum(oneParentDist)):
        members = []
        # create the parent, we let their age be between 20 and 55
        age = random.choice(range(35)) + 20
        while(len(population.ageDist[age]) < 1) :
            age = random.choice(range(35)) + 20
        members.append(population.ageDist[age].pop())

        # add the numberOfChildren wanted and add the the house to the household
        population, members, oneParentDist = addChildren(population, members, oneParentDist)
        population = addToHousehold(population, members)

    return population


def fillHousehold(number, population, lowerLimitAge, upperLimitAge, minMembers, maxMembers) :
    """In this definition we fill a list of members of a houshold and add them later to the list of households.
    We add a random number between minMembers and maxMembers of people to the household. The ages of the
    people are between the lowerlimitAge and the upperLimitAge. This function is used to fill the retirement homes
    and the student houses."""
    # while there are still people to be put into households
    while (number > 0):
        members = []
        numberOfMembers = int(min(random.choice(range(minMembers,maxMembers)), number))

        # for the number of members we're going to add to a household, we choose randomly an age for them. If there
        # are no more people available of such age, we choose a new age.
        for i in range(numberOfMembers):
            age = random.choice(range(lowerLimitAge, upperLimitAge))
            while (len(population.ageDist[age]) < 1):
                age = random.choice(range(lowerLimitAge,upperLimitAge))
            person = population.ageDist[age].pop()

            # add member to list of memebers
            members.append(person)

        # add the list of members to the population
        population = addToHousehold(population, members)
        number -= numberOfMembers
    return population


def studentHousehold(population) :
    # number of students that live in a studenthome
    number = int(STUDENTHOUSE*N/100)
    population = fillHousehold(number, population, 18,25, 3,13)
    return population


def retirementHousehold(population) :
    # number of people living in a retirement house
    number = int(RETIREMENT*N/100)
    population = fillHousehold(number, population, 75,105, 44, 52)
    return population


def make_households(population, file1, file2, file3):
    """This function reads in the data about the people in the population and then creates different
    households based on this information. """

    # read in data from files 
    makeup_data = read_makeup_households(file1)
    population.noHH = calculate_houses(N, makeup_data)
    child_dist = read_child_distribution(file3)
    household_data = read_households(N, file2)

    population.amountPeople, total_child_or_couple = calculate_household(N, household_data)

    # couples with children
    couples = list(population.amountPeople["Fraction couple with children"])
    p = sum(couples)
    population.children = list(population.amountPeople["Fraction child"])
    q = sum(population.children)
    numberOfCouples = int(sum(couples) / 2)

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
    five_houses = int(remaining_children - four_houses) / 2
    twoParentDist[2] -= five_houses
    twoParentDist.append(five_houses)

    # add them to the population
    population = studentHousehold(population)
    population = createCouples(population, list(population.amountPeople["Fraction couple without children"]) , True, 0)
    population = oneParentHousehold(population, oneParentDist)
    population = createCouples(population, list(population.amountPeople["Fraction couple with children"]) , False, twoParentDist )
    population = retirementHousehold(population)
    population = otherHouseholds(population)

    return population


def otherHouseholds(population) :
    """"This function adds all the popele that have not been assigned to a household
    yet to a household. First we filter all of the people that are living alone out of the list.
    We do not put those people in a household."""
    # fill all people living alone
    cdef person p
    for person in range(int(LIVINGALONE*N/100)) :
        getIndex = random.choice(range(105))
        while(len(population.ageDist[getIndex]) < 1) :
            getIndex = random.choice(range(105))
        p = population.ageDist[getIndex].pop()
        index = p.person_id
        p.household = -1
        population.people[index] = p
    # calculate how many people there are left
    k = 0
    for i in range(len(population.ageDist)):
        for j in range(len(population.ageDist[i])):
            k += 1

    # now we have still some people left, we'll put them in households of 2,3 or 4
    lowestAge = 0
    while k > 0 :
        numberOfMembers = int(min(k, random.choice(range(2,5))))
        members = []
        for i in range(numberOfMembers) :
            # we look for the lowest age still available
            while(len(population.ageDist[lowestAge]) < 1) :
                lowestAge += 1
            person = population.ageDist[lowestAge].pop()
            members.append(person)
        population = addToHousehold(population, members)
        k -= numberOfMembers
    return population


def create_people(population, N, dataframe) :
    """This function creates all the people that will be living in the population.
    We add them to agegroups to easily find people in a certain age when filling hosueholds. We
    add them to a dataframe to be able to create the contact matrix later."""

    # read in file with age distrubution
    startage = dataframe["Start of age group"].tolist()
    # we will store the people in lists per age in the following list
    cdef person p
    people = [ ]
    people.append([])
    currentAge = 0

    # go through N people and create them as person
    # starting with age 0, we start adding people until we have enough people of a certain age and then continue to the next age
    for i in range(N):
        if(i < startage[currentAge+1]) :
            p.person_id = i
            p.age = currentAge
            # we need to assign values to all variables of person
            p.daysSinceInfection = 0
            p.weekOfVaccination = -1
            p.household = -1
            p.infectious = 0
            p.susceptible = 1
            p.quarantined = 0
            p.hospitalised = 0
            p.recovered = 0
            p.vaccinated = 0
            p.deceased = 0
            p.vaccinationReadiness = 0
            p.dontVaccme = 0
            p.infectionProtected = 0
            p.schoolClass = -1
            p.daysSinceRecovery = 0
            people[currentAge].append(p)
            dataframe.loc[currentAge, 'Age group class object'].members.append(p)
        else :  
            currentAge += 1
            people.append([])
            p.person_id = i
            p.age = currentAge
            # we need to assign values to all variables of person
            p.daysSinceInfection = 0
            p.weekOfVaccination = -1
            p.household = -1
            p.infectious = 0
            p.susceptible = 1
            p.quarantined = 0
            p.hospitalised = 0
            p.recovered = 0
            p.vaccinated = 0
            p.deceased = 0
            p.vaccinationReadiness = 0
            p.dontVaccme = 0
            p.infectionProtected = 0
            p.schoolClass = -1
            p.daysSinceRecovery = 0
            people[currentAge].append(p)
            dataframe.loc[currentAge, 'Age group class object'].members.append(p)

    population.ageDist = people

    # one long list (used for vaccinating ie)
    population.people = [item for sublist in people for item in sublist]
    return population


def create_subnetwork(group1, group2, degree, i0, j0):
    cdef person persona, personb
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
                    i = group2.members[r1]["person_id"]
                    r2 = rd.randint(0, n - 1)
                    j = group1.members[r2]["person_id"]
                    if not i == j:  # no links to self
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
            p = Groepen[gi]
            q = contact_data[gi][gj]
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
    total_child_or_couple = round(N * dataframe.sum().sum()  / total)
    #
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

    return out, total_child_or_couple


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
            size = random.choice(range(average - 5, average + 6))
            size = min(size, len(population.ageDist[age]))
            group = schoolGroup(groupID,age)

            # add the kids to the group
            for child in range(size) :
                group.add_member(population.people[counter])

            # add group to population
            population.otherGroups.append(group)


    return population
