import structlog, logging, os

ENV_MODE = os.getenv("ENV_MODE", "LOCAL")

# Compatibilidade com Python 3.10 - getLevelNamesMapping() só existe no 3.11+
def get_logging_level():
    level_name = os.getenv("LOGGING_LEVEL", "DEBUG").upper()
    level_mapping = {
        'DEBUG': logging.DEBUG,
        'INFO': logging.INFO,
        'WARNING': logging.WARNING,
        'ERROR': logging.ERROR,
        'CRITICAL': logging.CRITICAL
    }
    return level_mapping.get(level_name, logging.DEBUG)

LOGGING_LEVEL = get_logging_level()

renderer = [structlog.processors.JSONRenderer()]
# if ENV_MODE.lower() == "local".lower() or ENV_MODE.lower() == "staging".lower():
#     renderer = [structlog.dev.ConsoleRenderer()]

structlog.configure(
    processors=[
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.dict_tracebacks,
        structlog.processors.CallsiteParameterAdder(
            {
                structlog.processors.CallsiteParameter.FILENAME,
                structlog.processors.CallsiteParameter.FUNC_NAME,
                structlog.processors.CallsiteParameter.LINENO,
            }
        ),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.contextvars.merge_contextvars,
        *renderer,
    ],
    cache_logger_on_first_use=True,
    wrapper_class=structlog.make_filtering_bound_logger(LOGGING_LEVEL),
)

logger: structlog.stdlib.BoundLogger = structlog.get_logger()
