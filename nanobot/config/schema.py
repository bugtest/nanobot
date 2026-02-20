"""Configuration schema using Pydantic."""

from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from pydantic_settings import BaseSettings


class Base(BaseModel):
    """Base model."""

    model_config = ConfigDict(populate_by_name=True)


class AgentDefaults(Base):
    """Default agent configuration."""

    workspace: str = "~/.nanobot/workspace"
    model: str = "openrouter/anthropic/claude-3-5-sonnet"
    max_tokens: int = 8192
    temperature: float = 0.7
    max_tool_iterations: int = 20
    memory_window: int = 50


class AgentsConfig(Base):
    """Agent configuration."""

    defaults: AgentDefaults = Field(default_factory=AgentDefaults)


class ProviderConfig(Base):
    """LLM provider configuration."""

    api_key: str = ""
    api_base: str | None = None


class ProvidersConfig(Base):
    """Configuration for LLM providers."""

    openrouter: ProviderConfig = Field(default_factory=ProviderConfig)
    ollama: ProviderConfig = Field(default_factory=ProviderConfig)


class WebSearchConfig(Base):
    """Web search tool configuration."""

    api_key: str = ""
    max_results: int = 5


class WebToolsConfig(Base):
    """Web tools configuration."""

    search: WebSearchConfig = Field(default_factory=WebSearchConfig)


class ExecToolConfig(Base):
    """Shell exec tool configuration."""

    timeout: int = 60


class ToolsConfig(Base):
    """Tools configuration."""

    web: WebToolsConfig = Field(default_factory=WebToolsConfig)
    exec: ExecToolConfig = Field(default_factory=ExecToolConfig)
    restrict_to_workspace: bool = False


class Config(BaseSettings):
    """Root configuration for nanobot."""

    agents: AgentsConfig = Field(default_factory=AgentsConfig)
    providers: ProvidersConfig = Field(default_factory=ProvidersConfig)
    tools: ToolsConfig = Field(default_factory=ToolsConfig)

    @property
    def workspace_path(self) -> Path:
        """Get expanded workspace path."""
        return Path(self.agents.defaults.workspace).expanduser()

    def get_api_key(self, provider: str | None = None) -> str | None:
        """Get API key for the specified provider."""
        if provider == "ollama":
            return self.providers.ollama.api_key
        return self.providers.openrouter.api_key

    def get_api_base(self, provider: str | None = None) -> str | None:
        """Get API base URL for the specified provider."""
        if provider == "ollama":
            p = self.providers.ollama
            return p.api_base if p.api_base else "http://localhost:11434"
        p = self.providers.openrouter
        if p.api_base:
            return p.api_base
        return "https://openrouter.ai/api/v1"

    model_config = ConfigDict(env_prefix="NANOBOT_", env_nested_delimiter="__")
