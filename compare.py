# Import the things we need
from gedcom.element.individual import IndividualElement
from gedcom.parser import Parser
import datetime

############### SUB-ROUTINES ######################

# This routine tries to ensure the date is in a simple, common format
def GetStandardisedDate(txt):
	txt=txt.upper()
	txt=txt.replace('JANUARY','JAN')
	txt=txt.replace('FEBRUARY','FEB')
	txt=txt.replace('MARCH','MAR')
	txt=txt.replace('APRIL','APR')
	txt=txt.replace('MAY','MAY')
	txt=txt.replace('JUNE','JUN')
	txt=txt.replace('JULY','JUL')
	txt=txt.replace('AUGUST','AUG')
	txt=txt.replace('SEPTEMBER','SEP')
	txt=txt.replace('OCTOBER','OCT')
	txt=txt.replace('NOVEMBER','NOV')
	txt=txt.replace('DECEMBER','DEC')
	txt=txt.replace('ABOUT','ABT')
	txt=txt.replace('.','')
	
	return txt

# This routine returns a name in a nice standaradised format
def GetStandardisedName(ind):
	#  Input is an Individual record
	#  Output is in string format "Forenames Surname (DoB-YoD)"
	#  Example "Joe Billy Bloggs (1911-?)"
	
	# extract the names
	(firstname, surname)=ind.get_name()
	
	# extract the year of birth
	YoB=ind.get_birth_year()
	
	# extract the year of death and deal with probably deceased people without a year of birth/death
	if ind.is_deceased() or datetime.date.today().year-YoB>120:
		YoD=ind.get_death_year()
		if YoD==-1: YoD='?'
	else:
		YoD=''
	if YoB==-1: YoB='?'
	
	# construct the format and return it
	ident = firstname+' '+surname+' ('+str(YoB)+'-'+str(YoD)+')'
	return ident

# This routine loads the requested GEDCOMs and locates the requested individual
def LoadGEDCOMs(file_path_1,file_path_2,root_person_criteria):
	# Global variables
	global root_person_1
	global root_person_2
	global gedcom_parser_1
	global gedcom_parser_2
	root_person_1 = ''
	root_person_2 = ''
	# Initialize the parser
	gedcom_parser_1 = Parser()
	gedcom_parser_2 = Parser()
	
	# Parse your file
	gedcom_parser_1.parse_file(file_path_1, False)
	root_child_elements_1 = gedcom_parser_1.get_root_child_elements()

	gedcom_parser_2.parse_file(file_path_2, False)
	root_child_elements_2 = gedcom_parser_2.get_root_child_elements()

	# Iterate through all root child elements
	for element in root_child_elements_1:

		# Is the `element` an actual `IndividualElement`? (Allows usage of extra functions such as `surname_match` and `get_name`.)
		if isinstance(element, IndividualElement):
			if element.criteria_match(root_person_criteria):
				root_person_1 = element
				exit

	# Iterate through all root child elements
	for element in root_child_elements_2:

		# Is the `element` an actual `IndividualElement`? (Allows usage of extra functions such as `surname_match` and `get_name`.)
		if isinstance(element, IndividualElement):
			if element.criteria_match(root_person_criteria):
				root_person_2 = element
				exit

# This routine does a simple comparison.  Used to decide if close enough to consider for more detailed matching
def SimpleCompare(ind1, ind2):
	(firstnames_1,surname_1)=ind1.get_name()
	(firstnames_2,surname_2)=ind2.get_name()
	initial_1=firstnames_1[:1]
	initial_2=firstnames_2[:1]
	
	if DEBUGMODE>4: print('   -->SimpleCompare: '+initial_1+' '+surname_1+' vs '+initial_2+' '+surname_2)
	
	return (initial_1==initial_2) and (surname_1==surname_2)

