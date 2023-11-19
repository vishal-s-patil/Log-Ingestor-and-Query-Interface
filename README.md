## Log-Ingestor-and-Query-Interface

### Setup and Installation

1. **Create an AWS SQS:** Follow the instructions provided by AWS to create an SQS queue for handling log messages.

2. **Replace Environment Variables:** Replace all placeholder environment variables in the project's configuration file(docker-compose.yaml file) with your actual credentials and settings.

3. **Run Docker Compose:** Execute the command `docker-compose up` to bring up the required Docker containers for the log ingestor and query interface.

4. **Database Migration:** Run the command `docker exec -it <project/app docker container id> python manage.py migrate` to apply database migrations for the application.

### Log Ingestion and Querying

1. **Create Elasticsearch Index:** Make a PUT request to `http://localhost:3000/logs/` to create an index in Elasticsearch for storing log data.

2. **Start SQS Consumer Server:** Hit the URL `http://127.0.0.1:3000/ing/sqs_consumer/` to start the SQS consumer server, which will continuously consume log messages from the SQS queue and index them in Elasticsearch.

3. **Ingest Log Entries:** Send a POST request to `http://127.0.0.1:3000/ing/logentries/` with log entries in JSON format to ingest them into the system.

4. **Search Logs:** Access the URL `http://localhost:3000/ing/search_logs/` to perform various search queries on the indexed log data.

   - **Filter by Fields:** Specify fields like `level`, `Trace ID`, etc., to filter logs based on specific criteria.

   - **Search by Message:** Add a `message` field to search for logs containing a particular term, such as "Failed to connect".

   - **Range Queries:** Include `start_time` and `end_time` fields to perform range queries and retrieve logs within a specified time frame.

### Visualization Approaches

approach 1: \
![Image Alt Text](https://github.com/vishal-s-patil/Log-Ingestor-and-Query-Interface/blob/main/process1.png?raw=true) 
approach 2: \
![Image Alt Text](https://github.com/vishal-s-patil/Log-Ingestor-and-Query-Interface/blob/main/process2.png?raw=true) 
approach 3(implemented): \
![Image Alt Text](https://github.com/vishal-s-patil/Log-Ingestor-and-Query-Interface/blob/main/process3.png?raw=true) 