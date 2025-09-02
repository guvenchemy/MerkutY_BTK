# Deprecated duplicate model file retained for compatibility.
# The authoritative definitions live in `app.models.user_vocabulary`.
# Keeping this file minimal prevents conflicting SQLAlchemy Base metadata.

# Compatibility shim: re-export from canonical module to avoid ImportError
from app.models.user_vocabulary import UserGrammarKnowledge  # noqa: F401

# Intentionally left without ORM models. Use:
# from app.models.user_vocabulary import UserGrammarKnowledge 