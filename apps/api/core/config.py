from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "HireSense AI API"
    # Postgres Database URL (Defaulting to localhost for development)
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/hiresense"
    
    # External APIs
    GROQ_API_KEY: str = "GROQ_API_KEY"
    TINYFISH_API_KEY: str = "TINYFISH API KEY"
    
    # Google Auth
    GOOGLE_CLIENT_ID: str = "GOOGLE_API_KEY"

    class Config:
        env_file = ".env"

settings = Settings()
 