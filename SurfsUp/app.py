# Import the dependencies.
import numpy as np
import pandas as pd

import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func

from flask import Flask, jsonify


#################################################
# Database Setup
#################################################
engine = create_engine("sqlite:///../Resources/hawaii.sqlite")

# reflect an existing database into a new model
Base = automap_base()
# reflect the tables
Base.prepare(autoload_with = engine)

# Save references to each table
measurements = Base.classes.measurement
stations = Base.classes.station

#################################################
# Flask Setup
#################################################
app = Flask(__name__)

#################################################
# Flask Routes
#################################################
@app.route("/")
def home():
    """List all available api routes"""
    return(
        f"Welcome to the Hawaii Weather API!<br/>"
        f"Below are the available routes:<br/>"
        f"/api/v1.0/precipitation<br/>"
        f"api/v1.0/stations<br/>"
        f"api/v1.0/tobs<br/>"
        f"<br/>"
        f"If you'd like to choose specific dates, you can use to route formats below.<br/>"
        f"NOTE: The date format must be YYYY-MM-DD<br/>"
        f"/api/v1.0/start-date<br/>"
        f"/api/v1.0/start-date/end-date"
    )

@app.route("/api/v1.0/precipitation")
def precipitation():
    session = Session(engine)

    recent_date = session.query(measurements).order_by(measurements.date.desc()).first()
    one_year_before = str(pd.to_datetime(recent_date.date) + pd.DateOffset(years = -1))[:10]

    data = session.query(measurements.date, measurements.prcp).\
        filter(measurements.date >= one_year_before).all()
    
    prcp_dict = {}
    for i in data:
        prcp_dict[i.date] = i.prcp
    
    session.close()
    
    return jsonify(prcp_dict)
    
@app.route("/api/v1.0/stations")
def station():
    session = Session(engine)

    data = session.query(stations.station).all()

    session.close()

    return jsonify(list(np.ravel(data)))

@app.route("/api/v1.0/tobs")
def temps():
    session = Session(engine)

    active_station = session.query(measurements.station, func.count(measurements.station)).\
        order_by(func.count(measurements.station).desc()).\
        group_by(measurements.station).all()[0][0]
    
    recent_date = session.query(measurements).order_by(measurements.date.desc()).first()
    one_year_before = str(pd.to_datetime(recent_date.date) + pd.DateOffset(years = -1))[:10]

    data = session.query(measurements.date, measurements.tobs).\
    filter(measurements.date >= one_year_before).\
        filter(measurements.station == active_station)

    temp_dict = {}
    for i in data:
        temp_dict[i.date] = i.tobs
    
    session.close()
    
    return(jsonify(temp_dict))

@app.route("/api/v1.0/<start>")
def start_date(start):
    session = Session(engine)
    dates = list(np.ravel(session.query(measurements.date).all()))
    
    if start in dates:
        data = session.query(func.min(measurements.tobs),
                             func.avg(measurements.tobs),
                             func.max(measurements.tobs)
                             ).\
            filter(measurements.date >= start).first()
        
        meta = list(np.ravel(data))

        return jsonify({"Date": start,
                        "Minimum Temp": meta[0],
                        "Average Temp": meta[1],
                        "Max Temp": meta[2]})
    
    session.close()

    return jsonify({"error": f"Start date {start} not found."}), 404

@app.route("/api/v1.0/<start>/<end>")
def start_end_date(start, end):
    session = Session(engine)

    dates = list(np.ravel(session.query(measurements.date).all()))
    
    if start in dates and end in dates:
        data = session.query(func.min(measurements.tobs),
                             func.avg(measurements.tobs),
                             func.max(measurements.tobs)
                             ).\
            filter(measurements.date >= start).\
                filter(measurements.date <= end).first()
        
        meta = list(np.ravel(data))
        
        return jsonify({"Start Date": start,
                        "End Date": end,
                        "Minimum Temp": meta[0],
                        "Average Temp": meta[1],
                        "Max Temp": meta[2]})
    
    session.close()

    return jsonify({"error": f"Start date {start} not found."}), 404

if __name__ == 'main':
    app.run(debug = True)