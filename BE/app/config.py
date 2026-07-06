from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    clova_ocr_invoke_url: str
    clova_ocr_secret_key: str

    clova_studio_api_key: str
    clova_studio_api_base_url: str = "https://clovastudio.stream.ntruss.com/v1/openai"
    clova_studio_chat_model: str = "HCX-005"
    clova_studio_embedding_model: str = "clir-emb-dolphin"

    rag_index_path: str = "./data/food_index.pkl"
    cors_origins: str = "http://localhost:5173"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