# This route does detailed comparison of an individual and outputs findings
def CompareIndividuals(ind1, ind2):
	global DEBUGMODE
	global perfect_matches
	global output
	# check we actually have two individual records first!
	if isinstance(ind1, IndividualElement)==False or isinstance(ind2, IndividualElement)==False:
		if DEBUGMODE>2: print('>>>Comparing-> One or other is not an individual record')
		return 0
	else:
		retvalue = 0
	
	# extract the names
	(firstname_1, surname_1)=ind1.get_name()
	initial_1 = firstname_1[:1]
	(firstname_2, surname_2)=ind2.get_name()
	initial_2 = firstname_2[:1]
	
	if DEBUGMODE>0: print('>>>Comparing-> '+GetStandardisedName(ind1)+' vs '+GetStandardisedName(ind2))
	
	# next check the basics: Surname, Initial, Gender, YoB, YoD - 10% each
	if ind1.get_gender()==ind2.get_gender(): 
		retvalue=retvalue+0.1 
	else: 
		output+=' - GENDER MIS-MATCH : '+ind1.get_gender()+' vs '+ind2.get_gender()+'\n'
	
	if surname_1==surname_2: 
		retvalue=retvalue+0.1
	else: 
		output+=' - SURNAME MIS-MATCH : '+surname_1+' vs '+surname_2+'\n'

	# next check forename matches - plus 20% if matches exactly, plus 10% if just initial matches
	if firstname_1==firstname_2: 
		retvalue=retvalue+0.2 
	elif initial_1==initial_2: 
		retvalue=retvalue+0.1  
		output+=' - FULL NAME MIS-MATCH, FIRST INITIAL OK : '+firstname_1+' vs '+firstname_2+'\n'
	else: 
		output+=' - FULL NAME MIS-MATCH : '+firstname_1+' vs '+firstname_2+'\n'
	
	#### TODO: Handle instances where one or other date is not set, possibly "about", "Abt." and "March" vs "Mar" too?
	if ind1.get_birth_year()==ind2.get_birth_year():
		retvalue=retvalue+0.1 
	else: 
		output+=' - BIRTH YEAR MIS-MATCH : '+str(ind1.get_birth_year())+' vs '+str(ind2.get_birth_year())+'\n'
		
	if ind1.get_death_year()==ind2.get_death_year(): 
		retvalue=retvalue+0.1 
	else: 
		output+=' - DEATH YEAR MIS-MATCH : '+str(ind1.get_death_year())+' vs '+str(ind2.get_death_year())+'\n'
	
#	# All of the above must match (i.e. 50% confidence) to continue, otherwise reject the match
	if retvalue<0.5: 
		if DEBUGMODE>0: print('>>>Comparing-> Match insufficient at '+str(retvalue))
		return 0
	
	# next check DoB set and matches - plus 20% if matches exactly
	if GetStandardisedDate(ind1.get_birth_date())==GetStandardisedDate(ind2.get_birth_date()): 
		retvalue=retvalue+0.2 
	else: 
		output+=' - DOB MIS-MATCH : '+ind1.get_birth_date()+' vs '+ind2.get_birth_date()+'\n'
	
	# next check DoB set and matches - plus 20% if matches exactly
	if GetStandardisedDate(ind1.get_death_date())==GetStandardisedDate(ind2.get_death_date()): 
		retvalue=retvalue+0.2 
	else: 
		output+=' - DOD MIS-MATCH : '+ind1.get_death_date()+' vs '+ind2.get_death_date()+'\n'
	
	if retvalue>=1:
		perfect_matches += 1
		output+=' + INDIVIDUAL IS A PERFECT MATCH!\n'
	
	# otherwise, we have a match!	
	return retvalue

# This routine adds 2 individuals to the list for checking, first checking that they are not already there and have not already been checked!
def AddToList(ind_1, ind_2, sep):
	global list_of_checked
	global list_of_matches
	global list_of_matches_sep
	global SCOPE_SEP

	if sep>SCOPE_SEP:
		return False
	if (ind_1,ind_2) in list_of_checked: 
		return False
	else:
		if (ind_1,ind_2) in list_of_matches: 
			return False 
		else:
			list_of_matches = [(ind_1,ind_2)] + list_of_matches
			list_of_matches_sep = [sep] + list_of_matches_sep
			return True

###############   MAIN PROGRAM    ################## 
 
#### TODO: Allow input of file names
#### TODO: Allow input of criteria for root person to find

#### TODO: Allow input of debugmode (DEBUGMODE)
DEBUGMODE=0

#### TODO: Allow input of scope as ancestors only vs all (SCOPE_ALL)
SCOPE_ALL=False

#### TODO: Allow input of max separation (SCOPE_SEP)
SCOPE_SEP=99

#### TODO: Allow input of outputting all individuals or just those with issues (OUTPUT_ALL)
OUTPUT_ALL=False

#### TODO: Check marriage records of individuals (dates/places)
#### TODO: Check places of birth / death for individuals

#### TODO: See if we can detect private / anonymous items and ignore?

print('\npyGEDCCOMpare')
print('=============')
print('By Mark Tiffany based on PyPl\n')
print('Loading GEDCOMs...\n')

