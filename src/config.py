from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    groq_api_key: str
    groq_model_fast: str = "llama-3.1-8b-instant"
    groq_model_reasoning: str = "llama-3.3-70b-versatile"

    qdrant_url: str = "http://localhost:6333"
    qdrant_collection: str = "documents"

    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "password"

    tavily_api_key: str = ""

    langfuse_public_key: str = ""
    langfuse_secret_key: str = ""
    langfuse_host: str = "https://cloud.langfuse.com"

    max_cost_usd: float = 0.05
    max_latency_ms: int = 15000
    max_rewrites: int = 2
    max_verify_loops: int = 1


settings = Settings()