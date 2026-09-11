class ErklaerBaerError(Exception):
    """Base error shown to CLI users without a traceback."""


class ConfigurationError(ErklaerBaerError):
    """The local or deployment configuration is incomplete or unsafe."""


class SourceError(ErklaerBaerError):
    """MINT source data is unavailable or invalid."""


class BudgetExceeded(ErklaerBaerError):
    """A local usage guard would be crossed."""


class ExternalServiceError(ErklaerBaerError):
    """An external API call failed or returned unusable data."""
