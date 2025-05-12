# AI Engineer - Take Home

## Getting Started

Before running the project locally, create a `.env` file in the root directory with `OPENAI_API_KEY` set.

Then, run `docker compose up` in your terminal, and you should be good to go!

## Testing

Head to `http://localhost:8000/docs` to view the project's documentation. The docs show which functionality has been implemented and allows you to directly interact with the app's endpoints without needing to write a program to do so.

Before testing the project, seed the database by calling the `POST /seed` method. This will place six SOAP notes into the SQL and vector databases.

## Methodology

Throughout this project, I aimed to write maintainable, production quality code with no corners cut, using the latest industry techniques (OpenAI's Structured Output API, xml tags in prompts, FastAPI dependency injection, uv dependency management, etc.). My goal was to demonstrate the type of work I would be comfortable shipping and iterating over. Minimizing complexity and avoiding over-engineering while delivering software that can be easily extended is a delicate balance, and I believe I have achieved the right amount of abstraction to allow easy reasoning through the business logic.

Due to time constraints, I was not able to complete parts 4 and 5 of the exercise, but I am confident that there is enough depth in my implementations to facilitate a thorough and accurate evaluation of my abilities.

## Tech Stack

FastAPI - Main Application
PostgreSQL - Relational Database
Qdrant - Vector Database
Redis - Caching

~shaiyon
