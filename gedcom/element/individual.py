# -*- coding: utf-8 -*-

# Python GEDCOM Parser
#
# Copyright (C) 2018 Damon Brodie (damon.brodie at gmail.com)
# Copyright (C) 2018-2019 Nicklas Reincke (contact at reynke.com)
# Copyright (C) 2016 Andreas Oberritter
# Copyright (C) 2012 Madeleine Price Ball
# Copyright (C) 2005 Daniel Zappala (zappala at cs.byu.edu)
# Copyright (C) 2005 Brigham Young University
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#
# Further information about the license: http://www.gnu.org/licenses/gpl-2.0.html
#
# Version History
# 2022-12-21 - Added ability to match on gender via criteria_match and gender_match.   
# 2022-12-21 - Adding birthdate match...

import re as regex
from gedcom.element.element import Element
from gedcom.helpers import deprecated
import gedcom.tags


class NotAnActualIndividualError(Exception):
    pass


class IndividualElement(Element):

    ###MOT 2023.08.10 - added attempt to check for exact match
    def is_identical(self,a):
        return str(self)==str(a)

    def is_individual(self):
        """Checks if this element is an actual individual
        :rtype: bool
        """
        return self.get_tag() == gedcom.tags.GEDCOM_TAG_INDIVIDUAL

    def is_deceased(self):
        """Checks if this individual is deceased
        :rtype: bool
        """
        if not self.is_individual():
            return False

        for child in self.get_child_elements():
            if child.get_tag() == gedcom.tags.GEDCOM_TAG_DEATH:
                return True

        return False

    def is_child(self):
        """Checks if this element is a child of a family
        :rtype: bool
        """
        if not self.is_individual():
            raise NotAnActualIndividualError(
                "Operation only valid for elements with %s tag" % gedcom.tags.GEDCOM_TAG_INDIVIDUAL
            )

        found_child = False

        for child in self.get_child_elements():
            if child.get_tag() == gedcom.tags.GEDCOM_TAG_FAMILY_CHILD:
                found_child = True

        return found_child

    def is_private(self):
        """Checks if this individual is marked private
        :rtype: bool
        """
        if not self.is_individual():
            return False

        for child in self.get_child_elements():
            if child.get_tag() == gedcom.tags.GEDCOM_TAG_PRIVATE:
                private = child.get_value()
                if private == 'Y':
                    return True

        return False

    def get_name(self):
        """Returns an individual's names as a tuple: (`str` given_name, `str` surname)
        :rtype: tuple
        """
        given_name = ""
        surname = ""

        if not self.is_individual():
            return given_name, surname

        # Return the first gedcom.tags.GEDCOM_TAG_NAME that is found.
        # Alternatively as soon as we have both the gedcom.tags.GEDCOM_TAG_GIVEN_NAME and _SURNAME return those.
        found_given_name = False
        found_surname_name = False

        for child in self.get_child_elements():
            if child.get_tag() == gedcom.tags.GEDCOM_TAG_NAME:
                # Some GEDCOM files don't use child tags but instead
                # place the name in the value of the NAME tag.
                if child.get_value() != "":
                    name = child.get_value().split('/')

                    if len(name) > 0:
                        given_name = name[0].strip()
                        if len(name) > 1:
                            surname = name[1].strip()

                    return given_name, surname

                for childOfChild in child.get_child_elements():

                    if childOfChild.get_tag() == gedcom.tags.GEDCOM_TAG_GIVEN_NAME:
                        given_name = childOfChild.get_value()
                        found_given_name = True

                    if childOfChild.get_tag() == gedcom.tags.GEDCOM_TAG_SURNAME:
                        surname = childOfChild.get_value()
                        found_surname_name = True

                if found_given_name and found_surname_name:
                    return given_name, surname

        # If we reach here we are probably returning empty strings
        return given_name, surname

    #MOT: added 2022.12.19 gender match
    def gender_match(self, gender_to_match):
        """Matches a string with the gender of an individual
        :type gender_to_match: str
        :rtype: bool
        """
        return self.get_gender() == gender_to_match

    def surname_match(self, surname_to_match):
        """Matches a string with the surname of an individual
        :type surname_to_match: str
        :rtype: bool
        """
        (given_name, surname) = self.get_name()
        return regex.search(surname_to_match, surname, regex.IGNORECASE)

    @deprecated
    def given_match(self, name):
        """Matches a string with the given name of an individual
        ::deprecated:: As of version 1.0.0 use `given_name_match()` method instead
        :type name: str
        :rtype: bool
        """
        return self.given_name_match(name)

    def given_name_match(self, given_name_to_match):
        """Matches a string with the given name of an individual
        :type given_name_to_match: str
        :rtype: bool
        """
        (given_name, surname) = self.get_name()
        return regex.search(given_name_to_match, given_name, regex.IGNORECASE)

    def get_gender(self):
        """Returns the gender of a person in string format
        :rtype: str
        """
        gender = ""

        if not self.is_individual():
            return gender

        for child in self.get_child_elements():
            if child.get_tag() == gedcom.tags.GEDCOM_TAG_SEX:
                gender = child.get_value()

        return gender

    def get_birth_data(self):
        """Returns the birth data of a person formatted as a tuple: (`str` date, `str` place, `list` sources)
        :rtype: tuple
        """
        date = ""
        place = ""
        sources = []

        if not self.is_individual():
            return date, place, sources

        for child in self.get_child_elements():
            if child.get_tag() == gedcom.tags.GEDCOM_TAG_BIRTH:
                for childOfChild in child.get_child_elements():

                    if childOfChild.get_tag() == gedcom.tags.GEDCOM_TAG_DATE:
                        date = childOfChild.get_value()

                    if childOfChild.get_tag() == gedcom.tags.GEDCOM_TAG_PLACE:
                        place = childOfChild.get_value()

                    if childOfChild.get_tag() == gedcom.tags.GEDCOM_TAG_SOURCE:
                        sources.append(childOfChild.get_value())

        return date, place, sources

    def get_birth_year(self):
        """Returns the birth year of a person in integer format
        :rtype: int
        """
        date = ""

        if not self.is_individual():
            return date

        for child in self.get_child_elements():
            if child.get_tag() == gedcom.tags.GEDCOM_TAG_BIRTH:
                for childOfChild in child.get_child_elements():
                    if childOfChild.get_tag() == gedcom.tags.GEDCOM_TAG_DATE:
                        date_split = childOfChild.get_value().split()
                        date = date_split[len(date_split) - 1]

        if date == "":
            return -1
        try:
            return int(date)
        except ValueError:
            return -1

    #MOT: 2022.12.21 added get_birth date
    def get_birth_date(self):
        """Returns the birth date of a person in string format
        :rtype: str
        """
        date = ""

        if not self.is_individual():
            return date

        for child in self.get_child_elements():
            if child.get_tag() == gedcom.tags.GEDCOM_TAG_BIRTH:
                for childOfChild in child.get_child_elements():
                    if childOfChild.get_tag() == gedcom.tags.GEDCOM_TAG_DATE:
                        date = str(childOfChild.get_value())

        try:
            return str(date)
        except ValueError:
            return ""

	#MOT: 2023.08.09 added get_death_date
    def get_death_date(self):
        """Returns the death date of a person in string format
        :rtype: str
        """
        date = ""

        if not self.is_individual():
            return date

        for child in self.get_child_elements():
            if child.get_tag() == gedcom.tags.GEDCOM_TAG_DEATH:
                for childOfChild in child.get_child_elements():
                    if childOfChild.get_tag() == gedcom.tags.GEDCOM_TAG_DATE:
                        date = str(childOfChild.get_value())

        try:
            return str(date)
        except ValueError:
            return ""

    def get_death_data(self):
        """Returns the death data of a person formatted as a tuple: (`str` date, `str` place, `list` sources)
        :rtype: tuple
        """
        date = ""
        place = ""
        sources = []

        if not self.is_individual():
            return date, place

        for child in self.get_child_elements():
            if child.get_tag() == gedcom.tags.GEDCOM_TAG_DEATH:
                for childOfChild in child.get_child_elements():
                    if childOfChild.get_tag() == gedcom.tags.GEDCOM_TAG_DATE:
                        date = childOfChild.get_value()
                    if childOfChild.get_tag() == gedcom.tags.GEDCOM_TAG_PLACE:
                        place = childOfChild.get_value()
                    if childOfChild.get_tag() == gedcom.tags.GEDCOM_TAG_SOURCE:
                        sources.append(childOfChild.get_value())

        return date, place, sources

    def get_death_year(self):
        """Returns the death year of a person in integer format
        :rtype: int
        """
        date = ""

        if not self.is_individual():
            return date

        for child in self.get_child_elements():
            if child.get_tag() == gedcom.tags.GEDCOM_TAG_DEATH:
                for childOfChild in child.get_child_elements():
                    if childOfChild.get_tag() == gedcom.tags.GEDCOM_TAG_DATE:
                        date_split = childOfChild.get_value().split()
                        date = date_split[len(date_split) - 1]

        if date == "":
            return -1
        try:
            return int(date)
        except ValueError:
            return -1

    @deprecated
    def get_burial(self):
        """Returns the burial data of a person formatted as a tuple: (`str` date, `str´ place, `list` sources)
        ::deprecated:: As of version 1.0.0 use `get_burial_data()` method instead
        :rtype: tuple
        """
        self.get_burial_data()

    def get_burial_data(self):
        """Returns the burial data of a person formatted as a tuple: (`str` date, `str´ place, `list` sources)
        :rtype: tuple
        """
        date = ""
        place = ""
        sources = []

        if not self.is_individual():
            return date, place

        for child in self.get_child_elements():
            if child.get_tag() == gedcom.tags.GEDCOM_TAG_BURIAL:
                for childOfChild in child.get_child_elements():

                    if childOfChild.get_tag() == gedcom.tags.GEDCOM_TAG_DATE:
                        date = childOfChild.get_value()

                    if childOfChild.get_tag() == gedcom.tags.GEDCOM_TAG_PLACE:
                        place = childOfChild.get_value()

                    if childOfChild.get_tag() == gedcom.tags.GEDCOM_TAG_SOURCE:
                        sources.append(childOfChild.get_value())

        return date, place, sources

    @deprecated
    def get_census(self):
        """Returns a list of censuses of an individual formatted as tuples: (`str` date, `str´ place, `list` sources)
        ::deprecated:: As of version 1.0.0 use `get_census_data()` method instead
        :rtype: list of tuple
        """
        self.get_census_data()

    def get_census_data(self):
        """Returns a list of censuses of an individual formatted as tuples: (`str` date, `str´ place, `list` sources)
        :rtype: list of tuple
        """
        census = []

        if not self.is_individual():
            raise NotAnActualIndividualError(
                "Operation only valid for elements with %s tag" % gedcom.tags.GEDCOM_TAG_INDIVIDUAL
            )

        for child in self.get_child_elements():
            if child.get_tag() == gedcom.tags.GEDCOM_TAG_CENSUS:

                date = ''
                place = ''
                sources = []

                for childOfChild in child.get_child_elements():

                    if childOfChild.get_tag() == gedcom.tags.GEDCOM_TAG_DATE:
                        date = childOfChild.get_value()

                    if childOfChild.get_tag() == gedcom.tags.GEDCOM_TAG_PLACE:
                        place = childOfChild.get_value()

                    if childOfChild.get_tag() == gedcom.tags.GEDCOM_TAG_SOURCE:
                        sources.append(childOfChild.get_value())

                census.append((date, place, sources))

        return census

    def get_last_change_date(self):
        """Returns the date of when the person data was last changed formatted as a string
        :rtype: str
        """
        date = ""

        if not self.is_individual():
            return date

        for child in self.get_child_elements():
            if child.get_tag() == gedcom.tags.GEDCOM_TAG_CHANGE:
                for childOfChild in child.get_child_elements():
                    if childOfChild.get_tag() == gedcom.tags.GEDCOM_TAG_DATE:
                        date = childOfChild.get_value()

        return date

    def get_occupation(self):
        """Returns the occupation of a person
        :rtype: str
        """
        occupation = ""

        if not self.is_individual():
            return occupation

        for child in self.get_child_elements():
            if child.get_tag() == gedcom.tags.GEDCOM_TAG_OCCUPATION:
                occupation = child.get_value()

        return occupation

    def birth_year_match(self, year):
        """Returns `True` if the given year matches the birth year of this person
        :type year: int
        :rtype: bool
        """
        return self.get_birth_year() == year
        
    #MOT: 2022-12-21 added birth date match    
    def birth_date_match(self, date):
        """Returns `True` if the given date matches the birth date of this person
        :type date: int
        :rtype: bool
        """

        return self.get_birth_date() == date
        
    def birth_range_match(self, from_year, to_year):
        """Checks if the birth year of a person lies within the given range
        :type from_year: int
        :type to_year: int
        :rtype: bool
        """
        birth_year = self.get_birth_year()

        if from_year <= birth_year <= to_year:
            return True

        return False

    def death_year_match(self, year):
        """Returns `True` if the given year matches the death year of this person
        :type year: int
        :rtype: bool
        """
        return self.get_death_year() == year

    def death_range_match(self, from_year, to_year):
        """Checks if the death year of a person lies within the given range
        :type from_year: int
        :type to_year: int
        :rtype: bool
        """
        death_year = self.get_death_year()

        if from_year <= death_year <= to_year:
            return True

        return False

    #MOT: 2022-12-21 - added match based on another indivudal element
    def is_match(self, ind):
		#### TODO: not functional - considering using work in compare code
        """
        Checks if this individual matches another individual
        'ind' is the individual to check for a match against.
        Returns a simple % confidence based on match to:
        Surname - 20%
        Initial - 10%
        Forename - 20%
        Year of Birth - 10%
        Year of Death - 10%
        Date of Birth - 15%
        Date of Death - 15%
        
        :type ind: IndividualElement
        :rtype: int
        """
        
        match = 0

        #TODO: Actually try matching!

        return match

    def criteria_match(self, criteria):
		# MOT: 2022.12.21 Added gender match
		# MOT: 2022.12.21 Added birth_date match
        """Checks if this individual matches all of the given criteria

        `criteria` is a colon-separated list, where each item in the
        list has the form [name]=[value]. The following criteria are supported:

        surname=[name]
             Match a person with [name] in any part of the `surname`.
        given_name=[given_name]
             Match a person with [given_name] in any part of the given `given_name`.
        gender=[gender]
             Match a person with [gender] as their gender.
        birth=[year]
             Match a person whose birth year is a four-digit [year].
        birth_date=[date]
		     Match a person whose birth date matches [date].
        birth_range=[from_year-to_year]
             Match a person whose birth year is in the range of years from
             [from_year] to [to_year], including both [from_year] and [to_year].

        :type criteria: str
        :rtype: bool
        """

        # Check if criteria is a valid criteria and can be split by `:` and `=` characters
        try:
            for criterion in criteria.split(':'):
                criterion.split('=')
        except ValueError:
            return False

        match = True

        for criterion in criteria.split(':'):
            key, value = criterion.split('=')

            if key == "surname" and not self.surname_match(value):
                match = False
            elif key == "name" and not self.given_name_match(value):
                match = False
            elif key == "gender" and not self.gender_match(value):
                match = False
            elif key == "birth":

                try:
                    year = int(value)
                    if not self.birth_year_match(year):
                        match = False
                except ValueError:
                    match = False

            elif key == "birth_date":

                try:
                    #date = datetime(value)
                    if not self.birth_date_match(value):
                        match = False
                except ValueError:
                    match = False

            elif key == "birth_range":

                try:
                    from_year, to_year = value.split('-')
                    from_year = int(from_year)
                    to_year = int(to_year)
                    if not self.birth_range_match(from_year, to_year):
                        match = False
                except ValueError:
                    match = False

            elif key == "death":

                try:
                    year = int(value)
                    if not self.death_year_match(year):
                        match = False
                except ValueError:
                    match = False

            elif key == "death_range":

                try:
                    from_year, to_year = value.split('-')
                    from_year = int(from_year)
                    to_year = int(to_year)
                    if not self.death_range_match(from_year, to_year):
                        match = False
                except ValueError:
                    match = False

        return match
