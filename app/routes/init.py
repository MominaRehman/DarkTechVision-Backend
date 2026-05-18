from .training import router as training_router
from .onion_scraper import router as onion_router
from .prediction import router as prediction_router

__all__ = ['training_router', 'onion_router', 'prediction_router']