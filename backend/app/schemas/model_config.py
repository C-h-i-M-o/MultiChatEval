from pydantic import BaseModel, Field


class AvailableModelRead(BaseModel):
    id: int
    provider_name: str = Field(alias="providerName")
    display_name: str = Field(alias="displayName")
    model_name: str = Field(alias="modelName")


class ModelConfigRead(BaseModel):
    id: int
    provider_name: str = Field(alias="providerName")
    display_name: str = Field(alias="displayName")
    model_name: str = Field(alias="modelName")
    base_url: str = Field(alias="baseUrl")
    enabled: bool
    builtin: bool
    has_api_key: bool = Field(alias="hasApiKey")
    masked_api_key: str = Field(alias="maskedApiKey")
    max_tokens: int = Field(alias="maxTokens")
    price_input: float = Field(alias="priceInput")
    price_output: float = Field(alias="priceOutput")


class ModelConfigCreate(BaseModel):
    provider_name: str = Field(alias="providerName")
    display_name: str = Field(alias="displayName")
    model_name: str = Field(alias="modelName")
    base_url: str = Field(alias="baseUrl")
    api_key: str | None = Field(default=None, alias="apiKey")
    enabled: bool = True
    max_tokens: int = Field(default=1024, alias="maxTokens", ge=1)
    price_input: float = Field(default=0, alias="priceInput", ge=0)
    price_output: float = Field(default=0, alias="priceOutput", ge=0)


class ModelConfigUpdate(BaseModel):
    provider_name: str | None = Field(default=None, alias="providerName")
    display_name: str | None = Field(default=None, alias="displayName")
    model_name: str | None = Field(default=None, alias="modelName")
    base_url: str | None = Field(default=None, alias="baseUrl")
    api_key: str | None = Field(default=None, alias="apiKey")
    enabled: bool | None = None
    max_tokens: int | None = Field(default=None, alias="maxTokens", ge=1)
    price_input: float | None = Field(default=None, alias="priceInput", ge=0)
    price_output: float | None = Field(default=None, alias="priceOutput", ge=0)


class ModelConfigTestRequest(BaseModel):
    model_config_id: int | None = Field(default=None, alias="modelConfigId")
    provider_name: str | None = Field(default=None, alias="providerName")
    model_name: str | None = Field(default=None, alias="modelName")
    base_url: str | None = Field(default=None, alias="baseUrl")
    api_key: str | None = Field(default=None, alias="apiKey")
    max_tokens: int = Field(default=128, alias="maxTokens", ge=1)


class ModelConfigTestResult(BaseModel):
    success: bool
    message: str
    latency_ms: int = Field(default=0, alias="latencyMs")
