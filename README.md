# ai-intelligence-hub
AI-Powered Content Summarizer &amp; Intelligence Hub

Current work in progress, very new. Please see the design I put together for it though. 

### Design
![ai-intelligence-hub design](readme_images/ai-intelligence-hub-design.png)

### Running Current Backend
```
cd api
npm install
npm run dev
curl -X POST http://localhost:3000/analyze -H "Content-Type: application/json" -d '{"url": "website url"}'
```

This should spin up the endpoint and allow you to hit it from your local machine.

### Running Current Frontend
```
cd client-react
npm install
npm run dev
http://localhost:5173
```
This should allow you to navigate in your browser to the frontend.

### Docker
```
docker-compose down -v
docker-compose up -d
```

### Redis Debugging
```
docker-compose exec redis redis-cli
```

### Postgres Debugging
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
