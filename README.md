# ai-intelligence-hub
AI-Powered Content Summarizer &amp; Intelligence Hub

Current work in progress, very new. Please see the design I put together for it though. 

### Design
![ai-intelligence-hub design](readme_images/ai-intelligence-hub-design.png)


### Docker
```
docker-compose down -v
docker-compose up -d
```

### Postgres
Connect to the DB
```
psql -U user -d intelligence_db
```

See list of tables
```
\dt
```

View table structure
```
\d "AnalysisJob"
```

See data from table
```
SELECT * FROM "AnalysisJob"
```
