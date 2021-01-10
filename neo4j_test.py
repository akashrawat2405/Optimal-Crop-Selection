from neo4j import GraphDatabase
from flask import Flask, redirect, url_for, request
from flask import render_template

app = Flask(__name__)
driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "password"), encrypted=False)


# for creating neo4j database
def create_database():
    with driver.session() as session:
        query1 = """LOAD CSV WITH HEADERS FROM 'file:///WaterRequirement.csv' AS row
        MERGE (:Crop{name:row.Crop});"""
        query2 = """LOAD CSV WITH HEADERS FROM 'file:///WaterRequirement.csv' AS row
        MERGE (c:Crop{name:row.Crop})
        MERGE (w:Water{name:"Water"})
        MERGE (c)-[:requires{min:toInteger(row.WaterRequirementMin),max:toInteger(row.WaterRequirementMax)}]->(w);"""
        query3 = """LOAD CSV WITH HEADERS FROM 'file:///SoilRequirement.csv' AS row
        MERGE (:Crop{name:row.Crop});"""
        query4 = """LOAD CSV WITH HEADERS FROM 'file:///SoilRequirement.csv' AS row
        MERGE (c:Crop{name:row.Crop})
        MERGE (s:Soiltype{name:row.SoilRequirement})
        MERGE (c)-[:grows_in]->(s);"""
        query5 = """LOAD CSV WITH HEADERS FROM 'file:///RainfallRequirement.csv' AS row
        MERGE (:Crop{name:row.Crop});"""
        query6 = """LOAD CSV WITH HEADERS FROM 'file:///RainfallRequirement.csv' AS row
        MERGE (c:Crop{name:row.Crop})
        MERGE (r:Rainfall{name:"Rainfall"})
        MERGE (c)-[:requires{min:toInteger(row.RainfallRequirementMin),max:toInteger(row.RainfallRequirementMax)}]->(r);"""
        query7 = """LOAD CSV WITH HEADERS FROM 'file:///TemperatureRequirement.csv' AS row
        MERGE (:Crop{name:row.Crop});"""
        query8 = """LOAD CSV WITH HEADERS FROM 'file:///TemperatureRequirement.csv' AS row
        MERGE (c:Crop{name:row.Crop})
        MERGE (t:Temperature{name:"Temperature"})
        MERGE (c)-[:requires{min:toInteger(row.TemperatureRequirementMin),max:toInteger(row.TemperatureRequirementMax)}]->(t);"""

        tx = session.begin_transaction()
        tx.run(query1)
        tx.run(query2)
        tx.run(query3)
        tx.run(query4)
        tx.run(query5)
        tx.run(query6)
        tx.run(query7)
        tx.run(query8)
        tx.commit()


# returns a list satisfying given parameters
def get_optimal_crop(soiltype, temperature, water, rainfall):
    driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "password"), encrypted=False)
    with driver.session() as session:
        query1 = "MATCH (c:Crop)-[]->(s:Soiltype) WHERE s.name=$soiltype RETURN c.name as value1"
        query2 = "MATCH (c:Crop)-[r]->(t:Temperature) WHERE r.min<=$temperature AND r.max>=$temperature RETURN c.name as value2"
        query3 = "MATCH (c:Crop)-[r]->(t:Water) WHERE r.min<=$water AND r.max>=$water RETURN c.name as value3"
        query4 = "MATCH (c:Crop)-[r]->(t:Rainfall) WHERE r.min<=$rainfall AND r.max>=$rainfall RETURN c.name as value4"
        tx = session.begin_transaction()
        result1 = tx.run(query1, soiltype=soiltype)
        result2 = tx.run(query2, temperature=temperature)
        result3 = tx.run(query3, water=water)
        result4 = tx.run(query4, rainfall=rainfall)
        tx.commit()
        list1 = []
        list2 = []
        list3 = []
        list4 = []
        result = []
        for record in result1:
            list1.append(record["value1"])
        for record in result2:
            list2.append(record["value2"])
        for record in result3:
            list3.append(record["value3"])
        for record in result4:
            list4.append(record["value4"])
        result = list(set(list1) & set(list2) & set(list3) & set(list4))
        driver.close()
        return result