# Load the files and locate the root people
#LoadGEDCOMs('myfiles/ancestry.ged','myfiles/familysearch-gen4.ged','surname=Tiffany:name=Mark:gender=M:birth_year=1975')
LoadGEDCOMs('myfiles/ancestry.ged','myfiles/wikitree.ged','surname=Tiffany:name=Rebecca:gender=F:birth_year=2003')
#LoadGEDCOMs('myfiles/wikitree.ged','myfiles/ancestry.ged','surname=Tiffany:name=Rebecca:gender=F:birth_year=2003')
#LoadGEDCOMs('myfiles/ancestry.ged','myfiles/wikitree.ged','surname=Tiffany:name=Mark:gender=M:birth_year=1975')
#LoadGEDCOMs('myfiles/ancestry.ged','myfiles/wikitree.ged','surname=Lyon:name=Keith Frederick:gender=M:birth_year=1926')
#LoadGEDCOMs('myfiles/wikitree.ged','myfiles/ancestry.ged','surname=Tiffany:name=Leonard:gender=M')

if not isinstance(root_person_1, IndividualElement):
	print('Could not find individual in GEDCOM 1!')
	if not isinstance(root_person_2, IndividualElement):
		print('Could not find individual in GEDCOM 2!')
	exit()

print('Starting with: '+GetStandardisedName(root_person_1))

# Start iterating through parents and relations to check data matches
t=(root_person_1,root_person_2)
list_of_matches = [t]
list_of_matches_sep =[0]
list_of_checked = []
list_of_checked_sep =[]
perfect_matches = 0
non_matches = 0
max_sep=0
count_issues = 0

if DEBUGMODE>1: print('>>>LOOP-> Start')

