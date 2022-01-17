
# Purpose of this database:

This project builds a database in Postgres to understand what songs are being listened to. The project collects data out of JSON files. The data was collected in our new music streaming app and contains information on songs and user activity.  
This project creates a database schema and ETL pipeline to enable the above mentioned analysis. 

***

# Project intruction manual:

Import information to work with the files in this project.

## Files in this project.

This project consists of the following files and folders. 

- Folder "data", this folder contains all the log_data of the app and the song_data available in the new app. 
- create_tables.py, python file to create tables.
- etl.ipynb, python file to test the etl job.
- etl.py, python to load the tables with an ETL job.
- README.MD, document file containing information about the files and project.
- sql_queries.py, file containing the SQL statement used in this project.
- test.ipynb, file to test if the tables were created succesfull with the correct data. 

## How to run the files in this project.

To run the project first fun "create_tables.py" to create the tables in the data warehouse. Next, run the ETL job with "etl.py". You can check if you where succesfull by running test.ipynb.

***

# Database schema

The project creates the following database schema:

**Fact Table**
- songplays - records in log data associated with song plays i.e. records with page NextSong <br>
        songplay_id, start_time, user_id, level, song_id, artist_id, session_id, location, user_agent

**Dimension Tables**

- users - users in the app
        user_id, first_name, last_name, gender, level
- songs - songs in music database
        song_id, title, artist_id, year, duration
- artists - artists in music database
        artist_id, name, location, latitude, longitude
- time - timestamps of records in songplays broken down into specific units
        start_time, hour, day, week, month, year, weekday

Schema for Song Play Analysis is a start schema, so we can easily analyse and execute queries on song play for our analysis on what songs are being listened to. 

***



