class ProviderError(Exception):
    pass

class ProviderAuthError(ProviderError):
    pass

class ProviderModelError(ProviderError):
    pass
