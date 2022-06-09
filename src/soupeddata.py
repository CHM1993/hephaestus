from bs4 import BeautifulSoup
import requests
import json
import pandas as pd
import re

html_markup = open("Arrays.html",'r')
soup = BeautifulSoup(html_markup, "html.parser")
#print(soup.prettify())
file_object = open('Arrays_prettify.html','w')
file_object.write(soup.prettify().encode('utf8'))

#print soup.findAll('main')[0]

#soup.findAll('main')[0].tbody.findAll('tr')
#for row in soup.findAll('table')[0].tbody.findAll('tr'):
#	first_column = row.findAll('th')[0].contents
#	third_column = row.findAll('td')[0].contents
#	print first_column, third_column


## Convert to json
#pd.DataFrame(data, columns=colnames).to_json()


#print(soup.title)
#print(soup.find_all(class_='title'))
#print(soup.find_all(class_='colFirst'))

data = [] # create a list to store the items
#for aaa in soup.find_all(class_='main'):
#	item={}
#	for bbb in soup.find_all(class_='title'):
#		item['name']=bbb.text
#	for ccc in soup.find_all(class_='inheritance'):
#		item['inheritance']=ccc.text
#	data.append(item) # add the item to the list

#with open("myjson.json", "w") as writeJSON:
#    json.dump(data, writeJSON, ensure_ascii=False)

#item={}
#clas = soup.find_all(class_='title')
#c_name= clas.findAll(text=True)
#print(c_name)
#item['class_name']=c_name

#inh = soup.find_all(class_='inheritance')
api = {
  'methods': [],
  'type_parameters': [],
  'implements': [],
  'inherits': [],
  'fields': [],
}
for pack in (soup.find_all(class_='subTitle')):
	pack1=pack.findAll(text=True)
	print(pack1[2])

for cl1 in (soup.find_all(class_='description')):
	cl2 = cl1.find(class_='blockList')
	cl3 = cl2.find("pre")
	cl4 = cl3.findAll(text=True)
	print(cl4)
	api['api_name'] = pack1[2]+'.'+cl4[1]
	api['extends'] = cl4[2].replace("\n","")

for aaa in (soup.find_all(class_='altColor')):
	item={}
	bbb = aaa.find(class_='colFirst')
	access_mod=bbb.findAll(text=True)
	print(access_mod)
	item['method_return_type']=access_mod
	ccc = aaa.find(class_='colSecond')
#	ddd = ccc.find(class_='memberNameLink')
	m_name=ccc.findAll(text=True)
#	print(m_name)
	item['method_Name']=m_name
	#akoma exei thema den pianei ta []
	par_types = re.findall("byte|List|List <T>|int|int[]|T|T[]|char|char[]|double|double[]|float|float[]|boolean|boolean[]|long|long[]|short|short[]|<? super T>|U|U[]|java.lang.Object[]",m_name[1])
	if len(access_mod) - access_mod.count(0) >= 2: #exoyme type parameters
		api['methods'].append({
			 'name': m_name[0],
			 'parameters_types': par_types,
			 'return_type': ' '.join(access_mod[1:]),
			 'is_static': 'static' in access_mod[0],
			 'access_mod': 'public',
			 'type_parameters': access_mod[0].partition("static")[2]
		})
	else:
		api['methods'].append({
			 'name': m_name[0],
			 'parameters_types': par_types,
			 'return_type': access_mod[0].partition("static")[2],
			 'is_static': 'static' in access_mod[0],
			 'access_mod': 'public',
			 'type_parameters': [y for y in access_mod[1:]]
		})


for aaa in (soup.find_all(class_='rowColor')):
	item={}
	bbb = aaa.find(class_='colFirst')
	access_mod=bbb.findAll(text=True)
	print(access_mod)
	item['method_return_type']=access_mod
	ccc = aaa.find(class_='colSecond')
#	ddd = ccc.find(class_='memberNameLink')
	m_name=ccc.findAll(text=True)
#	print(m_name)
	item['method_Name']=m_name
	#akoma exei thema den pianei ta []
	par_types = re.findall("T|T\"[]\"|byte|List|List <T>|int|int[]|char|char[]|double|double[]|float|float[]|boolean|boolean[]|long|long[]|short|short[]|<? super T>|U|U[]|java.lang.Object[]",m_name[1])
	if len(access_mod) - access_mod.count(0) >= 2: #exoyme type parameters
		api['methods'].append({
			 'name': m_name[0],
			 'parameters_types': par_types,
			 'return_type': ' '.join(access_mod[1:]),
			 'is_static': 'static' in access_mod[0],
			 'access_mod': 'public',
			 'type_parameters': access_mod[0].partition("static")[2]
		})
	else:
		api['methods'].append({
			 'name': m_name[0],
			 'parameters_types': par_types,
			 'return_type': access_mod[0].partition("static")[2],
			 'is_static': 'static' in access_mod[0],
			 'access_mod': 'public',
			 'type_parameters': [y for y in access_mod[1:]]
		})
#	data.append(api) # add the item to the list
	
#for aaa in (soup.find_all(class_='rowColor')):
#	item={}
#	bbb = aaa.find(class_='colFirst')
#	access_mod=bbb.findAll(text=True)
#	print(access_mod)
#	item['method_mod_type']=access_mod
#	ccc = aaa.find(class_='colSecond')
#	m_name=ccc.findAll(text=True)
#	print(m_name)
#	item['method_Name']=m_name
#	data.append(item) # add the item to the list


with open("myjson.json", "w") as writeJSON:
    json.dump(api, writeJSON, ensure_ascii=True,)
#print(soup.select('b'))

#classes = []
#for element in soup.find_all(class_=True):
#    classes.extend(element["class"])
#print(classes)

#methods=[]
#for element in soup.find_all('a'):
#	if element.has_key('href'):
#		methods.append(element['href'])
#print(methods)
#methods2=[]
#for x in methods:
#	if "#" in x:
#		methods2.append(x)
#print(methods2)

#list_of_divs = soup.find_all(class_="inheritance")
#print(len(list_of_divs))
#print(soup.p)

#tag = soup.b
#type(tag)

#for link in soup.find_all('ul'):
#    print(link.get('class'))

#print(soup.get_text())