while len(list_of_matches)>0:
	output = ''
	# take the first item out of the list and add it to the checked list
	t=list_of_matches[0]
	list_of_matches=list_of_matches[1:]
	(ind_1,ind_2)=t
	list_of_checked = [(ind_1,ind_2)] + list_of_checked

	# determine degree of separation for this individual, remove it from the matches list and add to the checked list
	this_sep = list_of_matches_sep[0]
	list_of_matches_sep = list_of_matches_sep[1:]
	list_of_checked_sep = [this_sep] + list_of_checked_sep

	if this_sep>max_sep: max_sep=this_sep

	# Pop the names on the doors
	ident_1=GetStandardisedName(ind_1)
	ident_2=GetStandardisedName(ind_2)
	output+=ident_1+' : Degree of Separation='+str(this_sep)+'\n'
	
	# compare these individuals
	conf=CompareIndividuals(ind_1,ind_2)

	# provided we have some confidence in a match, check out the family members
	if conf<0.2:
		if DEBUGMODE>1: print('>>>Checking Family-> Insufficient confidence in match, skipping')
		non_matches+=1
	else:

		if SCOPE_ALL:
			# Add Spouse
			if DEBUGMODE>1: print('>>>Checking Spouse   -> Looking...')
			marriages=0
			fam_1=gedcom_parser_1.get_families(ind_1)
			fam_2=gedcom_parser_2.get_families(ind_2)
			for fam in fam_1:
				members_1=gedcom_parser_1.get_family_members(fam,"PARENTS")
				for t in members_1:
					if t.is_identical(ind_1)==False: 
						if DEBUGMODE>2: print('>>>Checking Spouse   -> GEDCOM1 Spouse found: '+str(t.get_name()))
						marriages += 1
						tmp_1 = t
						
						if DEBUGMODE>3: print('>>>Checking Spouse   -> Comparing to GEDCOM2...')
						found=0
						
						for fam_check in fam_2:
							members_2=gedcom_parser_2.get_family_members(fam_check,"PARENTS")
							for t2 in members_2:
								if t2.is_identical(ind_2)==False: 
									if DEBUGMODE>3: print('>>>Checking Spouse   -> GEDCOM2 Simple Compare: '+str(tmp_1.get_name())+' vs '+str(t2.get_name()))
									
									if SimpleCompare(tmp_1,t2):
										found=1
										tmp_2 = t2
									
										if DEBUGMODE>2: print('>>>Checking Spouse   -> GEDCOM2 Match found: '+str(tmp_2.get_name()))
						
										if AddToList(tmp_1,tmp_2, this_sep+1):
											if DEBUGMODE>0: print('>>>Checking Spouse   -> Added : '+str(tmp_1.get_name())+' and '+str(tmp_2.get_name()))
										else:
											if DEBUGMODE>0: print('>>>Checking Spouse   -> Dupe  : '+str(tmp_1.get_name())+' and '+str(tmp_2.get_name()))
						
						if found==0:
							output+=' - CANNOT MATCH SPOUSE : '+GetStandardisedName(tmp_1)+'\n'
			
			marriages_1=gedcom_parser_1.get_marriages(ind_1)
			marriages_2=gedcom_parser_2.get_marriages(ind_2)
			if len(marriages_1)!=marriages or len(marriages_2)!=marriages:
				output+=' - SPOUSES AND MARRIAGE MIS-MATCH : '+str(marriages)+' Spouse records vs '+str(len(marriages_1))+' / '+str(len(marriages_2))+' Marriage records'+'\n'
			
			if marriages==0:
				output+=' = No Spouses'+'\n'
			else:
				for m_1 in marriages_1:
					(d_1,p_1)=m_1
					for m_2 in marriages_2:
						(d_2,p_2)=m_2
						### TODO: check marriages for individuals

		# Add Parents
		if DEBUGMODE>1: print('>>>Checking Parents  -> Looking...')
		list_1=gedcom_parser_1.get_parents(ind_1)
		list_2=gedcom_parser_2.get_parents(ind_2)
		parents=0
		for tmp_1 in list_1:
			found=0
			parents+=1
			for tmp_2 in list_2:
				if DEBUGMODE>2: print('>>>Checking Parents  -> Simple Compare : '+str(tmp_1.get_name())+' and '+str(tmp_2.get_name())) 
				if SimpleCompare(tmp_1,tmp_2):
					found=1
					if AddToList(tmp_1,tmp_2, this_sep+1):
						if DEBUGMODE>0: print('>>>Checking Parents  -> Added : '+str(tmp_1.get_name())+' and '+str(tmp_2.get_name()))
					else:
						if DEBUGMODE>0: print('>>>Checking Parents  -> Dupe  :  '+str(tmp_1.get_name())+' and '+str(tmp_2.get_name()))
			if found==0:
				output+=' - CANNOT MATCH PARENT : '+GetStandardisedName(tmp_1)+'\n'
		
		if parents==0: 
			output+=' = No Parents\n'
		elif parents==1:
			output+=' = Missing 1 Parent\n'
		
	if conf>=0.5:

		if SCOPE_ALL:
			if DEBUGMODE>1: print('>>>Checking Children -> Looking...')

			count_kids=0
			list_1=gedcom_parser_1.get_families(ind_1)
			list_2=gedcom_parser_2.get_families(ind_2)
			for fam_1 in list_1:
				members_1=gedcom_parser_1.get_family_members(fam_1,"CHIL")
				for tmp_1 in members_1:
					if tmp_1.is_child():
						count_kids+=1
						if DEBUGMODE>2: print('>>>Checking Children -> '+str(tmp_1.get_name()))
						found=0
						
						for fam_2 in list_2:
							members_2=gedcom_parser_2.get_family_members(fam_2,"CHIL")
							for tmp_2 in members_2:
								if DEBUGMODE>2: print('>>>Checking Children -> Simple Compare : '+str(tmp_2.get_name()))
								if SimpleCompare(tmp_1,tmp_2):
									found=1
									if AddToList(tmp_1,tmp_2, this_sep+1):
										if DEBUGMODE>0: print('>>>Checking Children -> Added : '+str(tmp_1.get_name())+' and '+str(tmp_2.get_name()))
									else:
										if DEBUGMODE>1: print('>>>Checking Children -> Dupe  : '+str(tmp_1.get_name())+' and '+str(tmp_2.get_name()))
						if found==0:
							output+=' - CHILD NOT FOUND : '+GetStandardisedName(tmp_1)+'\n'
			if count_kids==0: output+=' = No Children\n'
	
	f=output.find(' - ')
	if f!=-1: count_issues+=1
	if OUTPUT_ALL or f!=-1:
		print(output)

# Finish up by summarising what we have done
print('\nAll tree checks completed. Thank you!')
print('  -- Individuals checked: '+str(len(list_of_checked)))
print('      -- Perfect Matches: '+str(perfect_matches))
print('      -- Partial Matches: '+str(len(list_of_checked)-perfect_matches-non_matches))
print('      -- Non Matches:     '+str(non_matches))
print('      -- Max Separation:  '+str(max_sep))
print('      -- With Issues:     '+str(count_issues))
print('')