# print(get_optimal_crop("black soil", 20, 1000, 120))
#create_database()


# returns details of about a specific crop
def get_details_of_crop(crop_name):
    with driver.session() as session:
        query1 = "MATCH (c:Crop)-[r]->(s:Soiltype) WHERE c.name=$crop_name RETURN s.name as value1"
        query2 = "MATCH (c:Crop)-[r]->(t:Temperature) WHERE c.name=$crop_name RETURN r.min as min2,r.max as max2"
        query3 = "MATCH (c:Crop)-[r]->(t:Water) WHERE c.name=$crop_name RETURN r.min as min3,r.max as max3"
        query4 = "MATCH (c:Crop)-[r]->(t:Rainfall) WHERE c.name=$crop_name RETURN r.min as min4,r.max as max4"
        tx = session.begin_transaction()
        result1 = tx.run(query1, crop_name=crop_name)
        result2 = tx.run(query2, crop_name=crop_name)
        result3 = tx.run(query3, crop_name=crop_name)
        result4 = tx.run(query4, crop_name=crop_name)
        tx.commit()
        list1 = []
        list2 = []
        list3 = []
        list4 = []
        for record in result1:
            list1.append(record["value1"])
        for record in result2:
            list2.append(record["min2"])
            list2.append(record["max2"])
        for record in result3:
            list3.append(record["min3"])
            list3.append(record["max3"])
        for record in result4:
            list4.append(record["min4"])
            list4.append(record["max4"])

        result = [list1, list2, list3, list4]
        return result


@app.route('/')
def formpage():
	return render_template('range.html')



@app.route('/exact')
def formpag():
	return render_template('exact.html')



@app.route('/process', methods=['GET', 'POST'] )
def process():
    if request.method == 'POST':
        soil = request.form['soil']
        water = request.form['water']
        temperature  = request.form['temp']
        rain = request.form['rain'] 
        print(soil,water,rain,temperature)
        x = get_optimal_crop(str(soil),int(temperature), int(water), int(rain))
        print(x)
        #print(get_optimal_crop("black soil", 20, 1000, 120))
        
    if len(x) == 0: 
        return render_template('result.html',header='No Matching Crops found', sub_header='(Based on key parameters you provided)', list_header="Try Other Combinations instead",
                       crops=x, title="Result")
    else: 
        return render_template('result.html',header='Results', sub_header='(Based on key parameters you provided)', list_header="Crop Names",
                       crops=x, title="Result")
    

@app.route('/openform')
def renders():
    return render_template('tenp.html')


@app.route('/process2',methods=['GET', 'POST'])
def processs():
    if request.method == 'POST':
        crop = request.form['crop']
        y = get_details_of_crop(str(crop))
       # print(y)

        if len(y[0]) == 0: 
            soil = "-"
        else:
            soil = y[0]
            
        if len(y[1]) == 0: 
            temp = "-"
        else:
            temp = y[1]
        
        if len(y[2]) == 0: 
            water = "-"
        else:
            water = y[2]

        if len(y[3]) == 0: 
            rainfall = "-"
        else:
            rainfall = y[3]

        
        
    
    if (len(y[0]) == 0 & len(y[1]) == 0 & len(y[2]) == 0 & len(y[3]) == 0): 
        return render_template('result2.html', sub_header='(Based on key parameters you provided)', list_header="Details not found for this entry",
                       crop_name= str(crop), title="Result",soils=soil,temps=temp,waters=water,rainfalls=rainfall)
    else: 
        return render_template('result2.html', sub_header='(Based on key parameters you provided)', list_header="Details",
                       crop_name= str(crop), title="Result",soils=soil,temps=temp,waters=water,rainfalls=rainfall)

    





if __name__ == '__main__':
   app.run(debug = True)
