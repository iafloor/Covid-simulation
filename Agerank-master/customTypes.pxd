cdef public struct person:
            int person_id, age, daysSinceInfection, weekOfVaccination, household, susceptible, infectious, quarantined, hospitalised, recovered, vaccinated, deceased, schoolClass, infectionProtected
            int vaccinationReadiness, dontVaccme, daysSinceRecovery

cdef struct changes:
            int newInfections, totalInfected, hospitalized, deceased
